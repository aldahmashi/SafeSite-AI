from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.database import get_db
from app.models.stream import Stream, StreamStatus
from app.schemas.stream import StreamStartRequest, StreamStatus as StreamStatusSchema, StreamRead
from app.services.stream_processor import registry

router = APIRouter(prefix="/api/streams", tags=["Streams"])


@router.post("/start", response_model=StreamStatusSchema, status_code=201)
def start_stream(req: StreamStartRequest, db: Session = Depends(get_db)):
    stream_id = str(uuid.uuid4())
    name = req.name or req.url

    # Persist to DB
    record = Stream(
        stream_id=stream_id,
        name=name,
        url=req.url,
        status=StreamStatus.running,
    )
    db.add(record)
    db.commit()

    # Start background thread
    session = registry.start(stream_id=stream_id, url=req.url, name=name)

    return StreamStatusSchema(
        stream_id=stream_id,
        name=name,
        status="running",
        url=req.url,
        incident_count=0,
        error_message=None,
        started_at=record.started_at,
    )


@router.post("/stop/{stream_id}", response_model=StreamStatusSchema)
def stop_stream(stream_id: str, db: Session = Depends(get_db)):
    record = db.query(Stream).filter(Stream.stream_id == stream_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Stream not found")

    # Signal thread
    registry.stop(stream_id)

    # Optimistically update DB
    record.status = StreamStatus.stopped
    record.stopped_at = datetime.utcnow()
    db.commit()

    return StreamStatusSchema(
        stream_id=stream_id,
        name=record.name,
        status="stopped",
        url=record.url,
        incident_count=record.incident_count,
        error_message=None,
        started_at=record.started_at,
    )


@router.get("", response_model=List[StreamRead])
def list_streams(db: Session = Depends(get_db)):
    streams = db.query(Stream).order_by(Stream.started_at.desc()).all()
    # Merge live incident counts from in-memory registry
    result = []
    for s in streams:
        live = registry.get(s.stream_id)
        if live:
            s.incident_count = live.incident_count
        result.append(s)
    return result


@router.get("/{stream_id}/status", response_model=StreamStatusSchema)
def get_stream_status(stream_id: str, db: Session = Depends(get_db)):
    record = db.query(Stream).filter(Stream.stream_id == stream_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Stream not found")

    # Merge live state
    live = registry.get(stream_id)
    status = live.status if live else record.status.value
    count = live.incident_count if live else record.incident_count
    error = live.error_message if live else record.error_message

    return StreamStatusSchema(
        stream_id=stream_id,
        name=record.name,
        status=status,
        url=record.url,
        incident_count=count,
        error_message=error,
        started_at=record.started_at,
    )


@router.delete("/{stream_id}", status_code=204)
def delete_stream(stream_id: str, db: Session = Depends(get_db)):
    record = db.query(Stream).filter(Stream.stream_id == stream_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Stream not found")
    registry.stop(stream_id)
    registry.remove(stream_id)
    db.delete(record)
    db.commit()
