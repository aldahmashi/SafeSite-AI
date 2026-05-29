"""
Live RTSP / webcam stream processor.

Each stream runs in its own background thread:
  1. Open source with OpenCV (webcam index or RTSP URL)
  2. Read frames continuously
  3. Run PPEDetector + ViolationEngine per sampled frame
  4. Persist incidents to DB
  5. Optionally fire alerts via alert_service

Thread lifecycle:
  StreamRegistry.start(stream_id, url, name)  →  spawns thread
  StreamRegistry.stop(stream_id)              →  signals thread to exit
  StreamRegistry.get(stream_id)               →  returns StreamSession snapshot
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import cv2

from app.config import settings
from app.database import SessionLocal
from app.models.incident import Incident, RiskLevel, ViolationType
from app.models.stream import Stream, StreamStatus
from app.services.detector import PPEDetector
from app.services.tracker import WorkerTracker
from app.services.violation_engine import ViolationEngine

logger = logging.getLogger(__name__)

_FRAME_SKIP = 5          # process every Nth frame from stream
_MAX_OPEN_RETRIES = 3    # retries if stream fails to open
_RETRY_DELAY = 3.0       # seconds between open retries


@dataclass
class StreamSession:
    stream_id: str
    url: str
    name: str
    status: str = "running"           # running | stopped | error
    incident_count: int = 0
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    stopped_at: Optional[datetime] = None
    _stop_event: threading.Event = field(default_factory=threading.Event, repr=False)
    _thread: Optional[threading.Thread] = field(default=None, repr=False)

    def request_stop(self) -> None:
        self._stop_event.set()

    def is_running(self) -> bool:
        return self.status == "running"


class StreamRegistry:
    """
    Process-level singleton that manages all active stream sessions.
    Thread-safe via a single lock.
    """
    _instance: Optional["StreamRegistry"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "StreamRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions: dict[str, StreamSession] = {}
            cls._instance._sessions_lock = threading.Lock()
        return cls._instance

    def start(self, stream_id: str, url: str, name: str) -> StreamSession:
        session = StreamSession(stream_id=stream_id, url=url, name=name)
        with self._sessions_lock:
            self._sessions[stream_id] = session

        thread = threading.Thread(
            target=_run_stream,
            args=(session,),
            name=f"stream-{stream_id[:8]}",
            daemon=True,
        )
        session._thread = thread
        thread.start()
        logger.info("Stream %s started: %s", stream_id[:8], url)
        return session

    def stop(self, stream_id: str) -> bool:
        with self._sessions_lock:
            session = self._sessions.get(stream_id)
        if not session:
            return False
        session.request_stop()
        logger.info("Stop signal sent to stream %s", stream_id[:8])
        return True

    def get(self, stream_id: str) -> Optional[StreamSession]:
        with self._sessions_lock:
            return self._sessions.get(stream_id)

    def list_all(self) -> list[StreamSession]:
        with self._sessions_lock:
            return list(self._sessions.values())

    def remove(self, stream_id: str) -> None:
        with self._sessions_lock:
            self._sessions.pop(stream_id, None)


registry = StreamRegistry()


def _run_stream(session: StreamSession) -> None:
    """
    Background thread body. Reads frames, runs inference, persists incidents.
    Updates session state in-place; also syncs status to DB.
    """
    db = SessionLocal()
    try:
        detector = PPEDetector(
            weights_path=settings.yolo_weights_path,
            confidence=0.4,
            device="cpu",
        )
        try:
            detector.load()
        except (FileNotFoundError, ImportError) as exc:
            _set_error(session, db, str(exc))
            return

        tracker = WorkerTracker(cooldown_seconds=float(settings.violation_cooldown_seconds))
        engine = ViolationEngine(tracker=tracker, infer_from_absence=False)

        cap = None
        for attempt in range(_MAX_OPEN_RETRIES):
            cap = cv2.VideoCapture(_parse_source(session.url))
            if cap.isOpened():
                break
            logger.warning(
                "Stream %s open attempt %d/%d failed",
                session.stream_id[:8], attempt + 1, _MAX_OPEN_RETRIES,
            )
            time.sleep(_RETRY_DELAY)

        if cap is None or not cap.isOpened():
            _set_error(session, db, f"Cannot open stream: {session.url}")
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        raw_idx = 0

        while not session._stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                # End of file or stream dropped — stop gracefully
                logger.info("Stream %s: no more frames.", session.stream_id[:8])
                break

            raw_idx += 1
            if raw_idx % _FRAME_SKIP != 0:
                continue

            timestamp = raw_idx / fps
            detections = detector.track_frame(frame)
            events = engine.process_frame(raw_idx, timestamp, detections)

            for ev in events:
                try:
                    incident = Incident(
                        video_id=1,          # sentinel: stream incidents share video_id=1
                        timestamp_seconds=ev.timestamp,
                        frame_number=ev.frame_number,
                        violation_type=ViolationType(ev.violation_type),
                        risk_level=RiskLevel(ev.risk_level),
                        confidence=ev.confidence,
                        bbox=",".join(str(v) for v in ev.worker_bbox),
                        description=ev.description,
                    )
                    db.add(incident)
                    db.commit()
                    session.incident_count += 1

                    # Sync incident_count to DB record
                    _update_incident_count(db, session)

                    # Fire alert for high/critical
                    if ev.risk_level in ("HIGH", "CRITICAL"):
                        _fire_alert_bg(session.name, ev)

                except Exception:
                    logger.exception("Stream %s: failed to persist incident", session.stream_id[:8])
                    db.rollback()

        cap.release()
        _mark_stopped(session, db)

    except Exception:
        logger.exception("Unhandled error in stream %s", session.stream_id[:8])
        try:
            _set_error(session, db, "Unexpected error — check logs.")
        except Exception:
            pass
    finally:
        db.close()


def _parse_source(url: str):
    """Convert '0', '1', etc. to integer for webcam; otherwise keep as RTSP URL."""
    if url.isdigit():
        return int(url)
    return url


def _set_error(session: StreamSession, db, message: str) -> None:
    session.status = "error"
    session.error_message = message
    session.stopped_at = datetime.utcnow()
    logger.error("Stream %s error: %s", session.stream_id[:8], message)
    try:
        record = db.query(Stream).filter(Stream.stream_id == session.stream_id).first()
        if record:
            record.status = StreamStatus.error
            record.error_message = message
            record.stopped_at = datetime.utcnow()
            db.commit()
    except Exception:
        db.rollback()


def _mark_stopped(session: StreamSession, db) -> None:
    session.status = "stopped"
    session.stopped_at = datetime.utcnow()
    try:
        record = db.query(Stream).filter(Stream.stream_id == session.stream_id).first()
        if record:
            record.status = StreamStatus.stopped
            record.stopped_at = datetime.utcnow()
            db.commit()
    except Exception:
        db.rollback()


def _update_incident_count(db, session: StreamSession) -> None:
    try:
        record = db.query(Stream).filter(Stream.stream_id == session.stream_id).first()
        if record:
            record.incident_count = session.incident_count
            db.commit()
    except Exception:
        db.rollback()


def _fire_alert_bg(stream_name: str, ev) -> None:
    """Fire Telegram alert in a separate thread to not block the stream loop."""
    import asyncio
    from app.services.alert_service import send_telegram_alert

    message = (
        f"🚨 *SafeSite AI Alert*\n"
        f"Stream: {stream_name}\n"
        f"Violation: {ev.violation_type.replace('_', ' ')}\n"
        f"Risk: {ev.risk_level}\n"
        f"Time: {ev.timestamp:.1f}s"
    )

    def _send():
        try:
            asyncio.run(send_telegram_alert(message))
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()
