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
    no_helmet = sum(1 for i in incidents if i.violation_type == "NO_HELMET")
    no_vest = sum(1 for i in incidents if i.violation_type == "NO_VEST")
    total_workers = len(video.workers)

    helmet_pct = 100.0 if total_workers == 0 else max(0.0, 100.0 - (no_helmet / max(total_workers, 1) * 100))
    vest_pct = 100.0 if total_workers == 0 else max(0.0, 100.0 - (no_vest / max(total_workers, 1) * 100))

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


@router.delete("/{video_id}", status_code=204)
def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    db.delete(video)
    db.commit()
