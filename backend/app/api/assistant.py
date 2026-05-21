from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/assistant", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    message: str
    video_id: Optional[int] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # TODO: route through LangGraph agent:
    #   - if video_id provided: query DB for incidents/summary
    #   - if policy question: use RAG over uploaded documents
    #   - compose response without hallucinating DB data
    return ChatResponse(
        reply="AI assistant is not yet configured. Please set LLM_API_KEY in your .env file.",
        session_id=req.session_id,
    )
