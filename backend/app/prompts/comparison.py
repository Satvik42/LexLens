"""Prompt builder for evidence-backed document comparison."""

from app.prompts.system import wrap_untrusted

_COMPARE_RULES = """TASK: Compare two versions of a document term by term.

- Produce one row per meaningful term (notice period, compensation, duration, restrictions, termination, payment,
  renewal, liability, etc.). Aim for 6-14 rows covering the most decision-relevant terms.
- `original_value` / `updated_value`: the concrete value in each document, or null when that document does not state it.
- `change`: CHANGED (both present, different), NEW (only in updated), REMOVED (only in original), UNCHANGED (same).
- For every non-null value give 1-2 verbatim quotes from the corresponding document with its page/section.
- Never merge quotes across documents. Never infer a value the document does not state.
- `note`: optional one-sentence plain-language description of the practical difference.
- `summary`: one or two sentences describing the overall nature of the changes.
"""


def build_comparison_prompt(original_context: str, updated_context: str) -> str:
    return "\n\n".join(
        [
            _COMPARE_RULES,
            "ORIGINAL DOCUMENT:\n" + wrap_untrusted("original", original_context),
            "UPDATED DOCUMENT:\n" + wrap_untrusted("updated", updated_context),
        ]
    )
