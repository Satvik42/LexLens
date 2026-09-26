"""A deterministic stand-in for Gemini that returns schema-valid outputs and records prompts."""

from collections import deque
from typing import TypeVar

from pydantic import BaseModel

from app.schemas.analysis import (
    ComparisonOutput,
    ComparisonRowOutput,
    ConcernOutput,
    ConcernsOutput,
    DocumentTypeOutput,
    FindingOutput,
    FindingsOutput,
    InconsistencyOutput,
    InconsistencyValueOutput,
    LawyerOutput,
    LawyerQuestionOutput,
    QaOutput,
)
from app.schemas.document import DocumentType
from app.schemas.evidence import EvidenceQuote, EvidenceStatus
from app.services.gemini_service import StructuredModel

TModel = TypeVar("TModel", bound=BaseModel)

QUOTE_60 = EvidenceQuote(page=3, section="8.2", text="sixty (60) days written notice")
QUOTE_30 = EvidenceQuote(page=1, section="4.1", text="thirty (30) days written notice")
QUOTE_BOND = EvidenceQuote(page=3, section="11.2", text="repay to the Company the Training cost of INR 2,00,000")
QUOTE_FAKE = EvidenceQuote(page=3, section="8.2", text="ninety (90) days written notice is required")


def notice_findings(*, include_conflict: bool = True, fabricated: bool = False) -> FindingsOutput:
    evidence = [QUOTE_FAKE] if fabricated else [QUOTE_60]
    findings = [
        FindingOutput(label="Notice Period", value="60 days", category="notice_period", status=EvidenceStatus.EXPLICITLY_STATED, explanation="Either party must give 60 days written notice.", evidence=evidence),
        FindingOutput(label="Severance", value=None, category="severance", status=EvidenceStatus.NOT_FOUND, explanation="No severance clause was identified.", evidence=[]),
    ]
    inconsistencies = []
    if include_conflict:
        inconsistencies.append(
            InconsistencyOutput(
                topic="Notice period",
                description="These clauses appear to specify different notice periods. Consider clarifying which provision applies.",
                values=[InconsistencyValueOutput(value="30 days", evidence=QUOTE_30), InconsistencyValueOutput(value="60 days", evidence=QUOTE_60)],
            )
        )
    return FindingsOutput(
        summary="The agreement states notice periods in two clauses.",
        findings=findings,
        inconsistencies=inconsistencies,
        related_questions=["What happens if I resign during probation?", "Are there penalties for early exit?"],
        professional_questions=["Which notice period applies if two clauses specify different durations?"],
    )


def not_found_answer() -> QaOutput:
    return QaOutput(
        status=EvidenceStatus.NOT_FOUND,
        title="Cannot be determined from this document",
        answer=None,
        explanation="I couldn't identify a clause in the supplied document that explains what happens to stock options after resignation.",
        what_i_found="No relevant stock-option or equity clause was identified in this document.",
        evidence=[],
        related_questions=["Is there a separate equity agreement?"],
        professional_questions=["What happens to vested options after resignation?", "Is there an exercise period after leaving?"],
    )


def explicit_answer() -> QaOutput:
    return QaOutput(
        status=EvidenceStatus.EXPLICITLY_STATED,
        title="Notice period",
        answer="60 days",
        explanation="Clause 8.2 requires sixty days written notice.",
        what_i_found="A termination-by-notice clause.",
        evidence=[QUOTE_60],
        related_questions=["Can the company waive the notice period?"],
        professional_questions=[],
    )


def _default(schema: type[BaseModel]) -> BaseModel:
    if schema is FindingsOutput:
        return notice_findings()
    if schema is ConcernsOutput:
        return ConcernsOutput(
            summary="One potential inconsistency and one restrictive clause were identified.",
            concerns=[
                ConcernOutput(kind="POTENTIAL_INCONSISTENCY", title="Different notice periods mentioned", explanation="Two clauses give different durations.", evidence=[QUOTE_30, QUOTE_60]),
                ConcernOutput(kind="POTENTIAL_CONCERN", title="Training cost repayment", explanation="A repayment may be triggered by resignation.", evidence=[QUOTE_BOND]),
            ],
            inconsistencies=notice_findings().inconsistencies,
            related_questions=["Does the bond apply if I resign during probation?"],
            professional_questions=["Is the training repayment enforceable as drafted?"],
        )
    if schema is QaOutput:
        return not_found_answer()
    if schema is LawyerOutput:
        return LawyerOutput(questions=[LawyerQuestionOutput(text="Which notice period applies?", reason="Two clauses differ.", evidence=[QUOTE_30, QUOTE_60])])
    if schema is ComparisonOutput:
        return ComparisonOutput(
            summary="The notice period changed.",
            rows=[ComparisonRowOutput(term="Notice Period", original_value="30 days", updated_value="60 days", change="CHANGED", original_evidence=[QUOTE_30], updated_evidence=[QUOTE_60])],
        )
    if schema is DocumentTypeOutput:
        return DocumentTypeOutput(document_type=DocumentType.EMPLOYMENT, title="Employment Agreement")
    raise AssertionError(f"FakeModel has no default for {schema.__name__}")


class FakeModel(StructuredModel):
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.queued: deque[BaseModel] = deque()
        self.calls = 0

    def queue(self, *outputs: BaseModel) -> None:
        self.queued.extend(outputs)

    def generate(self, prompt: str, schema: type[TModel], *, conversational: bool = False) -> TModel:
        self.calls += 1
        self.prompts.append(prompt)
        if self.queued:
            output = self.queued.popleft()
            assert isinstance(output, schema), f"queued {type(output).__name__} but {schema.__name__} requested"
            return output
        return _default(schema)  # type: ignore[return-value]
