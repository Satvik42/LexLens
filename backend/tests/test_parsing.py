"""Parsing, paragraph reconstruction and clause segmentation."""

from app.services.local_parser_service import LocalParserService
from app.services.retrieval_service import expand_terms, select_clauses
from app.services.segmentation_service import annotate_blocks, build_clauses
from app.services.text_utils import detect_section, paragraphs_from_text


def test_detect_section_recognises_numbered_headings_only():
    assert detect_section("8.2 Termination by Notice") == ("8.2", "Termination by Notice")
    assert detect_section("8. Termination") == ("8", "Termination")
    assert detect_section("Section 4 Compensation") == ("4", "Compensation")
    assert detect_section("§8.2 Either party may terminate...") == ("8.2", None)
    assert detect_section("4.1 Either Party may terminate this Agreement by giving thirty (30) days notice.") == ("4.1", None)
    assert detect_section("30 days written notice") == (None, None)
    assert detect_section("15 July 2025 is the joining date") == (None, None)


def test_paragraphs_from_pdf_style_lines_merge_wrapped_text():
    text = "8. Termination\n8.2 Either Party may terminate this Agreement by\nproviding sixty (60) days written notice.\n8.3 Effect of Termination\nUpon termination the Employee shall return property."
    paragraphs = paragraphs_from_text(text)
    assert paragraphs[0] == "8. Termination"
    assert paragraphs[1] == "8.2 Either Party may terminate this Agreement by providing sixty (60) days written notice."
    assert paragraphs[2].startswith("8.3 Effect of Termination")


def test_pdf_parsing_and_segmentation(demo_pdf):
    parsed = LocalParserService().parse(demo_pdf, "application/pdf")
    assert parsed.parser == "local" and parsed.page_count >= 3
    pages = annotate_blocks(parsed.pages)
    clauses = build_clauses(pages)
    sections = {clause.section for clause in clauses}
    assert {"4.1", "8.2", "11.2"} <= sections
    clause_82 = next(c for c in clauses if c.section == "8.2")
    assert "sixty (60) days" in clause_82.text


def test_txt_parsing_creates_synthetic_pages(demo_txt):
    parsed = LocalParserService().parse(demo_txt, "text/plain")
    assert parsed.page_count > 1
    assert all(page.blocks for page in parsed.pages)


def test_retrieval_selects_relevant_clauses_within_budget(demo_pdf):
    pages = annotate_blocks(LocalParserService().parse(demo_pdf, "application/pdf").pages)
    clauses = build_clauses(pages)
    terms = expand_terms("What happens to my stock options if I resign?")
    assert "resignation" in terms and "equity" in terms
    selected = select_clauses(clauses, terms, char_budget=1500)
    assert selected and sum(len(c.text) for c in selected) <= 1500
    assert any("resign" in c.text.lower() or "terminat" in c.text.lower() for c in selected)
    # document order is preserved for the model
    assert [(c.page_number, c.start) for c in selected] == sorted((c.page_number, c.start) for c in selected)
