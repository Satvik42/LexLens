"""Document-grounded questions and conversation history."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.analysis import model_error_response
from app.api.deps import ServiceContainer, get_ready_document, get_owned_document, get_services
from app.db.database import get_db
from app.db.models import Conversation, Document
from app.schemas.analysis import ConversationOut, QaAnswer, QuestionRequest
from app.security.auth import AuthenticatedUser, get_current_user
from app.security.rate_limit import rate_limited
from app.services.gemini_service import ModelOutputError, ModelUnavailableError

router = APIRouter(prefix="/api/documents", tags=["questions"])


@router.post("/{document_id}/questions", response_model=QaAnswer)
def ask_question(
    payload: QuestionRequest,
    document: Document = Depends(get_ready_document),
    user: AuthenticatedUser = Depends(rate_limited("questions")),
    db: Session = Depends(get_db),
    services: ServiceContainer = Depends(get_services),
) -> QaAnswer:
    try:
        return services.questions.ask(db, document, user.id, payload.question.strip(), payload.conversation_id)
    except (ModelUnavailableError, ModelOutputError) as exc:
        raise model_error_response(exc) from exc


@router.get("/{document_id}/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: str,
    document: Document = Depends(get_owned_document),
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationOut:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.document_id != document.id or conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "NOT_FOUND", "message": "Conversation not found."})
    messages = [
        {"id": m.id, "role": m.role, "content": m.content, "result": m.result_json, "created_at": m.created_at.isoformat()}
        for m in conversation.messages
    ]
    return ConversationOut(id=conversation.id, document_id=document.id, messages=messages)
