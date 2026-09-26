"""Shared text helpers used by parsing, segmentation, retrieval and evidence validation."""

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_TOKEN = re.compile(r"[a-z0-9₹$€£%]+")
_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-"})

# "8.2 Termination", "8. Termination", "Section 4", "Clause 8.2", "§8.2", "Article III".
# A bare number followed by text ("30 days") is deliberately NOT a section start.
_SECTION_PREFIX = re.compile(
    r"^\s*(?:(?P<keyword>section|clause|article|§)\s*)?"
    r"(?P<number>\d{1,2}(?:\.\d{1,2}){0,3})(?P<dot>\.)?\)?\s+(?P<rest>\S.*)$",
    re.IGNORECASE,
)
_ROMAN_ARTICLE = re.compile(r"^\s*(?:article|section)\s+(?P<number>[IVXLC]+)[.:]?\s+(?P<rest>\S.*)$", re.IGNORECASE)
MAX_HEADING_LENGTH = 90

STOPWORDS = frozenset(
    """a an and are as at be by for from has have if in into is it its of on or that the this to was
    will with shall may any such under upon other party parties agreement hereof herein thereof""".split()
)


def make_block_id(page_number: int, index: int) -> str:
    return f"p{page_number}-b{index}"


def normalize_text(text: str) -> str:
    """Lower-case, unify quotes/dashes, collapse whitespace. Used for matching, never for display."""
    text = unicodedata.normalize("NFKC", text).translate(_QUOTES)
    return _WHITESPACE.sub(" ", text).strip().lower()


def tokenize(text: str) -> list[str]:
    return [token for token in _TOKEN.findall(text.lower()) if token not in STOPWORDS]


def first_line(text: str) -> str:
    stripped = text.strip()
    return stripped.splitlines()[0] if stripped else ""


def detect_section(text: str) -> tuple[str | None, str | None]:
    """Return (section_number, heading) if the text starts a numbered section, else (None, None)."""
    line = first_line(text)
    match = _SECTION_PREFIX.match(line)
    if match:
        if not (match.group("keyword") or match.group("dot") or "." in match.group("number")):
            return None, None
    else:
        match = _ROMAN_ARTICLE.match(line)
        if not match:
            return None, None
    number = match.group("number").rstrip(".")
    rest = match.group("rest").strip()
    return number, (rest if looks_like_heading(rest) else None)


def looks_like_heading(rest: str) -> bool:
    if not rest or len(rest) > MAX_HEADING_LENGTH or rest.endswith((";", ",")):
        return False
    words = rest.rstrip(".").split()
    if len(words) > 10:
        return False
    capitalised = sum(1 for word in words if word[:1].isupper())
    return capitalised >= max(1, (len(words) + 1) // 2)


def paragraphs_from_text(text: str) -> list[str]:
    """Group lines into paragraphs. A blank line, a numbered section start, or an all-caps title starts a new one.

    Works for text with blank-line separated paragraphs (TXT/DOCX) and for PDF extraction where wrapped lines
    are separated only by single newlines.
    """
    paragraphs: list[str] = []
    open_paragraph = False
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            open_paragraph = False
            continue
        starts_section = detect_section(line)[0] is not None
        is_title = line.isupper() and len(line) <= MAX_HEADING_LENGTH
        if not open_paragraph or starts_section or is_title:
            paragraphs.append(line)
            open_paragraph = not is_title
        else:
            paragraphs[-1] = f"{paragraphs[-1]} {line}"
    return paragraphs
