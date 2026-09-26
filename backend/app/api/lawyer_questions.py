"""Prepare for a Lawyer."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.analysis import model_error_response
from app.api.deps import ServiceContainer, get_ready_document, get_services
from app.db.database import get_db
from app.db.models import Document
from app.schemas.analysis import LawyerQuestions, LawyerQuestionsRequest
from app.security.auth import AuthenticatedUser
from app.security.rate_limit import rate_limited
from app.services.gemini_service import ModelOutputError, ModelUnavailableError

router = APIRouter(prefix="/api/documents", tags=["lawyer"])


@router.post("/{document_id}/lawyer-questions", response_model=LawyerQuestions)
def lawyer_questions(
    payload: LawyerQuestionsRequest,
    document: Document = Depends(get_ready_document),
    _: AuthenticatedUser = Depends(rate_limited("lawyer")),
    db: Session = Depends(get_db),
    services: ServiceContainer = Depends(get_services),
) -> LawyerQuestions:
    try:
        return services.lawyer.prepare(db, document, force=payload.force)
    except (ModelUnavailableError, ModelOutputError) as exc:
        raise model_error_response(exc) from exc
