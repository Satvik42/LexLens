"""Lexical clause retrieval: select the clauses most relevant to an operation or question.

Keeps model context targeted instead of sending the whole document on every request. Small documents that fit
the budget are sent in full (retrieval would only remove context without saving anything).
"""

import math
import re

from app.schemas.document import Clause
from app.services.text_utils import tokenize

DEFAULT_CHAR_BUDGET = 14_000
_MIN_CLAUSES = 3

# Small legal synonym map so plain-language questions reach the right clauses.
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "resign": ("resignation", "terminate", "termination", "notice"),
    "quit": ("resign", "resignation", "terminate", "notice"),
    "leave": ("resign", "termination", "notice", "leave"),
    "fired": ("terminate", "termination", "cause", "dismiss"),
    "notice": ("notice", "terminate", "termination"),
    "stock": ("stock", "equity", "shares", "option", "esop", "vest"),
    "options": ("option", "equity", "shares", "esop", "vest"),
    "equity": ("equity", "shares", "stock", "option", "esop"),
    "salary": ("salary", "compensation", "ctc", "remuneration", "pay"),
    "pay": ("pay", "payment", "salary", "fee", "compensation"),
    "bonus": ("bonus", "incentive", "variable"),
    "rent": ("rent", "deposit", "payment"),
    "deposit": ("deposit", "security", "refund"),
    "penalty": ("penalty", "liquidated", "damages", "forfeit", "bond", "repay"),
    "bond": ("bond", "repay", "repayment", "training"),
    "compete": ("compete", "non-compete", "competitor", "restrict"),
    "confidential": ("confidential", "confidentiality", "disclose"),
    "ip": ("intellectual", "property", "invention", "assign"),
    "holiday": ("leave", "vacation", "holiday"),
    "work": ("hours", "working", "remote", "location"),
    "remote": ("remote", "location", "place of work", "work from home"),
    "probation": ("probation", "probationary", "confirm"),
}


def expand_terms(query: str) -> list[str]:
    tokens = tokenize(query)
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        expanded.extend(_SYNONYMS.get(token, ()))
    return list(dict.fromkeys(expanded))


def _score(clause_text: str, terms: list[str]) -> float:
    lowered = clause_text.lower()
    score = 0.0
    for term in terms:
        hits = len(re.findall(re.escape(term), lowered))
        if hits:
            score += 1.0 + math.log1p(hits)
    length_penalty = math.log(len(lowered) + 50)
    return score / length_penalty if score else 0.0


def select_clauses(clauses: list[Clause], terms: list[str], char_budget: int = DEFAULT_CHAR_BUDGET) -> list[Clause]:
    """Return relevant clauses in document order within the character budget."""
    total_chars = sum(len(c.text) for c in clauses)
    if total_chars <= char_budget or not terms:
        return _trim_to_budget(clauses, char_budget)

    ranked = sorted(clauses, key=lambda c: _score(c.text, terms), reverse=True)
    selected: list[Clause] = []
    used = 0
    for clause in ranked:
        if len(selected) >= _MIN_CLAUSES and _score(clause.text, terms) == 0:
            break
        if used + len(clause.text) > char_budget:
            continue
        selected.append(clause)
        used += len(clause.text)
    return sorted(selected, key=lambda c: (c.page_number, c.start))


def _trim_to_budget(clauses: list[Clause], char_budget: int) -> list[Clause]:
    selected: list[Clause] = []
    used = 0
    for clause in clauses:
        if used + len(clause.text) > char_budget:
            break
        selected.append(clause)
        used += len(clause.text)
    return selected
