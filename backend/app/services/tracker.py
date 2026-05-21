"""
Worker tracker using ByteTrack (via Ultralytics).
Assigns persistent track IDs across frames.
Implemented in Phase 2.
"""


class WorkerTracker:
    def update(self, detections: list[dict], frame_shape: tuple) -> list[dict]:
        raise NotImplementedError("WorkerTracker not yet implemented — Phase 2")
