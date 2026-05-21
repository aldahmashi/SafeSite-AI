from fastapi import APIRouter, HTTPException
from app.schemas.stream import StreamStartRequest, StreamStatus

router = APIRouter(prefix="/api/streams", tags=["Streams"])

# In-memory store for MVP; will be replaced with DB-backed state
_active_streams: dict[str, dict] = {}


@router.post("/start", response_model=StreamStatus, status_code=201)
def start_stream(req: StreamStartRequest):
    import uuid
    stream_id = str(uuid.uuid4())
    _active_streams[stream_id] = {
        "url": req.url,
        "name": req.name or req.url,
        "status": "running",
        "incident_count": 0,
    }
    # TODO: launch stream_processor.start_stream(stream_id, req.url) in background thread
    return StreamStatus(
        stream_id=stream_id,
        status="running",
        url=req.url,
        incident_count=0,
    )


@router.post("/stop/{stream_id}")
def stop_stream(stream_id: str):
    if stream_id not in _active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    _active_streams[stream_id]["status"] = "stopped"
    # TODO: signal stream_processor.stop_stream(stream_id)
    return {"stream_id": stream_id, "status": "stopped"}


@router.get("/{stream_id}/status", response_model=StreamStatus)
def get_stream_status(stream_id: str):
    s = _active_streams.get(stream_id)
    if not s:
        raise HTTPException(status_code=404, detail="Stream not found")
    return StreamStatus(stream_id=stream_id, **s)


@router.get("/{stream_id}/incidents")
def get_stream_incidents(stream_id: str):
    if stream_id not in _active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    # TODO: return incidents from DB filtered by stream session
    return []
