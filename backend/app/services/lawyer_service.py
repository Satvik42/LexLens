"""'Prepare for a Lawyer': generates professional questions grounded in the document and prior analysis."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisResult as AnalysisResultRow
from app.db.models import Conversation, Document, Message, new_id
from app.domain.operations import Operation
from app.prompts.lawyer import build_lawyer_prompt
from app.schemas.analysis import LawyerOutput, LawyerQuestion, LawyerQuestions
from app.services.analysis_service import generate_with_repair
from app.services.context_service import build_operation_context
from app.services.evidence_repository import persist_evidence
from app.services.evidence_service import EvidenceValidator
from app.services.gemini_service import StructuredModel

_MAX_NOTES = 12


def collect_prior_notes(db: Session, document: Document) -> list[str]:
    """Gaps, conflicts and concerns already found for this document feed better lawyer questions."""
    notes: list[str] = []
    rows = db.scalars(select(AnalysisResultRow).where(AnalysisResultRow.document_id == document.id)).all()
    for row in rows:
        payload = row.result_json
        for inconsistency in payload.get("inconsistencies", []):
            notes.append(f"Potential inconsistency about {inconsistency['topic']}: {inconsistency['description']}")
        for finding in payload.get("findings", []):
            if finding.get("status") == "NOT_FOUND":
                notes.append(f"Not found in document: {finding['label']}")
        for concern in payload.get("concerns", []):
            notes.append(f"{concern['kind'].replace('_', ' ').title()}: {concern['title']}")
        notes.extend(payload.get("professional_questions", []))
    messages = db.scalars(
        select(Message).join(Conversation, Message.conversation_id == Conversation.id).where(Conversation.document_id == document.id)
    ).all()
    for message in messages:
        if message.result_json:
            notes.extend(message.result_json.get("professional_questions", []))
    return list(dict.fromkeys(note for note in notes if note))[:_MAX_NOTES]


def _convert(output: LawyerOutput, validator: EvidenceValidator, *, document_id: str) -> LawyerQuestions:
    questions = [
        LawyerQuestion(id=f"q{index}", text=q.text.strip(), reason=q.reason.strip() or None, evidence=validator.validate_all(q.evidence))
        for index, q in enumerate(output.questions, start=1)
        if q.text.strip()
    ]
    return LawyerQuestions(document_id=document_id, questions=questions[:10])


class LawyerService:
    def __init__(self, model: StructuredModel) -> None:
        self._model = model

    def prepare(self, db: Session, document: Document, *, force: bool = False) -> LawyerQuestions:
        if not force:
            cached = db.scalar(
                select(AnalysisResultRow).where(
                    AnalysisResultRow.document_id == document.id, AnalysisResultRow.operation == Operation.LAWYER_PREP.value
                )
            )
            if cached is not None:
                return LawyerQuestions.model_validate(cached.result_json)

        context = build_operation_context(document, Operation.LAWYER_PREP)
        notes = collect_prior_notes(db, document)
        result, _ = generate_with_repair(
            self._model,
            LawyerOutput,
            build_prompt=lambda feedback: build_lawyer_prompt(context.prompt_block, notes) + (f"\n\n{feedback}" if feedback else ""),
            make_validator=lambda: EvidenceValidator(context.pages),
            convert=lambda output, v: _convert(output, v, document_id=document.id),
        )
        assert isinstance(result, LawyerQuestions)
        self._store(db, document, result)
        return result

    @staticmethod
    def _store(db: Session, document: Document, result: LawyerQuestions) -> None:
        existing = db.scalar(
            select(AnalysisResultRow).where(
                AnalysisResultRow.document_id == document.id, AnalysisResultRow.operation == Operation.LAWYER_PREP.value
            )
        )
        if existing is not None:
            db.delete(existing)
            db.flush()
        row = AnalysisResultRow(id=new_id(), document_id=document.id, operation=Operation.LAWYER_PREP.value, status="EXPLICITLY_STATED", result_json={})
        db.add(row)
        db.flush()
        persist_evidence(db, document.id, [e for q in result.questions for e in q.evidence], analysis_result_id=row.id)
        row.result_json = result.model_dump(mode="json")
        db.commit()
