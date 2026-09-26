"""Evidence must be located in the parsed document before it is presented as verified."""

from app.schemas.document import NormalizedBlock, NormalizedPage
from app.schemas.evidence import EvidenceQuote, EvidenceStatus
from app.services.evidence_service import EvidenceValidator, downgrade_status, locate_quote
from app.services.segmentation_service import annotate_blocks

PAGE_TEXT = (
    "8. Termination\n\n"
    "8.1 The Company may terminate this Agreement with immediate effect for gross misconduct.\n\n"
    "8.2 Termination by Notice. Either Party may terminate this Agreement by providing sixty (60) days written "
    "notice to the other Party. The Company may waive the notice period.\n\n"
    "8.3 The Employee shall return all Company property, including laptops and “access cards”."
)


def _pages() -> list[NormalizedPage]:
    blocks, cursor = [], 0
    for index, paragraph in enumerate(PAGE_TEXT.split("\n\n")):
        blocks.append(NormalizedBlock(block_id=f"p14-b{index}", text=paragraph, start=cursor, end=cursor + len(paragraph)))
        cursor += len(paragraph) + 2
    other = NormalizedPage(page_number=4, text="4.1 Either Party may terminate by giving thirty (30) days written notice.", blocks=[
        NormalizedBlock(block_id="p4-b0", text="4.1 Either Party may terminate by giving thirty (30) days written notice.", start=0, end=75)
    ])
    return annotate_blocks([other, NormalizedPage(page_number=14, text=PAGE_TEXT, blocks=blocks)])


def test_exact_match_returns_offsets():
    span = locate_quote(PAGE_TEXT, "sixty (60) days written notice")
    assert span is not None
    assert PAGE_TEXT[span[0] : span[1]] == "sixty (60) days written notice"


def test_whitespace_and_quote_normalization():
    span = locate_quote(PAGE_TEXT, 'including   laptops and "access cards"')
    assert span is not None
    assert "laptops" in PAGE_TEXT[span[0] : span[1]] and "access cards" in PAGE_TEXT[span[0] : span[1]]


def test_fuzzy_match_tolerates_minor_ocr_noise():
    span = locate_quote(PAGE_TEXT, "Either Party may terminate this Agreement by providng sixty (60) days written notice")
    assert span is not None
    assert "sixty (60) days written notice" in PAGE_TEXT[span[0] : span[1]]


def test_fuzzy_match_never_swaps_numbers():
    assert locate_quote(PAGE_TEXT, "by providing thirty (30) days written notice to the other Party") is None


def test_missing_quote_is_rejected():
    assert locate_quote(PAGE_TEXT, "ninety (90) days written notice is required") is None
    assert locate_quote(PAGE_TEXT, "short") is None


def test_validator_accepts_and_enriches_verified_quote():
    validator = EvidenceValidator(_pages())
    item = validator.validate(EvidenceQuote(page=14, section=None, text="sixty (60) days written notice"))
    assert item is not None and item.verified
    assert item.page == 14 and item.section == "8.2" and item.heading == "Termination"
    assert item.start_offset is not None and item.block_id == "p14-b2"
    assert validator.report.failed_quotes == []


def test_validator_repairs_wrong_page():
    validator = EvidenceValidator(_pages())
    item = validator.validate(EvidenceQuote(page=14, section="4.1", text="thirty (30) days written notice"))
    assert item is not None and item.page == 4
    assert validator.report.repaired_pages == 1


def test_validator_rejects_fabricated_quote():
    validator = EvidenceValidator(_pages())
    assert validator.validate(EvidenceQuote(page=14, section="8.2", text="ninety (90) days written notice is required")) is None
    assert validator.report.failed_quotes == ["ninety (90) days written notice is required"]
    assert validator.report.notes and "could not be verified" in validator.report.notes[0]


def test_status_is_downgraded_when_evidence_is_rejected():
    assert downgrade_status(EvidenceStatus.EXPLICITLY_STATED, has_evidence=False, requested_evidence=True)[0] == EvidenceStatus.PARTIALLY_DETERMINED
    assert downgrade_status(EvidenceStatus.PARTIALLY_DETERMINED, has_evidence=False, requested_evidence=True)[0] == EvidenceStatus.NOT_FOUND
    assert downgrade_status(EvidenceStatus.EXPLICITLY_STATED, has_evidence=True, requested_evidence=True) == (EvidenceStatus.EXPLICITLY_STATED, None)
    assert downgrade_status(EvidenceStatus.NOT_FOUND, has_evidence=False, requested_evidence=False) == (EvidenceStatus.NOT_FOUND, None)
