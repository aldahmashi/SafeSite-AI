"""
Live RTSP / webcam stream processor.
Reads frames in a background thread, runs YOLO, generates real-time alerts.
Implemented in Phase 3.
"""


class StreamProcessor:
    def start(self, stream_id: str, url: str) -> None:
        raise NotImplementedError("StreamProcessor not yet implemented — Phase 3")

    def stop(self, stream_id: str) -> None:
        raise NotImplementedError("StreamProcessor not yet implemented — Phase 3")
