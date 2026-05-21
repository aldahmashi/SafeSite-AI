"""
Full video processing pipeline:
  open → read frames → detect → track → check violations
  → annotate → save incidents → export annotated video.
Implemented in Phase 2.
"""


class VideoProcessor:
    def process(self, video_id: int) -> dict:
        raise NotImplementedError("VideoProcessor not yet implemented — Phase 2")
