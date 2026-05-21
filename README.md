# SafeSite AI — Real-Time Construction Safety Monitoring Platform

> An end-to-end AI system for detecting PPE violations, tracking workers, and generating compliance reports from construction-site videos and live CCTV streams.

---

## Problem Statement

Construction sites are among the most dangerous workplaces globally. Manual PPE audits are infrequent, inconsistent, and unable to catch real-time violations. SafeSite AI automates safety monitoring at scale — detecting the absence of helmets, safety vests, and other PPE, tracking individual workers across a session, calculating safety scores, and generating AI-powered supervisor reports.

---

## Features

- **PPE Detection** — Helmet, no-helmet, safety vest, no-vest, person, machinery (via YOLOv8/YOLO11)
- **Worker Tracking** — Persistent worker IDs across frames using ByteTrack
- **Violation Engine** — Rule-based logic with per-worker cooldown windows to avoid duplicate alerts
- **Unsafe Zone Detection** — Polygon-based restricted zones with elevated risk scoring
- **Safety Scoring** — Session-level score from 0–100 weighted by violation severity
- **Annotated Video Export** — Full video with bounding boxes and violation labels burned in
- **Violation Screenshots** — Auto-saved frame crops at each incident
- **Dashboard** — React/Next.js UI with upload, live stream, analytics, incidents, and reports pages
- **AI Safety Reports** — Auto-generated PDF reports with statistics, screenshots, and recommendations
- **RAG Policy Assistant** — Ask questions against uploaded safety policy PDFs using LangChain + ChromaDB
- **Real-Time Alerts** — Telegram notifications on high-risk violations
- **Live CCTV / RTSP Support** — OpenCV-based stream reader with real-time detection loop

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│  Dashboard · Upload · Live Stream · Incidents · Reports · Chat  │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────────┐
│                    Backend (FastAPI)                            │
│                                                                 │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐ │
│  │VideoProcessor│  │StreamProcessor│  │  AI Assistant        │ │
│  │(OpenCV+YOLO) │  │ (RTSP loop)   │  │  (LangGraph + RAG)   │ │
│  └──────┬───────┘  └───────┬───────┘  └──────────┬───────────┘ │
│         │                  │                      │             │
│  ┌──────▼──────────────────▼──────┐  ┌────────────▼──────────┐ │
│  │   Violation Engine + Tracker   │  │  ChromaDB (policies)  │ │
│  │   (ByteTrack + rule engine)    │  └───────────────────────┘ │
│  └──────────────────┬─────────────┘                            │
│                     │                                           │
│  ┌──────────────────▼─────────────┐  ┌───────────────────────┐ │
│  │     PostgreSQL Database        │  │  ReportLab PDF Engine  │ │
│  │  videos · workers · incidents  │  └───────────────────────┘ │
│  └────────────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                         │ Alerts
              ┌──────────▼──────────┐
              │   Telegram Bot API   │
              └─────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Computer Vision | YOLOv8/YOLO11, OpenCV, Ultralytics |
| Tracking | ByteTrack (via Ultralytics) |
| Database | PostgreSQL 15, SQLAlchemy 2, Alembic |
| AI / LLM | LangChain, LangGraph, OpenAI/Groq API |
| Vector DB | ChromaDB |
| PDF Reports | ReportLab |
| Frontend | Next.js 14, Tailwind CSS, Recharts |
| Alerts | Telegram Bot API |
| Infra | Docker, docker-compose |
| Deployment | Render (backend), Vercel (frontend), Supabase (DB) |

---

## Dataset

The model is trained on public PPE/construction-safety datasets in YOLO format:

- [Construction Site Safety (Roboflow)](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety)
- [Kaggle PPE Dataset](https://www.kaggle.com/datasets/snehilsanyal/construction-site-safety-image-dataset-roboflow)
- [SH17 PPE Dataset](https://github.com/erfanMhi/SH17-Dataset)

See [docs/dataset.md](docs/dataset.md) for download and preparation instructions.

---

## Installation

### Prerequisites

- Docker + Docker Compose
- Python 3.11+ (for local dev without Docker)
- Node.js 18+ (for frontend dev)

### 1. Clone and configure

```bash
git clone https://github.com/your-username/safesite-ai.git
cd safesite-ai
cp .env.example .env
# Edit .env with your database URL and API keys
```

### 2. Start with Docker Compose

```bash
# Start PostgreSQL + Backend
docker-compose up --build

# Backend will be live at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 3. Run backend locally (without Docker)

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Run frontend

```bash
cd frontend
npm install
npm run dev
# Frontend at http://localhost:3000
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `YOLO_WEIGHTS_PATH` | Path to trained `.pt` weights |
| `UPLOAD_DIR` | Where uploaded videos are stored |
| `OUTPUT_DIR` | Where annotated videos are saved |
| `VIOLATION_FRAMES_DIR` | Where violation screenshots are saved |
| `REPORTS_DIR` | Where PDF reports are saved |
| `LLM_API_KEY` | OpenAI / Groq API key |
| `LLM_MODEL` | Model name, e.g. `gpt-4o-mini` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for alerts |
| `TELEGRAM_CHAT_ID` | Target chat ID for alerts |

---

## Model Training

```bash
# 1. Download and prepare dataset (see docs/dataset.md)
# 2. Train
python training/train_yolo.py \
  --model yolov8n.pt \
  --data training/dataset.yaml \
  --epochs 100 \
  --imgsz 640 \
  --device 0

# 3. Copy best weights to backend
cp runs/train/ppe_detector/weights/best.pt backend/weights/best.pt
```

See [docs/model_training.md](docs/model_training.md) for GPU setup and evaluation metrics.

---

## Processing a Video

```bash
# Via API (after starting backend)
curl -X POST http://localhost:8000/api/videos/upload \
  -F "file=@/path/to/site_footage.mp4"

# Standalone test (no backend needed)
python training/inference_video.py \
  --source /path/to/video.mp4 \
  --weights backend/weights/best.pt
```

---

## Live CCTV / RTSP Mode

```bash
# Start a stream session via API
curl -X POST http://localhost:8000/api/streams/start \
  -H "Content-Type: application/json" \
  -d '{"url": "rtsp://your-camera-ip/stream", "name": "Gate Camera"}'

# For local webcam testing use url = "0"
```

---

## API Documentation

Interactive Swagger docs available at `http://localhost:8000/docs` when the backend is running.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/videos/upload` | Upload a video for processing |
| GET | `/api/videos/{id}/summary` | Full analysis summary |
| POST | `/api/streams/start` | Start a live CCTV stream |
| GET | `/api/incidents/high-risk` | All high/critical incidents |
| POST | `/api/reports/generate/{video_id}` | Generate PDF report |
| POST | `/api/policies/upload` | Upload safety policy PDF |
| POST | `/api/assistant/chat` | Ask the AI assistant |

Full API reference: [docs/api.md](docs/api.md)

---

## Screenshots

_Coming after Phase 2 (YOLO integration) and Phase 3 (frontend)._

---

## Demo Video

_Coming after Phase 3._

---

## Results / Metrics

| Metric | Value |
|---|---|
| Model mAP@50 | _TBD after training_ |
| Helmet detection precision | _TBD_ |
| Vest detection precision | _TBD_ |
| Processing speed (CPU) | _TBD_ |
| Processing speed (GPU) | _TBD_ |

---

## Limitations

- GPU required for real-time processing at 25+ FPS on HD video
- Worker re-identification across camera views not yet supported
- Occlusion handling is limited to YOLO confidence thresholds
- RAG assistant requires OpenAI/Groq API key

---

## Future Improvements

- [ ] Fall detection using pose estimation (YOLOv8-Pose)
- [ ] Multi-camera synchronization
- [ ] Edge deployment with ONNX / TensorRT
- [ ] NVIDIA DeepStream integration
- [ ] Automated shift reports via cron
- [ ] WhatsApp alert channel
- [ ] Mobile app for supervisors

---

## Portfolio / CV Bullets

- Built an end-to-end real-time computer vision safety platform using YOLOv8 and ByteTrack, achieving PPE detection across multi-worker construction site footage
- Designed a modular FastAPI microservice architecture with PostgreSQL, async background processing, and REST endpoints consumed by a Next.js dashboard
- Implemented a RAG-based AI assistant using LangChain + ChromaDB to answer safety compliance queries from uploaded policy documents
- Integrated LangGraph agentic workflow for structured AI report generation with real database retrieval — zero hallucinated incident data
- Containerized the full stack with Docker Compose; deployed backend to Render, frontend to Vercel, database to Supabase

---

## License

MIT — see [LICENSE](LICENSE)
