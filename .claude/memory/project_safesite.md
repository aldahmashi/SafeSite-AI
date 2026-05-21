---
name: project-safesite-foundation
description: SafeSite AI project context — current phase, build plan, and tech decisions
metadata:
  type: project
---

SafeSite AI is a real-time construction safety monitoring platform being built as a portfolio project.

**Why:** Portfolio-level project demonstrating CV, full-stack, agentic AI, and RAG skills.

**Phase 1 (complete):** Monorepo foundation — FastAPI skeleton, PostgreSQL docker-compose, all SQLAlchemy models (videos, workers, incidents, reports, policy_documents), all API route stubs, all service stubs, requirements.txt, Dockerfile, .env.example, .gitignore, README, docs stubs.

**Phase 2 (next):** YOLO integration — PPEDetector, WorkerTracker (ByteTrack), ViolationEngine with cooldown logic, VideoProcessor pipeline, zone_engine polygon logic, safety scoring.

**Phase 3 (after):** Live CCTV/RTSP stream processor, Telegram alert service, Next.js frontend dashboard.

**Phase 4 (after):** LangGraph AI assistant, RAG pipeline (LangChain + ChromaDB), PDF report generation (ReportLab).

**Key decisions:**
- ByteTrack via Ultralytics (not separate library) — simpler dep management
- Cooldown window (default 5s) per worker per violation type to avoid duplicate incidents
- Violation engine is stateless per call; cooldown state lives in VideoProcessor
- Service stubs raise NotImplementedError so routes don't break during incremental build
- Static files for violation screenshots served at /violation_frames

**How to apply:** When continuing the build, pick up at Phase 2. Do not re-implement Phase 1 files unless fixing a bug.
