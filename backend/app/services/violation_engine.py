"""
Violation detection logic engine.
Associates PPE detections with worker bounding boxes,
applies rules, and enforces per-worker cooldown windows.
Implemented in Phase 2.
"""


class ViolationEngine:
    def process_frame(
        self,
        frame_number: int,
        timestamp: float,
        detections: list[dict],
        zones: list[dict] | None = None,
    ) -> list[dict]:
        raise NotImplementedError("ViolationEngine not yet implemented — Phase 2")
