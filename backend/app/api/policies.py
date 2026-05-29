from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid

from app.database import get_db
from app.config import settings
from app.models.policy_document import PolicyDocument
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/policies", tags=["Policies"])


def _ingest_in_background(document_id: int, file_path: str) -> None:
    """Run RAG ingestion in a background task so upload returns immediately."""
    ok = rag_service.ingest_document(document_id, file_path)
    if not ok:
        import logging
        logging.getLogger(__name__).warning(
            "RAG ingestion skipped for document_id=%s (deps missing or error).",
            document_id,
        )


@router.post("/upload", status_code=201)
async def upload_policy(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    policy_dir = Path(settings.upload_dir) / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    save_path   = policy_dir / unique_name
    with save_path.open("wb") as dest:
        shutil.copyfileobj(file.file, dest)

    doc = PolicyDocument(
        filename=file.filename,
        file_path=str(save_path),
        vector_collection_name=settings.vector_collection_name,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Kick off embedding in background (non-blocking)
    background_tasks.add_task(_ingest_in_background, doc.id, str(save_path))

    return {
        "id":           doc.id,
        "filename":     doc.filename,
        "uploaded_at":  doc.uploaded_at,
        "status":       "ingestion_scheduled",
    }


@router.get("")
def list_policies(db: Session = Depends(get_db)):
    return db.query(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).all()


@router.delete("/{document_id}", status_code=204)
def delete_policy(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(PolicyDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()


@router.get("/rag/status")
def rag_status():
    """Return how many chunks are stored in ChromaDB."""
    count = rag_service.collection_count()
    return {"chunks_stored": count, "rag_available": count > 0}
