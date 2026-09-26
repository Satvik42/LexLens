"""Evidence-backed comparison between two of the user's documents."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.analysis import model_error_response
from app.api.deps import ServiceContainer, get_services, load_owned_document
from app.db.database import get_db
from app.db.models import Comparison
from app.schemas.analysis import ComparisonRequest, ComparisonResult
from app.schemas.document import ProcessingStatus
from app.security.auth import AuthenticatedUser, get_current_user
from app.security.rate_limit import rate_limited
from app.services.gemini_service import ModelOutputError, ModelUnavailableError

router = APIRouter(prefix="/api/comparisons", tags=["comparisons"])


@router.post("", response_model=ComparisonResult, status_code=status.HTTP_201_CREATED)
def create_comparison(
    payload: ComparisonRequest,
    user: AuthenticatedUser = Depends(rate_limited("compare")),
    db: Session = Depends(get_db),
    services: ServiceContainer = Depends(get_services),
) -> ComparisonResult:
    if payload.original_document_id == payload.updated_document_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "SAME_DOCUMENT", "message": "Choose two different documents to compare."})
    original = load_owned_document(db, user.id, payload.original_document_id)
    updated = load_owned_document(db, user.id, payload.updated_document_id)
    for document in (original, updated):
        if document.processing_status != ProcessingStatus.READY:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "DOCUMENT_NOT_READY", "message": "Both documents must finish processing first."})
    try:
        return services.comparison.compare(db, user.id, original, updated)
    except (ModelUnavailableError, ModelOutputError) as exc:
        raise model_error_response(exc) from exc


@router.get("/{comparison_id}", response_model=ComparisonResult)
def get_comparison(comparison_id: str, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)) -> ComparisonResult:
    row = db.scalar(select(Comparison).where(Comparison.id == comparison_id, Comparison.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND", "message": "Comparison not found."})
    return ComparisonResult.model_validate({**row.result_json, "created_at": row.created_at})
