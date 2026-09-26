"""Formatting of retrieved document context supplied to the model."""

from app.schemas.document import Clause, DocumentType, NormalizedPage
from app.prompts.system import wrap_untrusted
from app.services.text_utils import detect_section

_MAX_OUTLINE_ITEMS = 80


def format_outline(pages: list[NormalizedPage]) -> str:
    """Section outline so the model knows what the document covers and what it does not."""
    lines: list[str] = []
    seen: set[str] = set()
    for page in pages:
        for block in page.blocks:
            number, heading = detect_section(block.text)
            if number and heading and number not in seen:
                seen.add(number)
                lines.append(f"§{number} {heading} (page {page.page_number})")
            if len(lines) >= _MAX_OUTLINE_ITEMS:
                return "\n".join(lines)
    return "\n".join(lines) if lines else "(no numbered sections detected)"


def format_clauses(clauses: list[Clause]) -> str:
    parts = []
    for clause in clauses:
        header = f"[page {clause.page_number}" + (f" · §{clause.section}" if clause.section else "") + "]"
        parts.append(f"{header}\n{clause.text}")
    return "\n\n".join(parts)


def document_context(document_type: DocumentType, title: str | None, pages: list[NormalizedPage], clauses: list[Clause]) -> str:
    metadata = f"Document type: {document_type.value.replace('_', ' ').title()}" + (f"\nTitle: {title}" if title else "")
    body = f"{metadata}\n\nOUTLINE:\n{format_outline(pages)}\n\nEXCERPTS:\n{format_clauses(clauses)}"
    return wrap_untrusted("document", body)
