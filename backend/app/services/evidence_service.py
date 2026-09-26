"""Evidence validation: every quote returned by the model must be located in the parsed document.

Located quotes receive offsets (and block/bounding box when available) and are marked verified.
Quotes that cannot be located are rejected so they are never presented as verified document facts.
"""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from app.schemas.document import NormalizedBlock, NormalizedPage
from app.schemas.evidence import EvidenceItem, EvidenceQuote, EvidenceStatus
from app.services.segmentation_service import find_section_heading
from app.services.text_utils import normalize_text

_FUZZY_THRESHOLD = 0.9
_MIN_QUOTE_CHARS = 8
_DIGITS = re.compile(r"\d+")


@dataclass
class ValidationReport:
    failed_quotes: list[str] = field(default_factory=list)
    repaired_pages: int = 0

    @property
    def notes(self) -> list[str]:
        notes = []
        if self.failed_quotes:
            notes.append(
                f"{len(self.failed_quotes)} evidence quote(s) could not be verified against the document and were not shown."
            )
        return notes


class _NormalizedIndex:
    """Normalized text with a map back to original character offsets."""

    def __init__(self, original: str) -> None:
        self.original = original
        chars: list[str] = []
        self.offsets: list[int] = []
        previous_space = True
        for index, char in enumerate(normalize_text_preserving_length(original)):
            is_space = char.isspace()
            if is_space and previous_space:
                continue
            chars.append(" " if is_space else char)
            self.offsets.append(index)
            previous_space = is_space
        self.text = "".join(chars).strip()

    def to_original_span(self, start: int, end: int) -> tuple[int, int]:
        start = max(0, min(start, len(self.offsets) - 1))
        end = max(start + 1, min(end, len(self.offsets)))
        return self.offsets[start], self.offsets[end - 1] + 1


def normalize_text_preserving_length(text: str) -> str:
    """Character-wise normalization (no collapsing) so indices stay aligned with the original."""
    table = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-"})
    return text.translate(table).lower()


def locate_quote(page_text: str, quote: str, *, allow_fuzzy: bool = True) -> tuple[int, int] | None:
    """Find a quote in a page. Exact → whitespace/quote-normalized → (optionally) fuzzy sliding window."""
    quote = quote.strip()
    if len(quote) < _MIN_QUOTE_CHARS:
        return None
    exact = page_text.find(quote)
    if exact >= 0:
        return exact, exact + len(quote)

    index = _NormalizedIndex(page_text)
    needle = normalize_text(quote)
    position = index.text.find(needle)
    if position >= 0:
        return index.to_original_span(position, position + len(needle))
    return _fuzzy_locate(index, needle) if allow_fuzzy else None


def _numbers_preserved(needle: str, candidate: str) -> bool:
    """Fuzzy matches must never swap figures (e.g. 'sixty (60)' vs 'thirty (30)')."""
    return set(_DIGITS.findall(needle)) <= set(_DIGITS.findall(candidate))


def _fuzzy_locate(index: _NormalizedIndex, needle: str) -> tuple[int, int] | None:
    haystack = index.text
    window = len(needle)
    if window > len(haystack):
        return None
    step = max(1, window // 8)
    best_ratio, best_start = 0.0, -1
    matcher = SequenceMatcher(None, "", needle, autojunk=False)
    for start in range(0, len(haystack) - window + 1, step):
        candidate = haystack[start : start + window]
        matcher.set_seq1(candidate)
        if matcher.real_quick_ratio() < _FUZZY_THRESHOLD or matcher.quick_ratio() < _FUZZY_THRESHOLD:
            continue
        ratio = matcher.ratio()
        if ratio > best_ratio and _numbers_preserved(needle, candidate):
            best_ratio, best_start = ratio, start
    if best_ratio < _FUZZY_THRESHOLD:
        return None
    start, end = index.to_original_span(best_start, best_start + window)
    return _snap_to_word_boundaries(index.original, start, end)


def _snap_to_word_boundaries(text: str, start: int, end: int) -> tuple[int, int]:
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while end < len(text) and not text[end].isspace():
        end += 1
    return start, end


def _block_at(page: NormalizedPage, offset: int) -> NormalizedBlock | None:
    for block in page.blocks:
        if block.start <= offset < block.end:
            return block
    return None


class EvidenceValidator:
    def __init__(self, pages: list[NormalizedPage]) -> None:
        self._pages = {page.page_number: page for page in pages}
        self._ordered = pages
        self.report = ValidationReport()

    def validate(self, quote: EvidenceQuote) -> EvidenceItem | None:
        candidate_pages = self._candidate_pages(quote.page)
        # Exact/normalized matches anywhere beat a fuzzy match on the stated page.
        for allow_fuzzy in (False, True):
            for page in candidate_pages:
                span = locate_quote(page.text, quote.text, allow_fuzzy=allow_fuzzy)
                if span is None:
                    continue
                if page.page_number != quote.page:
                    self.report.repaired_pages += 1
                return self._build_item(quote, page, span)
        self.report.failed_quotes.append(quote.text)
        return None

    def validate_all(self, quotes: list[EvidenceQuote]) -> list[EvidenceItem]:
        items = [self.validate(quote) for quote in quotes]
        return [item for item in items if item is not None]

    def _candidate_pages(self, stated_page: int) -> list[NormalizedPage]:
        stated = self._pages.get(stated_page)
        neighbours = [self._pages.get(stated_page - 1), self._pages.get(stated_page + 1)]
        ordered = [stated, *neighbours] + [p for p in self._ordered if p not in (stated, *neighbours)]
        return [page for page in ordered if page is not None]

    def _build_item(self, quote: EvidenceQuote, page: NormalizedPage, span: tuple[int, int]) -> EvidenceItem:
        start, end = span
        block = _block_at(page, start)
        section = quote.section or (block.section if block else None)
        heading = find_section_heading(self._ordered, section) if section else None
        return EvidenceItem(
            page=page.page_number,
            section=section,
            text=page.text[start:end],
            heading=heading,
            start_offset=start,
            end_offset=end,
            block_id=block.block_id if block else None,
            verified=True,
        )


def downgrade_status(status: EvidenceStatus, has_evidence: bool, requested_evidence: bool) -> tuple[EvidenceStatus, str | None]:
    """A claim whose evidence was all rejected must not be presented as explicitly stated."""
    if has_evidence or not requested_evidence:
        return status, None
    if status in (EvidenceStatus.EXPLICITLY_STATED, EvidenceStatus.POTENTIAL_INCONSISTENCY):
        return EvidenceStatus.PARTIALLY_DETERMINED, "We couldn't verify this against the document, so it is not shown as verified."
    if status == EvidenceStatus.PARTIALLY_DETERMINED:
        return EvidenceStatus.NOT_FOUND, "We couldn't verify supporting text for this in the document."
    return status, None
