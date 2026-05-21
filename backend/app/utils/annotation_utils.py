"""
OpenCV annotation helpers.

All functions modify the frame in-place and return None,
so the caller controls when to copy.
"""
from __future__ import annotations

import cv2

from app.services.detector import color_for
from app.services.violation_engine import ViolationEvent

# ── font constants ─────────────────────────────────────────────────────────────
_FONT       = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE = 0.50
_THICKNESS  = 1
_V_FONT_SCALE = 0.55
_V_THICKNESS  = 2

_WHITE  = (255, 255, 255)
_BLACK  = (0,   0,   0)
_RED    = (0,   0,   220)


def draw_detections(frame, detections: list[dict]) -> None:
    """
    Draw every YOLO detection box with a class label and optional track ID.
    Class-specific colours from detector.color_for().
    """
    for det in detections:
        color = color_for(det["class_name"])
        x1, y1, x2, y2 = det["bbox_xyxy"]

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = det["class_name"]
        if det.get("track_id") is not None:
            label = f"#{det['track_id']} {label}"
        label += f" {det['confidence']:.0%}"

        # Filled label background so text is always readable
        (lw, lh), baseline = cv2.getTextSize(
            label, _FONT, _FONT_SCALE, _THICKNESS
        )
        top = max(y1 - lh - baseline - 4, 0)
        cv2.rectangle(
            frame,
            (x1, top),
            (x1 + lw + 4, y1),
            color,
            cv2.FILLED,
        )
        cv2.putText(
            frame, label,
            (x1 + 2, y1 - baseline - 2),
            _FONT, _FONT_SCALE, _WHITE, _THICKNESS,
        )


def draw_violations(frame, events: list[ViolationEvent]) -> None:
    """
    Overlay a red border + violation banner on each violating worker bbox.
    Called AFTER draw_detections so it renders on top.
    """
    for ev in events:
        x1, y1, x2, y2 = ev.worker_bbox

        # Thick red border around the person
        cv2.rectangle(frame, (x1, y1), (x2, y2), _RED, 3)

        banner = f"⚠ {ev.violation_type}"
        (bw, bh), base = cv2.getTextSize(
            banner, _FONT, _V_FONT_SCALE, _V_THICKNESS
        )
        top = max(y1 - bh - base - 6, 0)
        cv2.rectangle(frame, (x1, top), (x1 + bw + 6, y1), _RED, cv2.FILLED)
        cv2.putText(
            frame, banner,
            (x1 + 3, y1 - base - 2),
            _FONT, _V_FONT_SCALE, _WHITE, _V_THICKNESS,
        )


def draw_frame_overlay(
    frame,
    frame_number: int,
    timestamp: float,
    total_violations: int,
) -> None:
    """
    Top-left HUD: frame counter, timestamp, running violation count.
    Drawn with a shadow for readability on any background.
    """
    text = (
        f"Frame {frame_number}  |  {timestamp:.1f}s"
        f"  |  Violations: {total_violations}"
    )
    # Shadow
    cv2.putText(frame, text, (11, 25), _FONT, 0.6, _BLACK, 3)
    # Foreground
    cv2.putText(frame, text, (10, 24), _FONT, 0.6, _WHITE, 1)
