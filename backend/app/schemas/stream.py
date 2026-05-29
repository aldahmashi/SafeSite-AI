from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StreamStartRequest(BaseModel):
    url: str
    name: Optional[str] = None


class StreamStatus(BaseModel):
    stream_id: str
    name: str
    status: str          # running | stopped | error
    url: str
    incident_count: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None


class StreamRead(BaseModel):
    id: int
    stream_id: str
    name: str
    url: str
    status: str
    incident_count: int
    error_message: Optional[str] = None
    started_at: datetime
    stopped_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
