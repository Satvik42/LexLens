"""Section/clause segmentation over normalized pages.

Groups blocks into clauses by their numbered section. Pure functions: deterministic and cheap enough to run on
demand from stored pages.
"""

from app.schemas.document import Clause, NormalizedPage
from app.services.text_utils import MAX_HEADING_LENGTH, detect_section, first_line


def annotate_blocks(pages: list[NormalizedPage]) -> list[NormalizedPage]:
    """Attach section numbers and heading flags to blocks in place and return the pages."""
    current_section: str | None = None
    for page in pages:
        for block in page.blocks:
            number, heading = detect_section(block.text)
            if number:
                current_section = number
                block.is_heading = heading is not None and len(block.text) <= MAX_HEADING_LENGTH
            block.section = current_section
    return pages


def build_clauses(pages: list[NormalizedPage]) -> list[Clause]:
    """Group consecutive blocks that share a section into clauses. Text before any section forms its own clauses."""
    clauses: list[Clause] = []
    current: dict | None = None

    def flush() -> None:
        nonlocal current
        if current and current["text"].strip():
            clauses.append(
                Clause(
                    clause_id=f"c{len(clauses) + 1}",
                    section=current["section"],
                    heading=current["heading"],
                    page_number=current["page"],
                    text=current["text"].strip(),
                    start=current["start"],
                    end=current["end"],
                )
            )
        current = None

    for page in pages:
        for block in page.blocks:
            number, heading = detect_section(block.text)
            starts_new = number is not None or current is None or current["page"] != page.page_number
            if starts_new:
                flush()
                current = {
                    "section": number or block.section,
                    "heading": heading or (first_line(block.text) if block.is_heading else None),
                    "page": page.page_number,
                    "text": block.text,
                    "start": block.start,
                    "end": block.end,
                }
            else:
                current["text"] += "\n\n" + block.text
                current["end"] = block.end
    flush()
    return clauses


def find_section_heading(pages: list[NormalizedPage], section: str) -> str | None:
    """Heading for a section number, falling back to the parent section (e.g. 8.2 → 8)."""
    candidates = [section]
    if "." in section:
        candidates.append(section.split(".")[0])
    headings: dict[str, str] = {}
    for page in pages:
        for block in page.blocks:
            number, heading = detect_section(block.text)
            if number and heading and number not in headings:
                headings[number] = heading
    for candidate in candidates:
        if candidate in headings:
            return headings[candidate]
    return None
