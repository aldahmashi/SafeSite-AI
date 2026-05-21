from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid

from app.database import get_db
from app.config import settings
from app.models.policy_document import PolicyDocument

router = APIRouter(prefix="/api/policies", tags=["Policies"])


@router.post("/upload", status_code=201)
async def upload_policy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    policy_dir = Path(settings.upload_dir) / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    save_path = policy_dir / unique_name
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

    # TODO: rag_service.ingest_document(doc.id, db)
    return {"id": doc.id, "filename": doc.filename, "uploaded_at": doc.uploaded_at}


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
