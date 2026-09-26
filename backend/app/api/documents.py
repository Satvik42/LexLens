"""Document upload, retrieval, processing status, pages and evidence lookup."""

import hashlib
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ServiceContainer, ensure_user, get_owned_document, get_ready_document, get_services
from app.config import Settings, get_settings
from app.db.database import SessionLocal, get_db
from app.db.models import Document, Evidence
from app.schemas.document import DocumentOut, DocumentPagesOut, DocumentStatusOut, ProcessingStatus
from app.schemas.evidence import EvidenceOut
from app.security.auth import AuthenticatedUser, get_current_user
from app.security.rate_limit import rate_limited
from app.security.validation import validate_upload
from app.services.document_processing_service import load_pages
from app.services.storage_service import build_storage_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _run_processing(services: ServiceContainer, document_id: str) -> None:
    """Background task with its own session; never raises into the request cycle."""
    db = SessionLocal()
    try:
        services.processing.process(db, document_id)
    finally:
        db.close()


async def _read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    """Read at most max_bytes + 1 so oversized uploads are rejected without buffering the whole stream."""
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(1024 * 256):
        total += len(chunk)
        if total > max_bytes:
            return b"".join(chunks) + chunk  # validator reports FILE_TOO_LARGE
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(rate_limited("upload")),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    services: ServiceContainer = Depends(get_services),
) -> Document:
    content = await _read_limited(file, settings.max_upload_bytes)
    validated = validate_upload(file.filename, file.content_type, content, settings.max_upload_bytes)
    owner = ensure_user(db, user)
    content_hash = hashlib.sha256(validated.content).hexdigest()

    existing = db.scalar(
        select(Document).where(
            Document.user_id == owner.id,
            Document.content_hash == content_hash,
            Document.processing_status == ProcessingStatus.READY,
        )
    )
    if existing is not None:
        db.commit()
        return existing  # identical document already processed: reuse instead of re-parsing

    storage_key = build_storage_key(owner.id, validated.extension)
    services.storage.upload(storage_key, validated.content, validated.mime_type)
    document = Document(
        user_id=owner.id,
        filename=validated.filename,
        mime_type=validated.mime_type,
        size_bytes=len(validated.content),
        content_hash=content_hash,
        storage_key=storage_key,
        processing_status=ProcessingStatus.UPLOADED,
    )
    db.add(document)
    db.commit()
    background.add_task(_run_processing, services, document.id)
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Document]:
    return list(db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())))


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document: Document = Depends(get_owned_document)) -> Document:
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document: Document = Depends(get_owned_document),
    db: Session = Depends(get_db),
    services: ServiceContainer = Depends(get_services),
) -> None:
    services.storage.delete(document.storage_key)
    db.delete(document)
    db.commit()


@router.post("/{document_id}/process", response_model=DocumentStatusOut, status_code=status.HTTP_202_ACCEPTED)
def reprocess_document(
    background: BackgroundTasks,
    document: Document = Depends(get_owned_document),
    _: AuthenticatedUser = Depends(rate_limited("process")),
    services: ServiceContainer = Depends(get_services),
) -> DocumentStatusOut:
    if document.processing_status == ProcessingStatus.PROCESSING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "ALREADY_PROCESSING", "message": "Processing is already in progress."})
    background.add_task(_run_processing, services, document.id)
    return DocumentStatusOut(
        id=document.id,
        processing_status=ProcessingStatus.PROCESSING,
        processing_error=None,
        page_count=document.page_count,
        document_type=document.document_type,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusOut)
def document_status(document: Document = Depends(get_owned_document)) -> DocumentStatusOut:
    return DocumentStatusOut(
        id=document.id,
        processing_status=document.processing_status,
        processing_error=document.processing_error,
        page_count=document.page_count,
        document_type=document.document_type,
    )


@router.get("/{document_id}/pages", response_model=DocumentPagesOut)
def document_pages(document: Document = Depends(get_ready_document)) -> DocumentPagesOut:
    pages = load_pages(document)
    return DocumentPagesOut(document_id=document.id, page_count=len(pages), pages=pages)


@router.get("/{document_id}/evidence/{evidence_id}", response_model=EvidenceOut)
def get_evidence(evidence_id: str, document: Document = Depends(get_owned_document), db: Session = Depends(get_db)) -> Evidence:
    evidence = db.scalar(select(Evidence).where(Evidence.id == evidence_id, Evidence.document_id == document.id))
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND", "message": "Evidence not found."})
    return evidence
