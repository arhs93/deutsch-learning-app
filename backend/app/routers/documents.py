import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Document, User
from app.tasks.process_document import process_document

router = APIRouter(tags=["documents"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".srt"}


@router.post("/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_type: str = Form(...),
    title: str = Form(...),
    user_id: str = Form(...),  # In production: extracted from JWT
    db: AsyncSession = Depends(get_db),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {suffix}. Allowed: {ALLOWED_EXTENSIONS}")

    doc_id = uuid.uuid4()
    dest = UPLOAD_DIR / f"{doc_id}{suffix}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        id=doc_id,
        user_id=uuid.UUID(user_id),
        title=title,
        source_type=source_type,
        storage_path=str(dest),
        processing_status="pending",
    )
    db.add(doc)
    await db.commit()

    background_tasks.add_task(process_document, doc_id, db)

    return {"document_id": str(doc_id), "status": "pending"}


@router.get("/documents")
async def list_documents(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document).where(Document.user_id == uuid.UUID(user_id)).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "source_type": d.source_type,
            "processing_status": d.processing_status,
            "word_count": d.word_count,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.get("/documents/{document_id}")
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return {
        "id": str(doc.id),
        "title": doc.title,
        "source_type": doc.source_type,
        "processing_status": doc.processing_status,
        "word_count": doc.word_count,
        "raw_text": doc.raw_text,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
    }


@router.get("/documents/{document_id}/status")
async def get_document_status(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return {"status": doc.processing_status}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    # Remove uploaded file
    Path(doc.storage_path).unlink(missing_ok=True)
    await db.delete(doc)
    await db.commit()
    return {"deleted": True}
