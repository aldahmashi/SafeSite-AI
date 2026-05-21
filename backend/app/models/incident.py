from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ViolationType(str, enum.Enum):
    no_helmet = "NO_HELMET"
    no_vest = "NO_VEST"
    high_risk_zone = "HIGH_RISK_ZONE"
    machinery_proximity = "MACHINERY_PROXIMITY_RISK"
    fall_risk = "FALL_RISK"


class RiskLevel(str, enum.Enum):
    low = "LOW"
    medium = "MEDIUM"
    high = "HIGH"
    critical = "CRITICAL"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)
    timestamp_seconds = Column(Float, nullable=False)
    frame_number = Column(Integer, nullable=False)
    violation_type = Column(SAEnum(ViolationType), nullable=False)
    risk_level = Column(SAEnum(RiskLevel), nullable=False)
    confidence = Column(Float, nullable=True)
    bbox = Column(String, nullable=True)        # stored as "x1,y1,x2,y2"
    screenshot_path = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    video = relationship("Video", back_populates="incidents")
    worker = relationship("Worker", back_populates="incidents")
