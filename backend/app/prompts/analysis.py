"""Prompt builders for structured analysis operations."""

from app.domain.operations import Operation, OperationSpec
from app.schemas.document import DocumentType

_FINDING_RULES = """For each finding:
- `label`: short plain-language name (e.g. "Notice Period", "Security Deposit", "Return company property").
- `value`: the concrete value or null if the document does not state one.
- `category`: one of {topics}.
- `status`: EXPLICITLY_STATED if the value is clearly stated in the quoted clause; PARTIALLY_DETERMINED if only part of
  it is stated; NOT_FOUND if you are recording that an expected term is absent (value null, no evidence).
- `evidence`: 1-3 verbatim quotes with page and section from the excerpt headers.
- Cover distinct terms; do not repeat the same term twice. Order by importance.
- If two clauses give different values for the same term, keep each finding grounded in its own clause and ALSO add an
  entry to `inconsistencies` with both quotes.
"""

_CONCERN_RULES = """For each concern:
- `kind`: POTENTIAL_CONCERN (one-sided, penalty, broad), POTENTIAL_INCONSISTENCY (conflicting clauses),
  IMPORTANT_CLAUSE (significant but not necessarily problematic), AMBIGUOUS (unclear or undefined wording).
- `title`: short plain-language headline.
- `explanation`: why a reader may want to review or clarify it. Never state legal conclusions.
- `evidence`: 1-3 verbatim quotes.
- Every POTENTIAL_INCONSISTENCY concern must also appear in `inconsistencies` with both quotes and values.
- If nothing deserves attention, return an empty list and say so in the summary; never invent concerns.
"""


def build_analysis_prompt(spec: OperationSpec, document_type: DocumentType, context: str, repair_feedback: str | None = None) -> str:
    rules = _CONCERN_RULES if spec.key == Operation.CONCERNS else _FINDING_RULES.format(topics=", ".join(spec.topics))
    parts = [
        f"TASK: {spec.label}.",
        spec.focus_for(document_type),
        rules,
        "Also produce 3-5 `related_questions` the reader might ask next about THIS document, and 0-4 "
        "`professional_questions` about gaps, conflicts or unusual terms worth raising with a legal professional.",
        "The `summary` is one plain sentence about what the document does or does not cover for this task.",
    ]
    if repair_feedback:
        parts.append(repair_feedback)
    parts.append(context)
    return "\n\n".join(parts)


def repair_feedback(failed_quotes: list[str]) -> str:
    listed = "\n".join(f'- "{quote}"' for quote in failed_quotes[:10])
    return (
        "IMPORTANT: In a previous attempt the following evidence quotes could NOT be located in the document. "
        "They were paraphrased or invented. Copy quotes character-for-character from the excerpts, or drop the claim "
        "and use NOT_FOUND:\n" + listed
    )
