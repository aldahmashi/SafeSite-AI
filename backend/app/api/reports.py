from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List

from app.database import get_db
from app.models.incident import Incident
from app.models.report import Report
from app.models.video import Video, VideoStatus
from app.schemas.report import ReportRead
from app.services.report_generator import report_generator

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("/generate/{video_id}", response_model=ReportRead, status_code=201)
def generate_report(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != VideoStatus.completed:
        raise HTTPException(
            status_code=400,
            detail="Video must be in 'completed' state before generating a report.",
        )

    pdf_path = report_generator.generate(video_id, db)

    # Build a human-readable summary
    incidents = (
        db.query(Incident).filter(Incident.video_id == video_id).all()
    )
    no_helmet = sum(1 for i in incidents if i.violation_type.value == "NO_HELMET")
    no_vest   = sum(1 for i in incidents if i.violation_type.value == "NO_VEST")
    score_txt = (
        f"Safety score: {video.safety_score:.1f}/100. "
        if video.safety_score is not None
        else ""
    )
    summary = (
        f"{len(incidents)} incidents detected "
        f"({no_helmet} no-helmet, {no_vest} no-vest). "
        f"{score_txt}"
        f"{'PDF report generated.' if pdf_path else 'PDF generation failed — check reportlab installation.'}"
    )

    report = Report(video_id=video_id, report_path=pdf_path, summary=summary)
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
        raise HTTPException(
            status_code=404,
            detail="PDF file not found. Ensure reportlab is installed and regenerate.",
        )
    return FileResponse(
        report.report_path,
        media_type="application/pdf",
        filename=f"safesite_report_{report_id}.pdf",
    )
