"""Render the plain-text demo agreements in ./src into paginated PDFs.

Usage (from the repository root, with the backend virtualenv active):
    python demo_documents/build_pdfs.py
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).parent
SOURCE_DIR = ROOT / "src"

styles = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=styles["Normal"], fontName="Helvetica", fontSize=10.5, leading=15, spaceAfter=7)
HEADING = ParagraphStyle("heading", parent=BODY, fontName="Helvetica-Bold", fontSize=11.5, spaceBefore=8, spaceAfter=6)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Helvetica-Bold", fontSize=15, alignment=1, spaceAfter=16)


def _is_heading(paragraph: str) -> bool:
    first_word = paragraph.split(" ", 1)[0]
    return first_word.rstrip(".").isdigit() and len(paragraph) < 80 and "." not in first_word.rstrip(".")


def build_pdf(source: Path, target: Path) -> None:
    paragraphs = [p.strip() for p in source.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    document = SimpleDocTemplate(
        str(target), pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=22 * mm, bottomMargin=22 * mm,
        title=paragraphs[0], author="LexLens demo",
    )
    story = [Paragraph(paragraphs[0], TITLE), Spacer(1, 4)]
    for paragraph in paragraphs[1:]:
        escaped = paragraph.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        story.append(Paragraph(escaped, HEADING if _is_heading(paragraph) else BODY))
    document.build(story)


if __name__ == "__main__":
    for source in sorted(SOURCE_DIR.glob("*.txt")):
        target = ROOT / f"{source.stem}.pdf"
        build_pdf(source, target)
        print(f"wrote {target.relative_to(ROOT.parent)}")
