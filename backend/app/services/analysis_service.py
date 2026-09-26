"""Runs structured analysis operations with caching, evidence validation and one repair retry."""

import logging
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisResult as AnalysisResultRow
from app.db.models import Document, new_id
from app.domain.operations import ANALYSIS_OPERATIONS, Operation, get_spec
from app.prompts.analysis import build_analysis_prompt, repair_feedback
from app.schemas.analysis import AnalysisResult, ConcernsOutput, FindingsOutput
from app.services.context_service import build_operation_context
from app.services.evidence_repository import persist_evidence
from app.services.evidence_service import EvidenceValidator
from app.services.gemini_service import StructuredModel
from app.services.result_assembly import assemble_analysis, iter_analysis_evidence

logger = logging.getLogger(__name__)

TOutput = TypeVar("TOutput", bound=BaseModel)


class UnsupportedOperationError(ValueError):
    pass


def generate_with_repair(
    model: StructuredModel,
    schema: type[TOutput],
    build_prompt: Callable[[str | None], str],
    make_validator: Callable[[], EvidenceValidator],
    convert: Callable[[TOutput, EvidenceValidator], object],
    *,
    conversational: bool = False,
) -> tuple[object, EvidenceValidator]:
    """Generate, validate evidence, and retry once with feedback when quotes could not be located."""
    output = model.generate(build_prompt(None), schema, conversational=conversational)
    validator = make_validator()
    result = convert(output, validator)
    failed = validator.report.failed_quotes
    if not failed:
        return result, validator

    logger.info("%s evidence quote(s) unverified; retrying with repair feedback", len(failed))
    retry_output = model.generate(build_prompt(repair_feedback(failed)), schema, conversational=conversational)
    retry_validator = make_validator()
    retry_result = convert(retry_output, retry_validator)
    if len(retry_validator.report.failed_quotes) < len(failed):
        return retry_result, retry_validator
    return result, validator


class AnalysisService:
    def __init__(self, model: StructuredModel) -> None:
        self._model = model

    def get_cached(self, db: Session, document: Document, operation: Operation) -> AnalysisResult | None:
        row = db.scalar(
            select(AnalysisResultRow).where(
                AnalysisResultRow.document_id == document.id, AnalysisResultRow.operation == operation.value
            )
        )
        if row is None:
            return None
        return AnalysisResult.model_validate({**row.result_json, "cached": True, "created_at": row.created_at})

    def analyze(self, db: Session, document: Document, operation: Operation, *, force: bool = False) -> AnalysisResult:
        if operation not in ANALYSIS_OPERATIONS:
            raise UnsupportedOperationError(f"{operation} is not a structured analysis operation")
        if not force:
            cached = self.get_cached(db, document, operation)
            if cached is not None:
                return cached

        spec = get_spec(operation)
        context = build_operation_context(document, operation)
        schema = ConcernsOutput if operation == Operation.CONCERNS else FindingsOutput
        result_id = new_id()

        result, validator = generate_with_repair(
            self._model,
            schema,
            build_prompt=lambda feedback: build_analysis_prompt(spec, context.document_type, context.prompt_block, feedback),
            make_validator=lambda: EvidenceValidator(context.pages),
            convert=lambda output, v: assemble_analysis(
                output, v, result_id=result_id, document_id=document.id, operation=operation.value, title=spec.label
            ),
        )
        assert isinstance(result, AnalysisResult)
        self._store(db, document, operation, result)
        return result

    @staticmethod
    def _store(db: Session, document: Document, operation: Operation, result: AnalysisResult) -> None:
        existing = db.scalar(
            select(AnalysisResultRow).where(
                AnalysisResultRow.document_id == document.id, AnalysisResultRow.operation == operation.value
            )
        )
        if existing is not None:
            db.delete(existing)
            db.flush()
        row = AnalysisResultRow(id=result.id, document_id=document.id, operation=operation.value, status=result.status, result_json={})
        db.add(row)
        db.flush()
        persist_evidence(db, document.id, list(iter_analysis_evidence(result)), analysis_result_id=row.id)
        row.result_json = result.model_dump(mode="json", exclude={"cached", "created_at"})
        db.commit()
        result.created_at = row.created_at
