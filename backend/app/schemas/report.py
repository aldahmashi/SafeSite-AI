from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class ReportRead(BaseModel):
    id: int
    video_id: int
    report_path: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
