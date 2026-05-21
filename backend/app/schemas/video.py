from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.models.video import VideoStatus, VideoSource


class VideoBase(BaseModel):
    filename: str
    source_type: VideoSource = VideoSource.upload


class VideoCreate(VideoBase):
    original_path: str


class VideoRead(VideoBase):
    id: int
    status: VideoStatus
    duration_seconds: Optional[float] = None
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    safety_score: Optional[float] = None
    output_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VideoSummary(BaseModel):
    video: VideoRead
    total_workers: int
    total_incidents: int
    high_risk_incidents: int
    helmet_compliance_pct: float
    vest_compliance_pct: float
