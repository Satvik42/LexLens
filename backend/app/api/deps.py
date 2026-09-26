"""Shared FastAPI dependencies: service container, database session, owned-document resolution."""

import logging
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.database import get_db
from app.db.models import Document, User
from app.schemas.document import ProcessingStatus
from app.security.auth import AuthenticatedUser, get_current_user
from app.services.analysis_service import AnalysisService
from app.services.comparison_service import ComparisonService
from app.services.document_processing_service import DocumentParser, DocumentProcessingService
from app.services.gemini_service import GeminiService, ModelUnavailableError, StructuredModel
from app.services.lawyer_service import LawyerService
from app.services.question_service import QuestionService
from app.services.storage_service import StorageService, build_storage_service

logger = logging.getLogger(__name__)


@dataclass
class ServiceContainer:
    storage: StorageService
    processing: DocumentProcessingService
    model: StructuredModel | None

    @property
    def analysis(self) -> AnalysisService:
        return AnalysisService(self.model)

    @property
    def questions(self) -> QuestionService:
        return QuestionService(self._require_model())

    @property
    def lawyer(self) -> LawyerService:
        return LawyerService(self.model)

    @property
    def comparison(self) -> ComparisonService:
        return ComparisonService(self._require_model())

    def _require_model(self) -> StructuredModel:
        if self.model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "AI_UNAVAILABLE", "message": "Document analysis is not configured on this server."},
            )
        return self.model


def build_services(settings: Settings) -> ServiceContainer:
    model: StructuredModel | None = None
    if settings.uses_gemini:
        try:
            model = GeminiService(settings)
        except ModelUnavailableError:
            logger.warning("Gemini could not be initialised; analysis endpoints will be unavailable")
    storage = build_storage_service(settings)
    processing = DocumentProcessingService(settings, storage, DocumentParser(settings), model)
    return ServiceContainer(storage=storage, processing=processing, model=model)


def get_services(request: Request) -> ServiceContainer:
    return request.app.state.services


def ensure_user(db: Session, identity: AuthenticatedUser) -> User:
    user = db.get(User, identity.id)
    if user is None:
        user = User(id=identity.id, email=identity.email)
        db.add(user)
        db.flush()
    elif identity.email and user.email != identity.email:
        user.email = identity.email
    return user


def _not_found() -> HTTPException:
    # Foreign documents are reported as missing so their existence is not disclosed.
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND", "message": "Document not found."})


def get_owned_document(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    """Authorization: the authenticated user must own the requested document."""
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user.id))
    if document is None:
        raise _not_found()
    return document


def get_ready_document(document: Document = Depends(get_owned_document)) -> Document:
    if document.processing_status != ProcessingStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DOCUMENT_NOT_READY", "message": "The document has not finished processing."},
        )
    return document


def load_owned_document(db: Session, user_id: str, document_id: str) -> Document:
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user_id))
    if document is None:
        raise _not_found()
    return document
