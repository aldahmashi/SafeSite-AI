# CLAUDE.md — MASTER DEVELOPMENT INSTRUCTIONS FOR SAFESITE AI

# READ THIS FILE FIRST BEFORE MAKING ANY CHANGES

You are developing a production-style AI portfolio project called SafeSite AI.

This file contains:
- Project architecture
- Development rules
- Current implementation status
- Coding standards
- Future roadmap
- Strict implementation instructions
- Autonomy permissions

You MUST follow this file during development.

---

# PROJECT OVERVIEW

## Project Name
SafeSite AI

## Project Goal

SafeSite AI is a real-time AI-powered construction safety monitoring platform.

The system detects PPE (Personal Protective Equipment) violations from:
- Uploaded videos
- Live CCTV streams
- RTSP cameras
- Webcam feeds

The platform should:
- Detect workers
- Detect PPE compliance
- Track workers across frames
- Generate incidents
- Generate alerts
- Generate safety analytics
- Generate reports
- Provide AI-powered safety assistance later

The project must look:
- Production-grade
- Professional
- Portfolio-ready
- Recruiter/impressive
- Scalable

This project is intended for:
- AI engineer portfolio
- Computer vision portfolio
- Full-stack AI system showcase
- Internship/job applications

---

# IMPORTANT DEVELOPMENT PHILOSOPHY

## CRITICAL RULES

You are ALLOWED to:
- Refactor code
- Improve architecture
- Fix mistakes
- Improve scalability
- Rename poorly designed files/functions
- Add missing layers/utilities
- Improve API consistency
- Improve error handling
- Improve performance
- Improve frontend UX
- Improve backend architecture

You MUST:
- Preserve working functionality
- Keep the project modular
- Avoid breaking previous phases
- Explain major architectural modifications
- Maintain production-quality code
- Keep the project clean and scalable

You MUST NOT:
- Hardcode secrets
- Hardcode fake AI outputs
- Commit .env
- Commit datasets
- Commit node_modules
- Commit Python virtual environments
- Delete important architecture without reason
- Replace scalable architecture with hacks
- Create temporary messy code unless clearly marked

If you detect poor architecture:
- You may redesign it properly.
- You may improve the structure.
- You may split large files into modular services.
- You may improve maintainability.

---

# PROJECT PHASES

# PHASE 1 — FOUNDATION
STATUS: COMPLETED

Goals:
- Backend structure
- Database setup
- API structure
- Core services
- Docker support
- Initial schemas/models

Expected Structure:
backend/
frontend/
training/
docs/

---

# PHASE 2 — DETECTION PIPELINE
STATUS: COMPLETED OR IN PROGRESS

Goals:
- YOLO integration
- PPE detection
- Worker tracking
- Violation engine
- Video processor
- Annotation utilities

Required Features:
- Detect helmets
- Detect safety vests
- Detect persons/workers
- Assign worker IDs
- Generate incidents
- Generate screenshots
- Save annotated videos

Main files:
- detector.py
- tracker.py
- violation_engine.py
- video_processor.py

---

# PHASE 3 — FRONTEND DASHBOARD
STATUS: CURRENT PRIORITY

## GOAL

Build a professional frontend dashboard.

This dashboard should make the project visually impressive and easy to test.

The dashboard should look similar to:
- modern SaaS dashboards
- AI monitoring platforms
- enterprise analytics systems

## FRONTEND STACK

Required:
- Next.js preferred
- React acceptable
- Tailwind CSS
- Recharts
- Axios or Fetch API

## REQUIRED PAGES

### 1. Dashboard Home
Show:
- Total videos analyzed
- Total incidents
- High-risk incidents
- Average safety score
- Helmet compliance percentage
- Vest compliance percentage

Include:
- Charts
- Cards
- Recent incidents
- Modern UI

### 2. Upload Page
Features:
- Drag/drop upload
- Upload progress
- Video processing state
- Error handling
- Success handling

### 3. Videos Page
Features:
- List uploaded videos
- Search/filter
- Video status
- Safety score
- Created date

### 4. Video Details Page
Features:
- Video player
- Annotated output video
- Incident timeline
- Violation table
- Screenshots
- Safety analytics

### 5. Incidents Page
Features:
- Incident filtering
- Risk filtering
- Screenshot preview
- Worker ID
- Timestamp
- Violation type

### 6. Analytics Page
Features:
- Violation charts
- Risk distribution
- Compliance metrics
- Trends

### 7. Reports Page
Features:
- Reports table
- Download buttons
- PDF placeholders

### 8. AI Assistant Page
Current state:
- Placeholder only
- No AI logic yet

Display:
"AI Safety Assistant Coming Soon"

## FRONTEND RULES

You MUST:
- Use reusable components
- Use loading states
- Use empty states
- Use error states
- Avoid duplicated UI code
- Keep design modern
- Keep layout responsive
- Keep UI portfolio-grade

If API endpoints fail:
- DO NOT crash frontend
- Show graceful empty state

If backend endpoint is missing:
- Create placeholder integration
- Explain what backend endpoint is still needed

---

# PHASE 4 — LIVE CCTV / RTSP
STATUS: FUTURE

## GOAL

Allow live monitoring from:
- CCTV cameras
- RTSP streams
- Webcams

## REQUIRED FEATURES

### Stream Processor
- OpenCV VideoCapture
- Continuous frame processing
- YOLO inference
- Worker tracking
- Incident generation

### Stream APIs
Required:
- start stream
- stop stream
- stream status
- stream incidents

### Stream Types
Support:
- webcam index (0,1,2...)
- RTSP URLs

### PERFORMANCE GOALS
- modular architecture
- scalable design
- future GPU optimization support

---

# PHASE 5 — ALERT SYSTEM
STATUS: FUTURE

## TELEGRAM ALERTS

Requirements:
- Telegram bot integration
- HIGH/CRITICAL alerts only
- Cooldown logic
- Incident screenshot support later

Environment Variables:
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

## EMAIL ALERTS
Later phase.

---

# PHASE 6 — REPORT SYSTEM
STATUS: FUTURE

## GOAL

Generate:
- PDF reports
- Incident summaries
- Safety analytics reports

Report contents:
- Incident tables
- Screenshots
- Safety score
- Compliance percentages
- Recommendations

---

# PHASE 7 — AI ASSISTANT
STATUS: FUTURE

## GOAL

Implement:
- LangChain
- LangGraph
- AI safety assistant
- Incident Q&A
- Safety recommendations

Possible Features:
- "Summarize incidents from this week"
- "Which workers violate PPE most?"
- "Explain high-risk incidents"

DO NOT implement yet unless explicitly requested.

---

# PHASE 8 — RAG SAFETY POLICY SYSTEM
STATUS: FUTURE

## GOAL

Allow uploading safety PDFs.

Use:
- RAG
- Vector DB
- Embeddings
- PDF parsing

Features:
- Safety document Q&A
- Safety regulation retrieval
- AI safety explanations

DO NOT implement yet unless explicitly requested.

---

# PHASE 9 — DEPLOYMENT
STATUS: FUTURE

## GOAL

Deploy:
- frontend
- backend
- database

Potential Platforms:
- Vercel
- Render
- Railway
- Supabase

Also create:
- portfolio-ready README
- architecture diagrams
- demo assets

---

# TECH STACK

## Backend
- Python
- FastAPI
- OpenCV
- SQLAlchemy
- PostgreSQL
- Pydantic

## AI/ML
- YOLOv8 / YOLO11
- ByteTrack
- BoT-SORT

## Frontend
- Next.js
- React
- Tailwind CSS
- Recharts

## AI Later
- LangChain
- LangGraph
- RAG

---

# YOLO TRAINING INSTRUCTIONS

YOLO training may happen:
- locally
- Kaggle
- Google Colab

Datasets should NOT be committed.

Dataset path:
training/datasets/

Final trained model:
backend/weights/best.pt

If best.pt is missing:
- show clear backend error
- avoid crashing application

---

# BACKEND API REQUIREMENTS

## REQUIRED ENDPOINTS

### Health
GET /health

### Videos
POST /api/videos/upload
GET /api/videos
GET /api/videos/{video_id}

### Incidents
GET /api/incidents
GET /api/videos/{video_id}/incidents

### Streams
POST /api/streams/start
POST /api/streams/stop
GET /api/streams/{stream_id}/status

### Reports
POST /api/reports/generate/{video_id}

---

# DATABASE RULES

Use proper models for:
- videos
- incidents
- streams
- reports
- workers

Use:
- timestamps
- relationships
- indexes if useful

---

# FRONTEND ENVIRONMENT VARIABLES

Required:
NEXT_PUBLIC_API_URL=http://localhost:8000

---

# BACKEND ENVIRONMENT VARIABLES

DATABASE_URL=
SECRET_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

Never hardcode these values.

---

# ERROR HANDLING RULES

Backend:
- never crash entire app because of one failure
- log errors clearly
- return meaningful API errors

Frontend:
- show user-friendly errors
- avoid blank pages
- avoid crashing UI

---

# TESTING RULES

When implementing:
- explain how to test
- explain expected output
- explain missing dependencies if any

---

# DEVELOPMENT WORKFLOW

Workflow:
1. Edit files
2. Test locally
3. Fix errors
4. git add .
5. git commit
6. git push

---

# FINAL IMPORTANT INSTRUCTIONS

You should behave like a senior AI/full-stack engineer working on a real production startup product.

You are encouraged to:
- improve architecture
- fix weak implementations
- improve scalability
- improve maintainability
- improve readability
- improve UX

You should NOT:
- overengineer unnecessarily
- break previous functionality
- ignore modularity
- ignore production readiness

Always prioritize:
1. scalability
2. maintainability
3. modularity
4. production-style architecture
5. portfolio quality