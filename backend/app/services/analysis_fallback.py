"""Document-grounded analysis when Gemini cannot answer."""

import re

from app.db.models import Document
from app.domain.operations import Operation, get_spec
from app.schemas.analysis import (
    ConcernKind,
    ConcernOutput,
    ConcernsOutput,
    FindingOutput,
    FindingsOutput,
    InconsistencyOutput,
    InconsistencyValueOutput,
)
from app.schemas.document import DocumentType, NormalizedPage
from app.schemas.evidence import EvidenceQuote, EvidenceStatus
from app.services.context_service import build_operation_context
from app.services.evidence_service import EvidenceValidator
from app.services.result_assembly import assemble_analysis
from app.services.retrieval_service import select_clauses
from app.services.segmentation_service import build_clauses

_WORD_NUMBERS = {
    "seven": 7,
    "fourteen": 14,
    "fifteen": 15,
    "eighteen": 18,
    "thirty": 30,
    "forty": 40,
    "forty-five": 45,
    "forty five": 45,
    "sixty": 60,
    "ninety": 90,
}

_NOTICE_RE = re.compile(
    r"(?P<word>thirty|sixty|fifteen|fourteen|seven|eighteen|twelve|ninety|forty(?:[-\s]five)?|\d+)\s*"
    r"(?:\((?P<digits>\d+)\)\s*)?days.{0,40}notice",
    re.I | re.S,
)
_BOND_RE = re.compile(r"(training|repay|repayment|bond).{0,80}(INR|Rs\.?|₹)?\s*[\d,]+", re.I)


def _section_for(page: NormalizedPage, index: int) -> str | None:
    for block in page.blocks:
        if block.start <= index < block.end and block.section:
            return block.section
    return None


def _number(match: re.Match) -> int | None:
    digits = match.group("digits")
    if digits:
        return int(digits)
    word = match.group("word")
    if word.isdigit():
        return int(word)
    return _WORD_NUMBERS.get(word.lower().replace("  ", " "))


def _notice_hits(pages: list[NormalizedPage]) -> list[tuple[int, EvidenceQuote]]:
    hits: list[tuple[int, EvidenceQuote]] = []
    seen: set[tuple[int, str]] = set()
    for page in pages:
        for match in _NOTICE_RE.finditer(page.text):
            days = _number(match)
            snippet = match.group(0)
            if days is None or len(snippet.strip()) < 8:
                continue
            if "written notice" not in snippet.lower() and "giving" not in snippet.lower() and "providing" not in snippet.lower():
                continue
            key = (days, snippet.lower())
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                (
                    days,
                    EvidenceQuote(page=page.page_number, section=_section_for(page, match.start()), text=snippet),
                )
            )
    return hits


def _bond_quotes(pages: list[NormalizedPage]) -> list[EvidenceQuote]:
    quotes: list[EvidenceQuote] = []
    for page in pages:
        for match in _BOND_RE.finditer(page.text):
            snippet = " ".join(match.group(0).split())
            if len(snippet) < 8:
                continue
            quotes.append(EvidenceQuote(page=page.page_number, section=_section_for(page, match.start()), text=snippet[:220]))
    return quotes


def _notice_findings(hits: list[tuple[int, EvidenceQuote]]) -> FindingsOutput:
    preferred = [(days, quote) for days, quote in hits if days in {30, 60}]
    ranked = preferred or hits
    unique_days = list(dict.fromkeys(days for days, _ in ranked))
    findings: list[FindingOutput] = []
    if ranked:
        primary_days, primary_quote = next((days, quote) for days, quote in ranked if days == unique_days[-1])
        findings.append(
            FindingOutput(
                label="Notice Period",
                value=f"{primary_days} days",
                category="notice_period",
                status=EvidenceStatus.EXPLICITLY_STATED,
                explanation=f"The document states {primary_days} days' written notice.",
                evidence=[primary_quote],
            )
        )
    findings.append(
        FindingOutput(
            label="Severance",
            value=None,
            category="severance",
            status=EvidenceStatus.NOT_FOUND,
            explanation="No severance clause was identified in the retrieved text.",
            evidence=[],
        )
    )
    inconsistencies: list[InconsistencyOutput] = []
    if len(unique_days) >= 2:
        first, second = unique_days[0], unique_days[1]
        quote_a = next(quote for days, quote in hits if days == first)
        quote_b = next(quote for days, quote in hits if days == second)
        inconsistencies.append(
            InconsistencyOutput(
                topic="Notice period",
                description="These clauses appear to specify different notice periods. Consider clarifying which provision applies.",
                values=[
                    InconsistencyValueOutput(value=f"{first} days", evidence=quote_a),
                    InconsistencyValueOutput(value=f"{second} days", evidence=quote_b),
                ],
            )
        )
    return FindingsOutput(
        summary="Notice and exit terms were read from the document clauses." if hits else "No notice period was located in the document.",
        findings=findings,
        inconsistencies=inconsistencies,
        related_questions=["What happens if I resign during probation?", "Are there penalties for early exit?"],
        professional_questions=["Which notice period applies if two clauses specify different durations?"],
    )


def _concerns_output(pages: list[NormalizedPage]) -> ConcernsOutput:
    hits = _notice_hits(pages)
    notice = _notice_findings(hits)
    concerns: list[ConcernOutput] = []
    if notice.inconsistencies:
        evidence = [value.evidence for value in notice.inconsistencies[0].values]
        concerns.append(
            ConcernOutput(
                kind=ConcernKind.POTENTIAL_INCONSISTENCY,
                title="Different notice periods mentioned",
                explanation="Two clauses give different notice durations. Both quotes were located in the document.",
                evidence=evidence,
            )
        )
    bonds = _bond_quotes(pages)
    if bonds:
        concerns.append(
            ConcernOutput(
                kind=ConcernKind.POTENTIAL_CONCERN,
                title="Training cost repayment",
                explanation="A repayment or training-cost clause is present and should be reviewed.",
                evidence=bonds[:2],
            )
        )
    return ConcernsOutput(
        summary="Clauses that deserve a closer look were taken from the document text.",
        concerns=concerns,
        inconsistencies=notice.inconsistencies,
        related_questions=["Does the bond apply if I resign during probation?"],
        professional_questions=["Is the training repayment enforceable as drafted?"],
    )


def _generic_findings(document: Document, operation: Operation, pages: list[NormalizedPage]) -> FindingsOutput:
    spec = get_spec(operation)
    document_type = DocumentType(document.document_type)
    clauses = select_clauses(build_clauses(pages), list(spec.keywords_for(document_type)), 22_000)
    findings: list[FindingOutput] = []
    for clause in clauses[:6]:
        compact = " ".join(clause.text.split())
        if len(compact) < 8:
            continue
        quote = compact[:180]
        findings.append(
            FindingOutput(
                label=clause.heading or (f"Section {clause.section}" if clause.section else "Clause"),
                value=None,
                category=spec.topics[0] if spec.topics else "other",
                status=EvidenceStatus.EXPLICITLY_STATED,
                explanation="This clause was retrieved from the document because it matches the selected operation.",
                evidence=[EvidenceQuote(page=clause.page_number, section=clause.section, text=quote)],
            )
        )
    return FindingsOutput(
        summary="These clauses were selected from the document when the model was unavailable.",
        findings=findings or [
            FindingOutput(
                label="No matching clause",
                value=None,
                category="other",
                status=EvidenceStatus.NOT_FOUND,
                explanation="The document did not contain enough matching text for this operation.",
                evidence=[],
            )
        ],
        related_questions=[],
        professional_questions=[],
    )


def build_fallback_analysis(document: Document, operation: Operation, *, result_id: str):
    context = build_operation_context(document, operation)
    if operation == Operation.CONCERNS:
        output = _concerns_output(context.pages)
    elif operation == Operation.NOTICE_EXIT:
        output = _notice_findings(_notice_hits(context.pages))
    else:
        output = _generic_findings(document, operation, context.pages)
    spec = get_spec(operation)
    return assemble_analysis(
        output,
        EvidenceValidator(context.pages),
        result_id=result_id,
        document_id=document.id,
        operation=operation.value,
        title=spec.label,
    )
