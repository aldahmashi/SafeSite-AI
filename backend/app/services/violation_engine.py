"""
ViolationEngine — stateless safety rule evaluator.

Given a list of YOLO detections for one frame it:
  1. Splits detections by class group (persons, helmets, vests …)
  2. Associates PPE boxes with the person box that contains them
     (center-in-bbox strategy, dataset-agnostic class name sets)
  3. Applies safety rules (NO_HELMET, NO_VEST)
  4. Gates each violation through the WorkerTracker cooldown
  5. Returns a list of ViolationEvent dataclasses — no DB objects

Design decisions:
  - The engine is *stateless*: all state lives in WorkerTracker.
  - class name sets cover common public PPE dataset naming conventions.
  - infer_from_absence=True also flags violations when the model knows
    about a PPE class but finds none associated with a worker. This is
    useful for datasets that only label the positive class (helmet).
    Default is False (safer: only flag explicit no-ppe detections).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.services.tracker import WorkerTracker

# ── class-name sets (covers common public PPE dataset conventions) ────────────
PERSON_CLASSES = frozenset({
    "person", "worker", "people",
})
HELMET_CLASSES = frozenset({
    "helmet", "hardhat", "hard_hat", "hard hat",
})
NO_HELMET_CLASSES = frozenset({
    "no_helmet", "no_hardhat", "no_hard_hat",
    "no helmet", "no hardhat", "without_helmet",
    "without helmet",
    # Roboflow hyphenated forms (also covered by detector.py normalizer)
    "no-hardhat", "no-helmet",
})
VEST_CLASSES = frozenset({
    "vest", "safety_vest", "safety-vest", "safety vest",
})
NO_VEST_CLASSES = frozenset({
    "no_vest", "no_safety_vest", "no safety vest",
    "without_vest", "without vest",
    # Roboflow forms
    "no-safety vest", "no-safety-vest",
})
MACHINERY_CLASSES = frozenset({
    "machinery", "machine", "vehicle",
    "excavator", "crane", "forklift",
})

# ── violation metadata ────────────────────────────────────────────────────────
VIOLATION_RISK: dict[str, str] = {
    "NO_HELMET":              "HIGH",
    "NO_VEST":                "MEDIUM",
    "HIGH_RISK_ZONE":         "CRITICAL",
    "MACHINERY_PROXIMITY_RISK": "HIGH",
}

VIOLATION_DESC: dict[str, str] = {
    "NO_HELMET":  "Worker detected without a safety helmet.",
    "NO_VEST":    "Worker detected without a high-visibility safety vest.",
    "HIGH_RISK_ZONE":
        "Worker entered a restricted zone without required PPE.",
    "MACHINERY_PROXIMITY_RISK":
        "Worker in close proximity to machinery without PPE.",
}


# ── result type ───────────────────────────────────────────────────────────────

@dataclass
class ViolationEvent:
    track_id: int             # YOLO/ByteTrack track ID (may be negative for untracked)
    db_worker_id: Optional[int]   # workers.id once persisted; None before first DB write
    worker_bbox: list[int]         # [x1, y1, x2, y2] of the person box
    violation_type: str            # "NO_HELMET" | "NO_VEST" | …
    risk_level: str                # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    confidence: float
    frame_number: int
    timestamp: float               # seconds from video start
    description: str


# ── engine ────────────────────────────────────────────────────────────────────

class ViolationEngine:
    """
    Evaluates one frame's detections and returns violations that survive
    the per-worker cooldown gate.

    Args:
        tracker:              Shared WorkerTracker for this session.
        infer_from_absence:   When True, also flag violations when a worker
                              has no helmet/vest associated AND the loaded
                              model includes those classes. When False (default),
                              only flag when an explicit no-ppe class is detected.
        min_person_area:      Ignore person boxes smaller than this area (px²).
                              Filters out tiny far-away persons where PPE
                              cannot be reliably assessed. Default 4000.
    """

    def __init__(
        self,
        tracker: WorkerTracker,
        infer_from_absence: bool = False,
        min_person_area: int = 4000,
    ) -> None:
        self.tracker = tracker
        self.infer_from_absence = infer_from_absence
        self.min_person_area = min_person_area

    # ── public API ────────────────────────────────────────────────────────────

    def process_frame(
        self,
        frame_number: int,
        timestamp: float,
        detections: list[dict],
    ) -> list[ViolationEvent]:
        """
        Evaluate all detections for a single frame.

        Returns only ViolationEvents that passed the cooldown gate —
        safe to persist to DB directly.
        """
        all_persons = _filter(detections, PERSON_CLASSES)
        persons = [p for p in all_persons if _area(p["bbox_xyxy"]) >= self.min_person_area]
        helmets   = _filter(detections, HELMET_CLASSES)
        no_helmets = _filter(detections, NO_HELMET_CLASSES)
        vests     = _filter(detections, VEST_CLASSES)
        no_vests  = _filter(detections, NO_VEST_CLASSES)

        # Whether the dataset/model knows about each PPE class at all
        dataset_has_helmet = bool(helmets or no_helmets)
        dataset_has_vest   = bool(vests or no_vests)

        all_ppe = helmets + no_helmets + vests + no_vests
        assoc = _associate_ppe_with_persons(persons, all_ppe)

        events: list[ViolationEvent] = []

        for idx, person in enumerate(persons):
            track_id = person.get("track_id")
            # Untracked persons get a synthetic negative ID so cooldown
            # still works (shared across all untracked boxes in this frame)
            eff_id = track_id if track_id is not None else -(idx + 1)

            ws = self.tracker.get(eff_id)
            db_worker_id = ws.db_worker_id if ws else None

            associated  = assoc.get(idx, [])
            assoc_names = {d["class_name"].lower() for d in associated}

            # ── helmet rule ──────────────────────────────────────────────────
            trigger = self._check_helmet(
                person, associated, assoc_names, dataset_has_helmet
            )
            if trigger is not None:
                ev = self._gate(
                    eff_id, db_worker_id, person,
                    trigger, "NO_HELMET", frame_number, timestamp,
                )
                if ev:
                    events.append(ev)

            # ── vest rule ────────────────────────────────────────────────────
            trigger = self._check_vest(
                person, associated, assoc_names, dataset_has_vest
            )
            if trigger is not None:
                ev = self._gate(
                    eff_id, db_worker_id, person,
                    trigger, "NO_VEST", frame_number, timestamp,
                )
                if ev:
                    events.append(ev)

        return events

    # ── rule checks ───────────────────────────────────────────────────────────

    def _check_helmet(
        self,
        person: dict,
        associated: list[dict],
        assoc_names: set[str],
        dataset_has_helmet: bool,
    ) -> Optional[dict]:
        """
        Return the triggering detection if a NO_HELMET violation exists.
        Priority: explicit no_helmet label → inferred from absence.
        """
        # Explicit: a no_helmet/no_hardhat box overlaps this person
        for d in associated:
            if d["class_name"].lower() in NO_HELMET_CLASSES:
                return d

        # Inferred: model knows about helmets but none found on this person
        if self.infer_from_absence and dataset_has_helmet:
            if not any(n in HELMET_CLASSES for n in assoc_names):
                return person   # use the person box as the trigger reference

        return None

    def _check_vest(
        self,
        person: dict,
        associated: list[dict],
        assoc_names: set[str],
        dataset_has_vest: bool,
    ) -> Optional[dict]:
        for d in associated:
            if d["class_name"].lower() in NO_VEST_CLASSES:
                return d

        if self.infer_from_absence and dataset_has_vest:
            if not any(n in VEST_CLASSES for n in assoc_names):
                return person

        return None

    # ── cooldown gate ─────────────────────────────────────────────────────────

    def _gate(
        self,
        track_id: int,
        db_worker_id: Optional[int],
        person: dict,
        trigger: dict,
        violation_type: str,
        frame_number: int,
        timestamp: float,
    ) -> Optional[ViolationEvent]:
        """
        Pass through cooldown. Returns ViolationEvent or None if suppressed.
        """
        if not self.tracker.can_record(track_id, violation_type, timestamp):
            return None

        self.tracker.mark_recorded(track_id, violation_type, timestamp)

        return ViolationEvent(
            track_id=track_id,
            db_worker_id=db_worker_id,
            worker_bbox=list(person["bbox_xyxy"]),
            violation_type=violation_type,
            risk_level=VIOLATION_RISK.get(violation_type, "MEDIUM"),
            confidence=round(trigger["confidence"], 4),
            frame_number=frame_number,
            timestamp=timestamp,
            description=VIOLATION_DESC.get(
                violation_type, "Safety violation detected."
            ),
        )


# ── module-level helpers ───────────────────────────────────────────────────────

def _filter(detections: list[dict], class_set: frozenset[str]) -> list[dict]:
    return [d for d in detections if d["class_name"].lower() in class_set]


def _center(bbox: list[int]) -> tuple[int, int]:
    x1, y1, x2, y2 = bbox
    return (x1 + x2) // 2, (y1 + y2) // 2


def _area(bbox: list[int]) -> int:
    x1, y1, x2, y2 = bbox
    return max(0, x2 - x1) * max(0, y2 - y1)


def _associate_ppe_with_persons(
    persons: list[dict],
    ppe_boxes: list[dict],
) -> dict[int, list[dict]]:
    """
    For each PPE detection, find the person whose bounding box contains
    the PPE center point.

    The person box is expanded by 15% on each side before testing so that
    head-level detections (no_helmet) that sit near the top edge of the
    person box are still captured.

    When a PPE center falls inside multiple expanded person boxes, assign
    it to the person with the smallest original box area (nearest person).

    Returns {person_index: [matching_ppe_detections]}.
    """
    result: dict[int, list[dict]] = {i: [] for i in range(len(persons))}

    for ppe in ppe_boxes:
        cx, cy = _center(ppe["bbox_xyxy"])
        best_idx: Optional[int] = None
        best_area = float("inf")

        for i, person in enumerate(persons):
            px1, py1, px2, py2 = person["bbox_xyxy"]
            pw, ph = px2 - px1, py2 - py1
            pad_x, pad_y = int(pw * 0.15), int(ph * 0.15)
            if (px1 - pad_x) <= cx <= (px2 + pad_x) and (py1 - pad_y) <= cy <= (py2 + pad_y):
                area = pw * ph
                if area < best_area:
                    best_area = area
                    best_idx = i

        if best_idx is not None:
            result[best_idx].append(ppe)

    return result
