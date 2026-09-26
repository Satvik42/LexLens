"""'Prepare for a Lawyer': generates professional questions grounded in the document and prior analysis."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisResult as AnalysisResultRow
from app.db.models import Conversation, Document, Message, new_id
from app.domain.operations import Operation, get_spec
from app.prompts.lawyer import build_lawyer_prompt
from app.schemas.analysis import LawyerOutput, LawyerQuestion, LawyerQuestionOutput, LawyerQuestions
from app.schemas.document import Clause, DocumentType, NormalizedPage
from app.schemas.evidence import EvidenceQuote
from app.services.analysis_service import generate_with_repair
from app.services.context_service import build_operation_context
from app.services.evidence_repository import persist_evidence
from app.services.evidence_service import EvidenceValidator
from app.services.gemini_service import ModelOutputError, ModelUnavailableError, StructuredModel
from app.services.retrieval_service import select_clauses
from app.services.segmentation_service import build_clauses

logger = logging.getLogger(__name__)

_MAX_NOTES = 12
_MIN_FALLBACK = 5
_MAX_QUESTIONS = 8
_MIN_QUOTE = 8

_TOPIC_QUESTIONS: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("notice",), "Which notice period applies if I resign or the company ends the agreement?", "The document mentions notice, and more than one duration can appear."),
    (("training", "repay", "bond"), "What happens if I leave while a training-cost repayment still applies?", "A training-cost or repayment clause should be reviewed with a professional."),
    (("compete", "restrict"), "How long do post-employment restrictions last, and what work do they block?", "Restrictions after leaving are a common point to confirm."),
    (("confidential",), "What am I still not allowed to share after I leave?", "Confidentiality often continues after the agreement ends."),
    (("probation",), "What changes after probation, and can the company extend it?", "Probation terms affect notice and confirmation."),
    (("bonus", "incentive"), "Is any bonus guaranteed, and what happens if I am under notice on the payment date?", "Discretionary bonus language is worth confirming."),
    (("terminate", "termination"), "In which situations can the company end the agreement without notice?", "Immediate-termination clauses should be reviewed."),
)


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


def _clause_quote(clause: Clause) -> str | None:
    compact = " ".join(clause.text.split())
    if len(compact) < _MIN_QUOTE:
        return None
    if len(compact) <= 220:
        return compact
    return compact[:220].rsplit(" ", 1)[0]


def _evidence_for_clause(clause: Clause | None) -> list[EvidenceQuote]:
    if clause is None:
        return []
    quote = _clause_quote(clause)
    if not quote:
        return []
    return [EvidenceQuote(page=clause.page_number, section=clause.section, text=quote)]


def _question_from_note(note: str) -> LawyerQuestionOutput | None:
    lowered = note.lower()
    if "inconsistency" in lowered:
        topic = note.split("about", 1)[-1].split(":", 1)[0].strip() if "about" in lowered else "these clauses"
        return LawyerQuestionOutput(
            text=f"Which provision governs {topic} if the document states more than one version?",
            reason=note,
            evidence=[],
        )
    if lowered.startswith("not found"):
        label = note.split(":", 1)[-1].strip()
        return LawyerQuestionOutput(
            text=f"The document does not mention {label}. What should I confirm in writing before I sign?",
            reason=note,
            evidence=[],
        )
    if note.endswith("?"):
        return LawyerQuestionOutput(text=note, reason="Raised by earlier document analysis.", evidence=[])
    if ":" in note:
        title = note.split(":", 1)[-1].strip()
        return LawyerQuestionOutput(
            text=f"Can you review {title} and tell me what I should clarify?",
            reason=note,
            evidence=[],
        )
    return None


def build_fallback_questions(document: Document, pages: list[NormalizedPage], notes: list[str]) -> LawyerQuestions:
    """Build specific, document-grounded questions when Gemini cannot answer."""
    document_type = DocumentType(document.document_type)
    clauses = select_clauses(build_clauses(pages), list(get_spec(Operation.LAWYER_PREP).keywords_for(document_type)), 22_000)
    haystack = " ".join(clause.text.lower() for clause in clauses)
    drafted: list[LawyerQuestionOutput] = []
    for note in notes:
        question = _question_from_note(note)
        if question is not None:
            drafted.append(question)
    for keys, text, reason in _TOPIC_QUESTIONS:
        if not any(key in haystack for key in keys):
            continue
        match = next((clause for clause in clauses if any(key in clause.text.lower() for key in keys)), None)
        drafted.append(LawyerQuestionOutput(text=text, reason=reason, evidence=_evidence_for_clause(match)))
    if not any(token in haystack for token in ("stock", "equity", "option", "esop")):
        drafted.append(
            LawyerQuestionOutput(
                text="The document does not appear to mention stock options or equity. What should I confirm in writing before I sign?",
                reason="Equity treatment is often in a separate grant and is easy to miss.",
                evidence=[],
            )
        )
    for clause in clauses:
        if len(drafted) >= _MAX_QUESTIONS:
            break
        heading = clause.heading or (f"section {clause.section}" if clause.section else None)
        if not heading:
            continue
        drafted.append(
            LawyerQuestionOutput(
                text=f"How does {heading} apply in my situation?",
                reason=f"The document includes {heading}, which is worth confirming with a professional.",
                evidence=_evidence_for_clause(clause),
            )
        )
    unique: list[LawyerQuestionOutput] = []
    seen: set[str] = set()
    for question in drafted:
        key = question.text.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(question)
        if len(unique) >= _MAX_QUESTIONS:
            break
    if len(unique) < _MIN_FALLBACK:
        for clause in clauses:
            if len(unique) >= _MIN_FALLBACK:
                break
            quote = _clause_quote(clause)
            if not quote:
                continue
            text = f"Can you explain this clause and whether it is usual for this kind of document: \"{quote[:80]}\"?"
            if text.casefold() in seen:
                continue
            unique.append(LawyerQuestionOutput(text=text, reason="Taken from a clause in this document.", evidence=_evidence_for_clause(clause)))
    return _convert(LawyerOutput(questions=unique), EvidenceValidator(pages), document_id=document.id)


def _convert(output: LawyerOutput, validator: EvidenceValidator, *, document_id: str) -> LawyerQuestions:
    questions = [
        LawyerQuestion(id=f"q{index}", text=q.text.strip(), reason=q.reason.strip() or None, evidence=validator.validate_all(q.evidence))
        for index, q in enumerate(output.questions, start=1)
        if q.text.strip()
    ]
    return LawyerQuestions(document_id=document_id, questions=questions[:10])


class LawyerService:
    def __init__(self, model: StructuredModel | None) -> None:
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
        try:
            if self._model is None:
                raise ModelUnavailableError("Gemini is not configured")
            result, _ = generate_with_repair(
                self._model,
                LawyerOutput,
                build_prompt=lambda feedback: build_lawyer_prompt(context.prompt_block, notes) + (f"\n\n{feedback}" if feedback else ""),
                make_validator=lambda: EvidenceValidator(context.pages),
                convert=lambda output, v: _convert(output, v, document_id=document.id),
            )
        except (ModelUnavailableError, ModelOutputError):
            logger.warning("Gemini unavailable for lawyer prep; using document-grounded fallback")
            result = build_fallback_questions(document, context.pages, notes)
        assert isinstance(result, LawyerQuestions)
        if not result.questions:
            result = build_fallback_questions(document, context.pages, notes)
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
