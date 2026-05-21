from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List

from app.database import get_db
from app.models.report import Report
from app.models.video import Video
from app.schemas.report import ReportRead

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("/generate/{video_id}", response_model=ReportRead, status_code=201)
def generate_report(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # TODO: call report_generator.generate(video_id, db) and persist
    report = Report(video_id=video_id, summary="Report generation not yet implemented.")
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=List[ReportRead])
def list_reports(db: Session = Depends(get_db)):
    return db.query(Report).order_by(Report.created_at.desc()).all()


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.report_path or not Path(report.report_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not yet generated")
    return FileResponse(report.report_path, media_type="application/pdf", filename=f"report_{report_id}.pdf")
