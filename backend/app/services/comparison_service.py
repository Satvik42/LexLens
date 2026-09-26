"""Evidence-backed comparison of two documents owned by the same user."""

from sqlalchemy.orm import Session

from app.db.models import Comparison, Document, new_id
from app.domain.operations import Operation
from app.prompts.comparison import build_comparison_prompt
from app.schemas.analysis import ComparisonOutput, ComparisonResult, ComparisonRow
from app.schemas.evidence import EvidenceStatus
from app.services.context_service import build_operation_context
from app.services.evidence_repository import persist_evidence
from app.services.evidence_service import EvidenceValidator
from app.services.gemini_service import StructuredModel


class ComparisonService:
    def __init__(self, model: StructuredModel) -> None:
        self._model = model

    def compare(self, db: Session, user_id: str, original: Document, updated: Document) -> ComparisonResult:
        original_context = build_operation_context(original, Operation.COMPARE)
        updated_context = build_operation_context(updated, Operation.COMPARE)
        prompt = build_comparison_prompt(original_context.prompt_block, updated_context.prompt_block)
        output = self._model.generate(prompt, ComparisonOutput)

        original_validator = EvidenceValidator(original_context.pages)
        updated_validator = EvidenceValidator(updated_context.pages)
        rows = [
            ComparisonRow(
                id=f"r{index}",
                term=row.term.strip(),
                original_value=row.original_value.strip() if row.original_value else None,
                updated_value=row.updated_value.strip() if row.updated_value else None,
                change=row.change,
                note=row.note.strip() if row.note else None,
                original_evidence=original_validator.validate_all(row.original_evidence),
                updated_evidence=updated_validator.validate_all(row.updated_evidence),
            )
            for index, row in enumerate(output.rows, start=1)
        ]
        result = ComparisonResult(
            id=new_id(),
            original_document_id=original.id,
            updated_document_id=updated.id,
            original_filename=original.filename,
            updated_filename=updated.filename,
            status=EvidenceStatus.EXPLICITLY_STATED if rows else EvidenceStatus.NOT_FOUND,
            summary=output.summary.strip(),
            rows=rows,
            verification_notes=original_validator.report.notes + updated_validator.report.notes,
        )
        self._store(db, user_id, result)
        return result

    @staticmethod
    def _store(db: Session, user_id: str, result: ComparisonResult) -> None:
        persist_evidence(db, result.original_document_id, [e for r in result.rows for e in r.original_evidence])
        persist_evidence(db, result.updated_document_id, [e for r in result.rows for e in r.updated_evidence])
        row = Comparison(
            id=result.id,
            user_id=user_id,
            original_document_id=result.original_document_id,
            updated_document_id=result.updated_document_id,
            status=result.status,
            result_json=result.model_dump(mode="json", exclude={"created_at"}),
        )
        db.add(row)
        db.commit()
        result.created_at = row.created_at
