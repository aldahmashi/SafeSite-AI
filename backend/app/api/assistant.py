"""
AI Safety Assistant endpoint.

Uses LangChain + OpenAI (gpt-4o-mini by default) to answer questions
about PPE violations, compliance trends, and safety incidents.

If LLM_API_KEY is not configured, returns a helpful placeholder message.

Context passed to the LLM on every request:
  - Overall stats (videos, incidents, risk distribution)
  - Optional: per-video summary when video_id is provided
  - Recent 10 incidents (violation type + risk level)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assistant", tags=["AI Assistant"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    video_id: Optional[int] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None


# ── DB context builder ─────────────────────────────────────────────────────────

def _build_context(db: Session, video_id: Optional[int]) -> str:
    from app.models.incident import Incident, RiskLevel
    from app.models.video import Video, VideoStatus

    lines: list[str] = []

    # Overall stats
    total_videos    = db.query(Video).filter(Video.status == VideoStatus.completed).count()
    total_incidents = db.query(Incident).count()
    high_risk       = db.query(Incident).filter(
        Incident.risk_level.in_([RiskLevel.high, RiskLevel.critical])
    ).count()
    lines.append(
        f"Platform summary: {total_videos} completed videos, "
        f"{total_incidents} total incidents, {high_risk} high/critical risk incidents."
    )

    # Per-video context
    if video_id:
        video = db.get(Video, video_id)
        if video:
            inc = db.query(Incident).filter(Incident.video_id == video_id).all()
            no_helmet = sum(1 for i in inc if i.violation_type.value == "NO_HELMET")
            no_vest   = sum(1 for i in inc if i.violation_type.value == "NO_VEST")
            lines.append(
                f"Active video '{video.filename}': {len(inc)} incidents "
                f"({no_helmet} no-helmet, {no_vest} no-vest), "
                f"safety score: {video.safety_score:.1f}/100."
                if video.safety_score is not None
                else f"Active video '{video.filename}': {len(inc)} incidents "
                     f"({no_helmet} no-helmet, {no_vest} no-vest), safety score: N/A."
            )

    # Recent incidents snapshot
    recent = (
        db.query(Incident)
        .order_by(Incident.created_at.desc())
        .limit(10)
        .all()
    )
    if recent:
        snippet = ", ".join(
            f"{i.violation_type.value} [{i.risk_level.value}]" for i in recent
        )
        lines.append(f"Recent incidents (newest first): {snippet}.")

    return "\n".join(lines)


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    if not settings.llm_api_key:
        return ChatResponse(
            reply=(
                "The AI Assistant is not yet configured.\n\n"
                "To enable it:\n"
                "1. Obtain an OpenAI API key at platform.openai.com\n"
                "2. Add `LLM_API_KEY=sk-...` to your `backend/.env` file\n"
                "3. Restart the backend\n\n"
                "Once configured, I can answer questions like:\n"
                "• \"What are the most common PPE violations?\"\n"
                "• \"Which workers have the most incidents?\"\n"
                "• \"Summarize the safety report for video 3\""
            ),
            session_id=req.session_id,
        )

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        context = _build_context(db, req.video_id)

        # Optionally augment with RAG context from uploaded policy documents
        from app.services.rag_service import rag_service
        policy_context = rag_service.query(req.message, n_results=3)

        system_prompt = (
            "You are SafeSite AI's safety assistant — an expert in construction site "
            "PPE compliance and worker safety. "
            "You help site managers understand violations, compliance trends, and risk. "
            "Be concise, professional, and actionable. "
            "When referencing numbers, cite them exactly from the provided data. "
            "Do not invent data you were not given.\n\n"
            f"Current system data:\n{context}"
        )
        if policy_context:
            system_prompt += (
                f"\n\nRelevant policy document excerpts:\n{policy_context}"
            )

        llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            temperature=0.3,
            max_tokens=512,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=req.message),
        ]

        response = await llm.ainvoke(messages)
        return ChatResponse(reply=response.content, session_id=req.session_id)

    except ImportError:
        return ChatResponse(
            reply=(
                "LangChain / OpenAI packages are not installed. "
                "Run `pip install langchain-openai` in the backend environment."
            ),
            session_id=req.session_id,
        )
    except Exception as exc:
        logger.warning("AI assistant error: %s", exc)
        return ChatResponse(
            reply=(
                f"The assistant encountered an error: {exc}\n"
                "Please verify your LLM_API_KEY and model settings."
            ),
            session_id=req.session_id,
        )
