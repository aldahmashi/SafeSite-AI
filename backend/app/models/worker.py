from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    tracker_id = Column(Integer, nullable=False)
    first_seen_timestamp = Column(Float, nullable=True)
    last_seen_timestamp = Column(Float, nullable=True)
    total_violations = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    video = relationship("Video", back_populates="workers")
    incidents = relationship("Incident", back_populates="worker")
