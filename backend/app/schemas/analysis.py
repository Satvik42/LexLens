"""Structured AI output schemas and the analysis result contract returned to the frontend.

`*Output` models are the response schemas requested from Gemini. `*Result` models are what the API returns after
server-side validation and evidence verification. Keep the Gemini-facing models simple (no unions) because the
structured-output schema translator supports a constrained subset of JSON Schema.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.document import DocumentType
from app.schemas.evidence import EvidenceItem, EvidenceQuote, EvidenceStatus


# --------------------------------------------------------------------------------------------------
# Model-facing output schemas
# --------------------------------------------------------------------------------------------------
class FindingOutput(BaseModel):
    label: str = Field(description="Short plain-language name of the term, e.g. 'Notice Period'")
    value: str | None = Field(default=None, description="The concrete value, e.g. '60 days'. Null if not stated.")
    category: str = Field(description="One of the topic categories provided in the instructions")
    status: EvidenceStatus
    explanation: str = Field(description="One or two plain-language sentences grounded in the quoted evidence")
    evidence: list[EvidenceQuote] = Field(default_factory=list)


class InconsistencyValueOutput(BaseModel):
    value: str
    evidence: EvidenceQuote


class InconsistencyOutput(BaseModel):
    topic: str = Field(description="What the clauses disagree about, e.g. 'Notice period'")
    description: str = Field(description="Neutral wording; never decide which clause governs")
    values: list[InconsistencyValueOutput] = Field(min_length=2)


class FindingsOutput(BaseModel):
    summary: str = Field(description="One sentence describing what was found overall")
    findings: list[FindingOutput]
    inconsistencies: list[InconsistencyOutput] = Field(default_factory=list)
    related_questions: list[str] = Field(default_factory=list)
    professional_questions: list[str] = Field(default_factory=list)


class ConcernKind(StrEnum):
    POTENTIAL_CONCERN = "POTENTIAL_CONCERN"
    POTENTIAL_INCONSISTENCY = "POTENTIAL_INCONSISTENCY"
    IMPORTANT_CLAUSE = "IMPORTANT_CLAUSE"
    AMBIGUOUS = "AMBIGUOUS"


class ConcernOutput(BaseModel):
    kind: ConcernKind
    title: str
    explanation: str = Field(description="Why this deserves attention. Never state that a clause is illegal or invalid.")
    evidence: list[EvidenceQuote] = Field(default_factory=list)


class ConcernsOutput(BaseModel):
    summary: str
    concerns: list[ConcernOutput]
    inconsistencies: list[InconsistencyOutput] = Field(default_factory=list)
    related_questions: list[str] = Field(default_factory=list)
    professional_questions: list[str] = Field(default_factory=list)


class QaOutput(BaseModel):
    status: EvidenceStatus
    title: str = Field(description="Short headline; use 'Cannot be determined from this document' when NOT_FOUND")
    answer: str | None = Field(default=None, description="Direct answer. Null when the document does not answer.")
    explanation: str
    what_i_found: str = Field(description="What relevant content was or was not identified in the document")
    evidence: list[EvidenceQuote] = Field(default_factory=list)
    related_questions: list[str] = Field(default_factory=list)
    professional_questions: list[str] = Field(default_factory=list)


class LawyerQuestionOutput(BaseModel):
    text: str
    reason: str = Field(description="Why this question matters for this document")
    evidence: list[EvidenceQuote] = Field(default_factory=list)


class LawyerOutput(BaseModel):
    questions: list[LawyerQuestionOutput]


class ChangeKind(StrEnum):
    CHANGED = "CHANGED"
    NEW = "NEW"
    REMOVED = "REMOVED"
    UNCHANGED = "UNCHANGED"


class ComparisonRowOutput(BaseModel):
    term: str
    original_value: str | None = None
    updated_value: str | None = None
    change: ChangeKind
    note: str | None = None
    original_evidence: list[EvidenceQuote] = Field(default_factory=list)
    updated_evidence: list[EvidenceQuote] = Field(default_factory=list)


class ComparisonOutput(BaseModel):
    summary: str
    rows: list[ComparisonRowOutput]


class DocumentTypeOutput(BaseModel):
    document_type: DocumentType
    title: str = Field(description="A short human-readable title for the document, e.g. 'Employment Agreement'")


# --------------------------------------------------------------------------------------------------
# API result contract (after validation)
# --------------------------------------------------------------------------------------------------
class Finding(BaseModel):
    id: str
    label: str
    value: str | None
    category: str
    status: EvidenceStatus
    explanation: str
    evidence: list[EvidenceItem]
    verification_note: str | None = None


class InconsistencyValue(BaseModel):
    value: str
    evidence: EvidenceItem


class Inconsistency(BaseModel):
    id: str
    topic: str
    description: str
    values: list[InconsistencyValue]


class Concern(BaseModel):
    id: str
    kind: ConcernKind
    title: str
    explanation: str
    evidence: list[EvidenceItem]
    verification_note: str | None = None


class AnalysisResult(BaseModel):
    id: str
    document_id: str
    operation: str
    status: EvidenceStatus
    title: str
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    concerns: list[Concern] = Field(default_factory=list)
    inconsistencies: list[Inconsistency] = Field(default_factory=list)
    related_questions: list[str] = Field(default_factory=list)
    professional_questions: list[str] = Field(default_factory=list)
    verification_notes: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    cached: bool = False


class QaAnswer(BaseModel):
    id: str
    document_id: str
    conversation_id: str
    question: str
    status: EvidenceStatus
    title: str
    answer: str | None
    explanation: str
    what_i_found: str
    evidence: list[EvidenceItem]
    related_questions: list[str]
    professional_questions: list[str]
    verification_notes: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class LawyerQuestion(BaseModel):
    id: str
    text: str
    reason: str | None
    evidence: list[EvidenceItem] = Field(default_factory=list)


class LawyerQuestions(BaseModel):
    document_id: str
    questions: list[LawyerQuestion]


class ComparisonRow(BaseModel):
    id: str
    term: str
    original_value: str | None
    updated_value: str | None
    change: ChangeKind
    note: str | None
    original_evidence: list[EvidenceItem]
    updated_evidence: list[EvidenceItem]


class ComparisonResult(BaseModel):
    id: str
    original_document_id: str
    updated_document_id: str
    original_filename: str
    updated_filename: str
    status: EvidenceStatus
    summary: str
    rows: list[ComparisonRow]
    verification_notes: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


# --------------------------------------------------------------------------------------------------
# Request bodies
# --------------------------------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    operation: str
    force: bool = False


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=600)
    conversation_id: str | None = None


class LawyerQuestionsRequest(BaseModel):
    force: bool = False


class ComparisonRequest(BaseModel):
    original_document_id: str
    updated_document_id: str


class ConversationOut(BaseModel):
    id: str
    document_id: str
    messages: list[dict]
