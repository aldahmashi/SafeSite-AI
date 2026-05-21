"""
WorkerTracker — per-worker business state across frames.

The CV tracking algorithm (ByteTrack) lives inside Ultralytics YOLO.
This class handles:
  - A registry mapping YOLO track IDs → WorkerState
  - first_seen / last_seen timestamps
  - Violation cooldown windows: don't log the same violation for the
    same worker more than once per cooldown window

Create one WorkerTracker instance per video processing session.
This class is NOT thread-safe; it is designed for single-threaded use.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorkerState:
    track_id: int
    db_worker_id: Optional[int] = None    # FK to workers.id once persisted
    first_seen_ts: float = 0.0            # seconds from video start
    last_seen_ts: float = 0.0
    # Maps violation_type (str) → timestamp of last recorded violation
    cooldowns: dict[str, float] = field(default_factory=dict, repr=False)


class WorkerTracker:
    """
    Registry of workers seen during one video/stream session.

    Args:
        cooldown_seconds: Minimum gap between recording the same violation
                          for the same worker (default 5 s).
    """

    def __init__(self, cooldown_seconds: float = 5.0) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._registry: dict[int, WorkerState] = {}

    # ── worker registry ───────────────────────────────────────────────────────

    def update(self, track_id: int, timestamp: float) -> WorkerState:
        """Register a new worker or refresh their last-seen time."""
        if track_id not in self._registry:
            self._registry[track_id] = WorkerState(
                track_id=track_id,
                first_seen_ts=timestamp,
                last_seen_ts=timestamp,
            )
        else:
            self._registry[track_id].last_seen_ts = timestamp
        return self._registry[track_id]

    def set_db_id(self, track_id: int, db_id: int) -> None:
        """Link a YOLO track ID to its persisted DB workers.id."""
        if track_id in self._registry:
            self._registry[track_id].db_worker_id = db_id

    def get(self, track_id: int) -> Optional[WorkerState]:
        return self._registry.get(track_id)

    def all_workers(self) -> dict[int, WorkerState]:
        return dict(self._registry)

    # ── cooldown helpers ──────────────────────────────────────────────────────

    def can_record(
        self, track_id: int, violation_type: str, timestamp: float
    ) -> bool:
        """
        Return True if enough time has elapsed since the last identical
        violation was recorded for this worker.
        Always True for unknown track IDs (first occurrence).
        """
        state = self._registry.get(track_id)
        if state is None:
            return True
        last = state.cooldowns.get(violation_type, -(self.cooldown_seconds + 1.0))
        return (timestamp - last) >= self.cooldown_seconds

    def mark_recorded(
        self, track_id: int, violation_type: str, timestamp: float
    ) -> None:
        """Reset the cooldown clock after a violation has been persisted."""
        state = self._registry.get(track_id)
        if state is not None:
            state.cooldowns[violation_type] = timestamp
