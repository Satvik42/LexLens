"""Operation registry: the single place that defines what each operation means for each document type.

Operations are document-agnostic primitives. Document type only adapts wording, focus and retrieval hints.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from app.schemas.document import DocumentType


class Operation(StrEnum):
    KEY_TERMS = "KEY_TERMS"
    COMPENSATION = "COMPENSATION"
    NOTICE_EXIT = "NOTICE_EXIT"
    RESTRICTIONS = "RESTRICTIONS"
    CONCERNS = "CONCERNS"
    OBLIGATIONS = "OBLIGATIONS"
    DOCUMENT_QA = "DOCUMENT_QA"
    LAWYER_PREP = "LAWYER_PREP"
    COMPARE = "COMPARE"


# Operations whose results are persisted per (document, operation) and rendered as structured findings.
ANALYSIS_OPERATIONS: tuple[Operation, ...] = (
    Operation.KEY_TERMS,
    Operation.COMPENSATION,
    Operation.NOTICE_EXIT,
    Operation.RESTRICTIONS,
    Operation.CONCERNS,
    Operation.OBLIGATIONS,
)


@dataclass(frozen=True)
class OperationSpec:
    key: Operation
    label: str
    description: str
    focus: str  # instruction fragment describing what to extract
    keywords: tuple[str, ...]
    topics: tuple[str, ...] = ()  # categories the model should use for findings
    type_focus: dict[DocumentType, str] = field(default_factory=dict)
    type_keywords: dict[DocumentType, tuple[str, ...]] = field(default_factory=dict)

    def focus_for(self, document_type: DocumentType) -> str:
        extra = self.type_focus.get(document_type)
        return f"{self.focus} {extra}" if extra else self.focus

    def keywords_for(self, document_type: DocumentType) -> tuple[str, ...]:
        return self.keywords + self.type_keywords.get(document_type, ())


_COMMON_EXIT_KEYWORDS = (
    "notice", "terminate", "termination", "resign", "resignation", "exit", "expiry", "expire",
    "renewal", "severance", "garden leave", "cause", "breach", "cure period", "handover", "last working day",
)

_MONEY_KEYWORDS = (
    "salary", "compensation", "ctc", "pay", "payment", "fee", "fees", "bonus", "incentive", "allowance",
    "reimbursement", "invoice", "rate", "amount", "₹", "rs.", "inr", "$", "usd", "per month", "per annum",
    "benefit", "benefits", "insurance", "provident", "gratuity", "leave", "vacation", "equity", "stock", "esop",
)

OPERATIONS: dict[Operation, OperationSpec] = {
    Operation.KEY_TERMS: OperationSpec(
        key=Operation.KEY_TERMS,
        label="Key Terms",
        description="Extract important dates, amounts, durations and conditions.",
        focus=(
            "Extract the most important concrete terms: parties, dates, durations, amounts, renewal, "
            "governing law, notice periods, probation/trial periods and any figure a reader would want to know."
        ),
        keywords=(
            "effective date", "commencement", "term", "duration", "period", "date", "amount", "months", "years",
            "days", "renew", "governing law", "jurisdiction", "probation", "notice", "parties", "between",
        ),
        topics=("parties", "dates", "duration", "amounts", "conditions", "other"),
        type_focus={
            DocumentType.RENTAL: "Include rent, deposit, lease start/end, renewal and lock-in periods.",
            DocumentType.NDA: "Include the definition of confidential information, duration and governing law.",
            DocumentType.SAAS_TERMS: "Include subscription term, fees, renewal, service levels and data handling.",
        },
    ),
    Operation.COMPENSATION: OperationSpec(
        key=Operation.COMPENSATION,
        label="Compensation & Benefits",
        description="Find payment, salary, fees, bonuses, benefits and related terms.",
        focus="Extract every payment-related term: amounts, frequency, conditions, deductions, bonuses and benefits.",
        keywords=_MONEY_KEYWORDS,
        topics=("payment", "bonus", "benefit", "deduction", "reimbursement", "equity", "other"),
        type_focus={
            DocumentType.RENTAL: "Focus on rent, security deposit, maintenance charges, late fees and refund conditions.",
            DocumentType.FREELANCE: "Focus on rates, invoicing schedule, payment timelines, expenses and late-payment terms.",
            DocumentType.SAAS_TERMS: "Focus on subscription fees, renewal charges, price changes, refunds and taxes.",
            DocumentType.VENDOR: "Focus on pricing, payment terms, penalties, credits and invoicing.",
        },
        type_keywords={
            DocumentType.RENTAL: ("rent", "deposit", "security deposit", "maintenance", "late fee", "refund"),
            DocumentType.SAAS_TERMS: ("subscription", "renewal", "refund", "tax", "price"),
        },
    ),
    Operation.NOTICE_EXIT: OperationSpec(
        key=Operation.NOTICE_EXIT,
        label="Notice & Exit Terms",
        description="Understand termination, resignation, notice periods and exit conditions.",
        focus=(
            "Extract how the relationship can end: notice periods for each party, termination for cause, "
            "resignation, expiry/renewal, severance, exit obligations and post-exit restrictions."
        ),
        keywords=_COMMON_EXIT_KEYWORDS + ("post-employment", "return of property", "final settlement", "lock-in"),
        topics=("notice_period", "termination", "resignation", "severance", "post_exit", "renewal", "other"),
        type_focus={
            DocumentType.RENTAL: "Include lock-in period, vacating notice, deposit refund timing and early termination penalties.",
            DocumentType.SAAS_TERMS: "Include cancellation, auto-renewal, suspension and data export after termination.",
        },
    ),
    Operation.RESTRICTIONS: OperationSpec(
        key=Operation.RESTRICTIONS,
        label="Restrictions",
        description="Find confidentiality, non-compete, non-solicitation, exclusivity, bonds and similar restrictions.",
        focus=(
            "Extract every restriction placed on a party: confidentiality, non-compete, non-solicitation, exclusivity, "
            "training bonds or repayment obligations, IP assignment, use restrictions, and their scope and duration."
        ),
        keywords=(
            "confidential", "confidentiality", "non-compete", "non compete", "compete", "non-solicit", "solicit",
            "exclusive", "exclusivity", "bond", "repay", "repayment", "intellectual property", "assign", "restrict",
            "prohibited", "shall not", "may not", "must not", "without prior written consent", "sublet", "subletting",
        ),
        topics=("confidentiality", "non_compete", "non_solicitation", "exclusivity", "bond", "ip", "use_restriction", "other"),
    ),
    Operation.CONCERNS: OperationSpec(
        key=Operation.CONCERNS,
        label="Potential Concerns",
        description="Identify clauses that deserve closer attention, unusual terms, ambiguity or potential conflicts.",
        focus=(
            "Identify clauses a careful reader should review: one-sided terms, penalties, broad restrictions, "
            "ambiguous wording, undefined terms, and especially clauses that appear to conflict with each other."
        ),
        keywords=(
            "penalty", "liquidated", "indemnif", "sole discretion", "unilateral", "waive", "forfeit", "bond",
            "notice", "terminate", "non-compete", "at any time", "without cause", "automatically", "renew",
            "liable", "liability", "damages", "arbitration", "jurisdiction",
        ),
        topics=("POTENTIAL_CONCERN", "POTENTIAL_INCONSISTENCY", "IMPORTANT_CLAUSE", "AMBIGUOUS"),
    ),
    Operation.OBLIGATIONS: OperationSpec(
        key=Operation.OBLIGATIONS,
        label="Your Obligations",
        description="Turn document obligations into an actionable checklist.",
        focus=(
            "List the concrete obligations of the receiving party (the person most likely reading this document): "
            "what they must do, by when, and under what conditions. One obligation per finding, phrased as an action."
        ),
        keywords=(
            "shall", "must", "agrees to", "undertakes", "responsible", "obligation", "comply", "provide", "return",
            "maintain", "notify", "deliver", "submit", "pay", "report", "within",
        ),
        topics=("during_term", "on_exit", "payment", "confidentiality", "compliance", "other"),
        type_focus={
            DocumentType.RENTAL: "The receiving party is the tenant.",
            DocumentType.EMPLOYMENT: "The receiving party is the employee.",
            DocumentType.FREELANCE: "The receiving party is the freelancer/contractor.",
            DocumentType.INTERNSHIP: "The receiving party is the intern.",
        },
    ),
    Operation.DOCUMENT_QA: OperationSpec(
        key=Operation.DOCUMENT_QA,
        label="Ask About the Document",
        description="Ask a question grounded in the supplied document.",
        focus="Answer the user's question using only the supplied document excerpts.",
        keywords=(),
    ),
    Operation.LAWYER_PREP: OperationSpec(
        key=Operation.LAWYER_PREP,
        label="Prepare for a Lawyer",
        description="Generate useful questions to clarify with a legal professional.",
        focus="Prepare specific questions a legal professional could answer about this document.",
        keywords=("notice", "terminate", "bond", "penalty", "non-compete", "confidential", "liability", "indemnif", "renew"),
    ),
    Operation.COMPARE: OperationSpec(
        key=Operation.COMPARE,
        label="Compare Another Document",
        description="Upload a second document and compare relevant terms.",
        focus="Compare the key terms of two versions of a document.",
        keywords=(),
    ),
}


def get_spec(operation: Operation) -> OperationSpec:
    return OPERATIONS[operation]
