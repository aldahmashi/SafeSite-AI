"""
YOLO-based PPE detector.
Wraps Ultralytics YOLO model and returns structured detections per frame.
Implemented in Phase 2.
"""
from typing import Any


class PPEDetector:
    def __init__(self, weights_path: str, confidence: float = 0.4):
        self.weights_path = weights_path
        self.confidence = confidence
        self._model = None

    def load(self) -> None:
        raise NotImplementedError("PPEDetector not yet implemented — Phase 2")

    def detect(self, frame: Any) -> list[dict]:
        raise NotImplementedError("PPEDetector not yet implemented — Phase 2")
