"""Document-grounded question answering with conversation persistence."""

from sqlalchemy.orm import Session

from app.db.models import Conversation, Document, Message, new_id
from app.prompts.qa import build_qa_prompt
from app.schemas.analysis import QaAnswer, QaOutput
from app.schemas.evidence import EvidenceStatus
from app.services.analysis_service import generate_with_repair
from app.services.context_service import build_question_context
from app.services.evidence_repository import persist_evidence
from app.services.evidence_service import EvidenceValidator, downgrade_status
from app.services.gemini_service import StructuredModel

NOT_FOUND_TITLE = "Cannot be determined from this document"


def _convert(output: QaOutput, validator: EvidenceValidator, *, question: str, document_id: str, conversation_id: str) -> QaAnswer:
    evidence = validator.validate_all(output.evidence)
    status, note = downgrade_status(output.status, bool(evidence), bool(output.evidence))
    answer = output.answer.strip() if output.answer else None
    title = output.title.strip() or "Answer"
    if status == EvidenceStatus.NOT_FOUND:
        title, answer = NOT_FOUND_TITLE, None
    return QaAnswer(
        id=new_id(),
        document_id=document_id,
        conversation_id=conversation_id,
        question=question,
        status=status,
        title=title,
        answer=answer,
        explanation=output.explanation.strip(),
        what_i_found=output.what_i_found.strip(),
        evidence=evidence,
        related_questions=[q.strip() for q in output.related_questions if q.strip()][:5],
        professional_questions=[q.strip() for q in output.professional_questions if q.strip()][:5],
        verification_notes=([note] if note else []) + validator.report.notes,
    )


class QuestionService:
    def __init__(self, model: StructuredModel) -> None:
        self._model = model

    def ask(self, db: Session, document: Document, user_id: str, question: str, conversation_id: str | None) -> QaAnswer:
        conversation = self._get_or_create_conversation(db, document, user_id, conversation_id)
        history = [(m.role, m.content) for m in conversation.messages]
        context = build_question_context(document, question)

        answer, _ = generate_with_repair(
            self._model,
            QaOutput,
            build_prompt=lambda feedback: build_qa_prompt(question, context.prompt_block, history) + (f"\n\n{feedback}" if feedback else ""),
            make_validator=lambda: EvidenceValidator(context.pages),
            convert=lambda output, v: _convert(output, v, question=question, document_id=document.id, conversation_id=conversation.id),
            conversational=True,
        )
        assert isinstance(answer, QaAnswer)
        persist_evidence(db, document.id, answer.evidence)

        db.add(Message(conversation_id=conversation.id, role="user", content=question))
        assistant = Message(
            id=answer.id,
            conversation_id=conversation.id,
            role="assistant",
            content=answer.answer or answer.title,
            result_json=answer.model_dump(mode="json", exclude={"created_at"}),
        )
        db.add(assistant)
        db.commit()
        answer.created_at = assistant.created_at
        return answer

    @staticmethod
    def _get_or_create_conversation(db: Session, document: Document, user_id: str, conversation_id: str | None) -> Conversation:
        if conversation_id:
            conversation = db.get(Conversation, conversation_id)
            if conversation and conversation.document_id == document.id and conversation.user_id == user_id:
                return conversation
        conversation = Conversation(document_id=document.id, user_id=user_id)
        db.add(conversation)
        db.flush()
        return conversation
