from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.models.incident import ViolationType, RiskLevel


class IncidentRead(BaseModel):
    id: int
    video_id: int
    worker_id: Optional[int] = None
    timestamp_seconds: float
    frame_number: int
    violation_type: ViolationType
    risk_level: RiskLevel
    confidence: Optional[float] = None
    bbox: Optional[str] = None
    screenshot_path: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
