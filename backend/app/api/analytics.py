"""
Analytics overview endpoint.

All compliance metrics use DISTINCT violating workers as the numerator,
not raw incident counts, so repeated cooldown-gated incidents for the same
worker don't inflate the violation rate.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _peak_workers(workers) -> int:
    if not workers:
        return 0
    events: list[tuple[float, int]] = []
    for w in workers:
        if w.first_seen_timestamp is not None and w.last_seen_timestamp is not None:
            events.append((w.first_seen_timestamp, +1))
            events.append((w.last_seen_timestamp, -1))
    if not events:
        return 0
    events.sort(key=lambda e: (e[0], e[1]))
    peak = current = 0
    for _, delta in events:
        current += delta
        peak = max(peak, current)
    return peak


def _distinct_violators(incidents, violation_type_value: str) -> int:
    """
    Count distinct workers who had at least one violation of the given type.
    worker_id=None incidents count as one collective "untracked violator".
    """
    tracked = {
        i.worker_id
        for i in incidents
        if i.violation_type.value == violation_type_value and i.worker_id is not None
    }
    has_untracked = any(
        i.worker_id is None and i.violation_type.value == violation_type_value
        for i in incidents
    )
    return len(tracked) + (1 if has_untracked else 0)


@router.get("/overview")
def analytics_overview(db: Session = Depends(get_db)):
    from app.models.incident import Incident, RiskLevel
    from app.models.video import Video, VideoStatus
    from app.models.worker import Worker

    completed_videos = (
        db.query(Video).filter(Video.status == VideoStatus.completed).all()
    )
    all_incidents = db.query(Incident).all()

    from app.services.scoring import calculate_safety_score

    total_workers = 0
    safety_scores: list[float] = []

    for video in completed_videos:
        workers = db.query(Worker).filter(Worker.video_id == video.id).all()
        total_workers += _peak_workers(workers)
        # Recompute score live with the current formula so stale stored values don't distort
        video_incidents = db.query(Incident).filter(Incident.video_id == video.id).all()
        score = calculate_safety_score(video_incidents)
        safety_scores.append(score)
        # Persist corrected score back to DB if it differs
        if video.safety_score != score:
            video.safety_score = score
    db.commit()

    safe_base = max(total_workers, 1)

    helmet_violators = _distinct_violators(all_incidents, "NO_HELMET")
    vest_violators   = _distinct_violators(all_incidents, "NO_VEST")
    mask_violators   = _distinct_violators(all_incidents, "NO_MASK")

    helmet_pct = max(0.0, (1.0 - helmet_violators / safe_base) * 100.0)
    vest_pct   = max(0.0, (1.0 - vest_violators   / safe_base) * 100.0)
    mask_pct   = max(0.0, (1.0 - mask_violators   / safe_base) * 100.0)

    high_risk = sum(
        1 for i in all_incidents
        if i.risk_level in (RiskLevel.high, RiskLevel.critical)
    )

    violation_breakdown: dict[str, int] = {}
    for i in all_incidents:
        vt = i.violation_type.value
        violation_breakdown[vt] = violation_breakdown.get(vt, 0) + 1

    risk_breakdown: dict[str, int] = {}
    for i in all_incidents:
        rl = i.risk_level.value
        risk_breakdown[rl] = risk_breakdown.get(rl, 0) + 1

    return {
        "total_workers":         total_workers,
        "total_incidents":       len(all_incidents),
        "high_risk_incidents":   high_risk,
        "helmet_compliance_pct": round(helmet_pct, 1),
        "vest_compliance_pct":   round(vest_pct, 1),
        "mask_compliance_pct":   round(mask_pct, 1),
        "avg_safety_score":      round(sum(safety_scores) / len(safety_scores), 1) if safety_scores else 0.0,
        "violation_breakdown":   violation_breakdown,
        "risk_breakdown":        risk_breakdown,
        "completed_videos":      len(completed_videos),
    }
