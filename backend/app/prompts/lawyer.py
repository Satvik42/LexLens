"""Prompt builder for 'Prepare for a Lawyer'."""

from app.prompts.system import wrap_untrusted

_LAWYER_RULES = """TASK: Prepare 5-8 specific questions the reader may want to clarify with a legal professional.

Base the questions on:
- clauses that are present but restrictive, one-sided or unusual,
- information the document does not provide (gaps),
- clauses that appear to conflict with one another,
- the prior analysis notes supplied below.

For each question give a one-sentence `reason` and, where a clause motivates it, 1-2 verbatim evidence quotes.
Questions must be specific to THIS document (mention the actual term, e.g. "the ₹2,00,000 training bond"),
phrased in plain language, and must not assume a legal conclusion. Order by importance.
"""


def build_lawyer_prompt(context: str, prior_notes: list[str]) -> str:
    parts = [_LAWYER_RULES]
    if prior_notes:
        parts.append("Prior analysis notes (untrusted, derived from the document):\n" + wrap_untrusted("notes", "\n".join(f"- {n}" for n in prior_notes)))
    parts.append(context)
    return "\n\n".join(parts)
