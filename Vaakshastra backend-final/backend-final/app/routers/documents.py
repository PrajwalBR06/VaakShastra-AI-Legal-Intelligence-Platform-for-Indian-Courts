"""
Document upload and management routes.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import User, Document
from app.schemas import DocumentResponse, DocumentListResponse
from app.services.auth import get_current_user
from app.services.storage import storage_service
from app.services.pdf_extractor import pdf_extractor
from app.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_types = ["application/pdf", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: PDF, TXT")

    file_content = await file.read()

    if len(file_content) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max: {settings.max_file_size_mb}MB")

    document_id = uuid.uuid4().hex

    storage_path = await storage_service.upload_file(
        file_content=file_content,
        user_id=str(current_user.id),
        document_id=document_id,
        filename=file.filename or "document.pdf",
        content_type=file.content_type,
    )

    extracted_text = ""
    page_count = None
    extraction_method = "manual"

    if file.content_type == "application/pdf":
        extracted_text, page_count, extraction_method = await pdf_extractor.extract_text(file_content)
    elif file.content_type == "text/plain":
        extracted_text = file_content.decode("utf-8", errors="replace")
        extraction_method = "plaintext"

    word_count = pdf_extractor.count_words(extracted_text)

    document = Document(
        id=document_id,
        user_id=current_user.id,
        original_filename=file.filename or "document.pdf",
        file_size_bytes=len(file_content),
        mime_type=file.content_type,
        page_count=page_count,
        word_count=word_count,
        storage_backend="local",
        storage_path=storage_path,
        extracted_text=extracted_text,
        extraction_method=extraction_method,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * per_page
    count_query = select(func.count()).select_from(Document).where(
        Document.user_id == current_user.id, Document.is_deleted == 0
    )
    total = (await db.execute(count_query)).scalar()

    query = (
        select(Document)
        .where(Document.user_id == current_user.id, Document.is_deleted == 0)
        .order_by(Document.created_at.desc())
        .offset(offset).limit(per_page)
    )
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(documents=documents, total=total, page=page, per_page=per_page)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id, Document.is_deleted == 0)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document.is_deleted = True
    await db.commit()
