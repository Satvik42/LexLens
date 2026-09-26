"""Builds targeted model context for a document: pages → clauses → relevant selection → formatted prompt block."""

from dataclasses import dataclass

from app.db.models import Document
from app.domain.operations import Operation, OperationSpec, get_spec
from app.prompts.context import document_context
from app.schemas.document import DocumentType, NormalizedPage
from app.services.document_processing_service import load_pages
from app.services.retrieval_service import DEFAULT_CHAR_BUDGET, expand_terms, select_clauses
from app.services.segmentation_service import build_clauses

_WIDE_BUDGET = 22_000  # document-wide operations benefit from broader coverage
_WIDE_OPERATIONS = {Operation.KEY_TERMS, Operation.CONCERNS, Operation.OBLIGATIONS, Operation.LAWYER_PREP, Operation.COMPARE}


@dataclass
class DocumentContext:
    pages: list[NormalizedPage]
    document_type: DocumentType
    prompt_block: str
    clause_count: int


def _budget_for(operation: Operation) -> int:
    return _WIDE_BUDGET if operation in _WIDE_OPERATIONS else DEFAULT_CHAR_BUDGET


def build_operation_context(document: Document, operation: Operation) -> DocumentContext:
    spec: OperationSpec = get_spec(operation)
    pages = load_pages(document)
    document_type = DocumentType(document.document_type)
    clauses = build_clauses(pages)
    selected = select_clauses(clauses, list(spec.keywords_for(document_type)), _budget_for(operation))
    return DocumentContext(
        pages=pages,
        document_type=document_type,
        prompt_block=document_context(document_type, document.document_title, pages, selected),
        clause_count=len(selected),
    )


def build_question_context(document: Document, question: str) -> DocumentContext:
    pages = load_pages(document)
    document_type = DocumentType(document.document_type)
    clauses = build_clauses(pages)
    selected = select_clauses(clauses, expand_terms(question), DEFAULT_CHAR_BUDGET)
    return DocumentContext(
        pages=pages,
        document_type=document_type,
        prompt_block=document_context(document_type, document.document_title, pages, selected),
        clause_count=len(selected),
    )
