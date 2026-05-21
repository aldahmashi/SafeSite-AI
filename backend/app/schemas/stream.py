from pydantic import BaseModel
from typing import Optional


class StreamStartRequest(BaseModel):
    url: str
    name: Optional[str] = None


class StreamStatus(BaseModel):
    stream_id: str
    status: str   # running | stopped | error
    url: str
    incident_count: int
