from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.incident import Incident, RiskLevel
from app.schemas.incident import IncidentRead

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentRead])
def list_incidents(
    skip: int = 0,
    limit: int = 50,
    violation_type: str | None = None,
    risk_level: str | None = None,
    video_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Incident)
    if video_id is not None:
        q = q.filter(Incident.video_id == video_id)
    if violation_type:
        q = q.filter(Incident.violation_type == violation_type.upper())
    if risk_level:
        q = q.filter(Incident.risk_level == risk_level.upper())
    return q.order_by(Incident.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/high-risk", response_model=List[IncidentRead])
def list_high_risk_incidents(db: Session = Depends(get_db)):
    return (
        db.query(Incident)
        .filter(Incident.risk_level.in_([RiskLevel.high, RiskLevel.critical]))
        .order_by(Incident.created_at.desc())
        .limit(100)
        .all()
    )


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
