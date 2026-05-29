from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
import uuid
from pathlib import Path

from app.database import get_db
from app.config import settings
from app.models.video import Video, VideoStatus
from app.schemas.video import VideoRead, VideoSummary
from app.services.video_processor import process_video_task

router = APIRouter(prefix="/api/videos", tags=["Videos"])


@router.post("/upload", response_model=VideoRead, status_code=201)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    allowed = {".mp4", ".mov", ".avi", ".mkv"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    unique_name = f"{uuid.uuid4()}{suffix}"
    save_path = Path(settings.upload_dir) / unique_name
    with save_path.open("wb") as dest:
        shutil.copyfileobj(file.file, dest)

    video = Video(
        filename=file.filename,
        original_path=str(save_path),
        status=VideoStatus.uploaded,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    background_tasks.add_task(process_video_task, video.id)
    return video


@router.get("", response_model=List[VideoRead])
def list_videos(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Video).order_by(Video.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{video_id}", response_model=VideoRead)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/status")
def get_video_status(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"video_id": video_id, "status": video.status}


@router.get("/{video_id}/incidents")
def get_video_incidents(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video.incidents


@router.get("/{video_id}/summary", response_model=VideoSummary)
def get_video_summary(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    incidents = video.incidents
    high_risk = [i for i in incidents if i.risk_level in ("HIGH", "CRITICAL")]

    # Peak simultaneous workers (sweep-line, immune to ByteTrack ID-switch inflation)
    if not video.workers:
        total_workers = 0
    else:
        events: list[tuple[float, int]] = []
        for w in video.workers:
            if w.first_seen_timestamp is not None and w.last_seen_timestamp is not None:
                events.append((w.first_seen_timestamp, +1))
                events.append((w.last_seen_timestamp, -1))
        events.sort(key=lambda e: (e[0], e[1]))
        peak = current = 0
        for _, delta in events:
            current += delta
            peak = max(peak, current)
        total_workers = peak

    # Compliance = fraction of workers with NO violations of that type
    # Use distinct worker IDs so repeated cooldown-gated incidents don't over-penalise
    def _distinct_violators(vtype: str) -> int:
        tracked = {i.worker_id for i in incidents if i.violation_type == vtype and i.worker_id is not None}
        has_untracked = any(i.worker_id is None and i.violation_type == vtype for i in incidents)
        return len(tracked) + (1 if has_untracked else 0)

    safe_base = max(total_workers, 1)
    helmet_violators = _distinct_violators("NO_HELMET")
    vest_violators   = _distinct_violators("NO_VEST")

    helmet_pct = 100.0 if total_workers == 0 else max(0.0, (1.0 - helmet_violators / safe_base) * 100.0)
    vest_pct   = 100.0 if total_workers == 0 else max(0.0, (1.0 - vest_violators   / safe_base) * 100.0)

    return VideoSummary(
        video=video,
        total_workers=total_workers,
        total_incidents=len(incidents),
        high_risk_incidents=len(high_risk),
        helmet_compliance_pct=round(helmet_pct, 1),
        vest_compliance_pct=round(vest_pct, 1),
    )


@router.get("/{video_id}/download")
def download_annotated_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if not video.output_path or not Path(video.output_path).exists():
        raise HTTPException(status_code=404, detail="Annotated video not yet available")
    return FileResponse(video.output_path, media_type="video/mp4", filename=f"annotated_{video.filename}")


@router.post("/{video_id}/reprocess", response_model=VideoRead)
def reprocess_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    from datetime import datetime
    from app.models.incident import Incident
    from app.models.worker import Worker

    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status == VideoStatus.processing:
        raise HTTPException(status_code=409, detail="Video is already being processed")

    # Clear stale data from previous run
    db.query(Incident).filter(Incident.video_id == video_id).delete()
    db.query(Worker).filter(Worker.video_id == video_id).delete()

    video.status = VideoStatus.uploaded
    video.output_path = None
    video.safety_score = None
    video.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(video)
    background_tasks.add_task(process_video_task, video.id)
    return video


@router.delete("/{video_id}", status_code=204)
def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    db.delete(video)
    db.commit()
