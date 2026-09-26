"""Structured analysis operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ServiceContainer, get_ready_document, get_services
from app.db.database import get_db
from app.db.models import Document
from app.domain.operations import ANALYSIS_OPERATIONS, OPERATIONS, Operation
from app.schemas.analysis import AnalysisResult, AnalyzeRequest
from app.schemas.document import DocumentType
from app.security.auth import AuthenticatedUser
from app.security.rate_limit import rate_limited
from app.services.gemini_service import ModelOutputError, ModelUnavailableError

router = APIRouter(prefix="/api", tags=["analysis"])


def _parse_operation(raw: str) -> Operation:
    try:
        operation = Operation(raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_OPERATION", "message": "Unknown operation."}) from exc
    if operation not in ANALYSIS_OPERATIONS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_OPERATION", "message": "This operation has a dedicated endpoint."})
    return operation


def model_error_response(exc: Exception) -> HTTPException:
    if isinstance(exc, ModelUnavailableError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "AI_UNAVAILABLE", "message": "Analysis is taking longer than expected. Try again."})
    if isinstance(exc, ModelOutputError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail={"code": "AI_OUTPUT_INVALID", "message": "We couldn't produce a verified result for this document. Try again."})
    raise exc


@router.post("/documents/{document_id}/analyze", response_model=AnalysisResult)
def analyze_document(
    payload: AnalyzeRequest,
    document: Document = Depends(get_ready_document),
    _: AuthenticatedUser = Depends(rate_limited("analyze")),
    db: Session = Depends(get_db),
    services: ServiceContainer = Depends(get_services),
) -> AnalysisResult:
    operation = _parse_operation(payload.operation)
    try:
        return services.analysis.analyze(db, document, operation, force=payload.force)
    except (ModelUnavailableError, ModelOutputError) as exc:
        raise model_error_response(exc) from exc


@router.get("/documents/{document_id}/analyses", response_model=list[AnalysisResult])
def list_analyses(document: Document = Depends(get_ready_document), db: Session = Depends(get_db), services: ServiceContainer = Depends(get_services)) -> list[AnalysisResult]:
    """Cached results only; never triggers model calls."""
    results = [services.analysis.get_cached(db, document, operation) for operation in ANALYSIS_OPERATIONS]
    return [result for result in results if result is not None]


@router.get("/operations")
def list_operations() -> list[dict]:
    """Operation catalogue with document-type-specific focus wording for the intent cards."""
    return [
        {
            "key": spec.key.value,
            "label": spec.label,
            "description": spec.description,
            "type_focus": {doc_type.value: text for doc_type, text in spec.type_focus.items()},
        }
        for spec in OPERATIONS.values()
    ]


@router.get("/document-types")
def list_document_types() -> list[str]:
    return [doc_type.value for doc_type in DocumentType]
