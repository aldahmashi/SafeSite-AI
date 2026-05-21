from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.database import init_db
from app.api import videos, streams, incidents, reports, policies, assistant


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    init_db()
    yield


app = FastAPI(
    title="SafeSite AI",
    description="Real-Time Construction Safety Monitoring Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve violation frame screenshots as static files
_vf_dir = Path(settings.violation_frames_dir)
_vf_dir.mkdir(parents=True, exist_ok=True)
app.mount("/violation_frames", StaticFiles(directory=str(_vf_dir)), name="violation_frames")

# Register routers
app.include_router(videos.router)
app.include_router(streams.router)
app.include_router(incidents.router)
app.include_router(reports.router)
app.include_router(policies.router)
app.include_router(assistant.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "safesite-ai-backend",
        "version": "0.1.0",
        "environment": settings.app_env,
    }
