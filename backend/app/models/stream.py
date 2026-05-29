from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
import enum

from app.database import Base


class StreamStatus(str, enum.Enum):
    running = "running"
    stopped = "stopped"
    error = "error"


class Stream(Base):
    __tablename__ = "streams"

    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    status = Column(SAEnum(StreamStatus), default=StreamStatus.running, nullable=False)
    incident_count = Column(Integer, default=0, nullable=False)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    stopped_at = Column(DateTime, nullable=True)
