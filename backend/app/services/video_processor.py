"""
VideoProcessor — full per-video analysis pipeline.

Flow
────
  1.  Load Video record → validate it is in 'uploaded' state
  2.  Open with OpenCV → read fps / resolution / frame count
  3.  Update DB: status=processing, store metadata
  4.  Initialise PPEDetector (load weights), WorkerTracker, ViolationEngine
  5.  Open VideoWriter for annotated output
  6.  Frame loop:
        • Skip non-sampled frames (frame_skip setting) — pass-through to writer
        • Run detector.track_frame()
        • Update worker registry in WorkerTracker (persist new workers to DB)
        • Run ViolationEngine.process_frame()
        • Persist each ViolationEvent as an Incident row
        • Save cropped violation screenshot to violation_frames/
        • Annotate frame and write to output
  7.  Calculate safety score from all incidents
  8.  Update DB: status=completed, output_path, safety_score
  9.  Return ProcessingSummary dict

Entry point
───────────
  process_video_task(video_id)   — called as a FastAPI BackgroundTask;
                                   opens its own DB session.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2

from app.config import settings
from app.database import SessionLocal
from app.models.incident import Incident, RiskLevel, ViolationType
from app.models.video import Video, VideoStatus
from app.models.worker import Worker
from app.services.detector import PPEDetector
from app.services.scoring import calculate_safety_score
from app.services.tracker import WorkerTracker
from app.services.violation_engine import ViolationEngine, ViolationEvent
from app.utils.annotation_utils import (
    draw_detections,
    draw_frame_overlay,
    draw_violations,
)

logger = logging.getLogger(__name__)

# Minimum frames between progress log messages
_LOG_INTERVAL = 150


# ── background-task entry point ────────────────────────────────────────────────

def process_video_task(video_id: int) -> None:
    """
    Called by FastAPI's BackgroundTasks after a successful video upload.
    Creates its own DB session so it is independent of the request lifecycle.
    """
    db = SessionLocal()
    try:
        VideoProcessor().process(video_id=video_id, db=db)
    except Exception:
        logger.exception("Unhandled error in process_video_task video_id=%s", video_id)
        _mark_failed(db, video_id, "Unexpected error — check server logs.")
    finally:
        db.close()


# ── processor ─────────────────────────────────────────────────────────────────

class VideoProcessor:
    """
    Stateless: create one instance per call or reuse across calls.
    All mutable state is in the DB and local variables inside process().
    """

    def process(self, video_id: int, db) -> dict:
        """
        Run the full analysis pipeline.
        Always returns a summary dict; sets video.status to 'failed' on error.
        """
        # ── 1. Load and validate record ───────────────────────────────────────
        video: Optional[Video] = db.get(Video, video_id)
        if video is None:
            raise ValueError(f"Video {video_id} not found in database.")

        if video.status not in (VideoStatus.uploaded,):
            logger.warning(
                "video_id=%s already in state '%s', skipping.",
                video_id, video.status,
            )
            return {"status": "skipped", "reason": f"state is {video.status}"}

        # ── 2. Open video ─────────────────────────────────────────────────────
        cap = cv2.VideoCapture(video.original_path)
        if not cap.isOpened():
            msg = f"Cannot open video file: {video.original_path}"
            _mark_failed(db, video_id, msg)
            return {"error": msg}

        fps     = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = n_frames / fps if fps > 0 else 0.0

        # ── 3. Update DB with metadata ────────────────────────────────────────
        video.fps            = fps
        video.total_frames   = n_frames
        video.duration_seconds = duration
        video.status         = VideoStatus.processing
        video.updated_at     = datetime.utcnow()
        db.commit()

        logger.info(
            "video_id=%s  %.1fs  %.0f fps  %dx%d  %d frames",
            video_id, duration, fps, width, height, n_frames,
        )

        # ── 4. Prepare output paths ───────────────────────────────────────────
        out_dir = Path(settings.output_dir)
        vf_dir  = Path(settings.violation_frames_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        vf_dir.mkdir(parents=True, exist_ok=True)

        stem        = Path(video.filename).stem
        out_name    = f"annotated_{video_id}_{stem}.mp4"
        output_path = out_dir / out_name

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        # ── 5. Initialise CV services ─────────────────────────────────────────
        detector = PPEDetector(
            weights_path=settings.yolo_weights_path,
            confidence=0.4,
            device="cpu",
        )
        try:
            detector.load()
        except (FileNotFoundError, ImportError) as exc:
            cap.release()
            writer.release()
            _mark_failed(db, video_id, str(exc))
            return {"error": str(exc)}

        tracker = WorkerTracker(
            cooldown_seconds=float(settings.violation_cooldown_seconds)
        )
        engine = ViolationEngine(tracker=tracker, infer_from_absence=False)

        # ── 6. Frame loop ─────────────────────────────────────────────────────
        frame_skip      = max(1, settings.frame_skip)
        raw_idx         = 0     # every frame read
        processed_idx   = 0     # frames actually sent to YOLO
        total_violations = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            raw_idx += 1
            timestamp = raw_idx / fps

            # Pass non-sampled frames straight to the output video
            if raw_idx % frame_skip != 0:
                writer.write(frame)
                continue

            processed_idx += 1

            # ── Detection + tracking ──────────────────────────────────────────
            detections = detector.track_frame(frame)

            # ── Update worker registry ────────────────────────────────────────
            for det in detections:
                if det["class_name"].lower() in ("person", "worker"):
                    tid = det.get("track_id")
                    if tid is not None:
                        ws = tracker.update(tid, timestamp)
                        if ws.db_worker_id is None:
                            db_id = self._get_or_create_worker(
                                video_id, tid, timestamp, db
                            )
                            tracker.set_db_id(tid, db_id)

            # ── Violation checks ──────────────────────────────────────────────
            events = engine.process_frame(raw_idx, timestamp, detections)

            # ── Persist incidents ─────────────────────────────────────────────
            for ev in events:
                incident = self._save_incident(ev, video_id, db)
                shot = self._save_screenshot(frame, ev, incident.id, vf_dir)
                if shot:
                    incident.screenshot_path = shot
                    db.commit()
                total_violations += 1

            # ── Annotate and write ────────────────────────────────────────────
            annotated = frame.copy()
            draw_detections(annotated, detections)
            draw_violations(annotated, events)
            draw_frame_overlay(annotated, raw_idx, timestamp, total_violations)
            writer.write(annotated)

            if processed_idx % _LOG_INTERVAL == 0:
                logger.info(
                    "video_id=%s  frame %d/%d  violations=%d",
                    video_id, raw_idx, n_frames, total_violations,
                )

        cap.release()
        writer.release()

        # ── 7. Final scoring ──────────────────────────────────────────────────
        incidents = (
            db.query(Incident).filter(Incident.video_id == video_id).all()
        )
        safety_score = calculate_safety_score(incidents)

        # Update last_seen for all workers
        for tid, ws in tracker.all_workers().items():
            if ws.db_worker_id:
                w = db.get(Worker, ws.db_worker_id)
                if w:
                    w.last_seen_timestamp = ws.last_seen_ts
        db.commit()

        # ── 8. Finalise video record ──────────────────────────────────────────
        video.output_path  = str(output_path)
        video.safety_score = safety_score
        video.status       = VideoStatus.completed
        video.updated_at   = datetime.utcnow()
        db.commit()

        summary = {
            "video_id":          video_id,
            "status":            "completed",
            "total_frames_read": raw_idx,
            "frames_processed":  processed_idx,
            "total_workers":     len(tracker.all_workers()),
            "total_violations":  total_violations,
            "safety_score":      safety_score,
            "output_path":       str(output_path),
        }
        logger.info("video_id=%s done  %s", video_id, summary)
        return summary

    # ── DB helpers ─────────────────────────────────────────────────────────────

    def _get_or_create_worker(
        self, video_id: int, track_id: int, timestamp: float, db
    ) -> int:
        """Return the DB workers.id for this track_id, creating if needed."""
        existing = (
            db.query(Worker)
            .filter(Worker.video_id == video_id, Worker.tracker_id == track_id)
            .first()
        )
        if existing:
            return existing.id

        worker = Worker(
            video_id=video_id,
            tracker_id=track_id,
            first_seen_timestamp=timestamp,
            last_seen_timestamp=timestamp,
            total_violations=0,
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)
        return worker.id

    def _save_incident(
        self, ev: ViolationEvent, video_id: int, db
    ) -> Incident:
        """Persist a ViolationEvent as an Incident row and bump worker count."""
        incident = Incident(
            video_id=video_id,
            worker_id=ev.db_worker_id,
            timestamp_seconds=ev.timestamp,
            frame_number=ev.frame_number,
            violation_type=ViolationType(ev.violation_type),
            risk_level=RiskLevel(ev.risk_level),
            confidence=ev.confidence,
            bbox=",".join(str(v) for v in ev.worker_bbox),
            description=ev.description,
        )
        db.add(incident)

        if ev.db_worker_id:
            worker = db.get(Worker, ev.db_worker_id)
            if worker:
                worker.total_violations += 1

        db.commit()
        db.refresh(incident)
        return incident

    def _save_screenshot(
        self,
        frame,
        ev: ViolationEvent,
        incident_id: int,
        output_dir: Path,
    ) -> Optional[str]:
        """
        Save a padded crop around the violating worker as JPEG.
        Returns the file path string or None on failure.
        """
        try:
            x1, y1, x2, y2 = ev.worker_bbox
            h, w = frame.shape[:2]
            pad = 40
            cx1 = max(0, x1 - pad)
            cy1 = max(0, y1 - pad)
            cx2 = min(w, x2 + pad)
            cy2 = min(h, y2 + pad)

            crop = frame[cy1:cy2, cx1:cx2]
            if crop.size == 0:
                return None

            filename = f"incident_{incident_id}_{ev.violation_type}.jpg"
            path = output_dir / filename
            cv2.imwrite(str(path), crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return str(path)
        except Exception as exc:
            logger.warning(
                "Screenshot failed for incident_id=%s: %s", incident_id, exc
            )
            return None


# ── utilities ─────────────────────────────────────────────────────────────────

def _mark_failed(db, video_id: int, reason: str) -> None:
    logger.error("video_id=%s  FAILED: %s", video_id, reason)
    try:
        video = db.get(Video, video_id)
        if video:
            video.status     = VideoStatus.failed
            video.updated_at = datetime.utcnow()
            db.commit()
    except Exception:
        pass
