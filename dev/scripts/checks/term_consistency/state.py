"""State analysis for the term-consistency review probe."""

from __future__ import annotations

from dataclasses import dataclass
import re

if __package__:
    from .config import TermRule
else:  # pragma: no cover - direct module loading in tests
    from config import TermRule


@dataclass(frozen=True, slots=True)
class RuleState:
    canonical_count: int
    alias_counts: dict[str, int]
    found_terms: dict[str, int]
    debt_score: int


@dataclass(frozen=True, slots=True)
class RuleDelta:
    status: str
    before: RuleState
    after: RuleState


def _term_count(text: str | None, term: str) -> int:
    if not text:
        return 0
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", re.IGNORECASE)
    return len(pattern.findall(text))


def _mixed_term_debt(found_terms: dict[str, int]) -> int:
    if len(found_terms) < 2:
        return 0
    total = sum(found_terms.values())
    dominant = max(found_terms.values(), default=0)
    return total - dominant


def analyze_text(text: str | None, rule: TermRule) -> RuleState:
    canonical_count = _term_count(text, rule.canonical)
    alias_counts = {alias: _term_count(text, alias) for alias in rule.aliases}
    found_terms: dict[str, int] = {}
    if canonical_count > 0:
        found_terms[rule.canonical] = canonical_count
    for alias, count in alias_counts.items():
        if count > 0:
            found_terms[alias] = count
    debt_score = (
        sum(alias_counts.values())
        if rule.match_mode == "prefer_canonical"
        else _mixed_term_debt(found_terms)
    )
    return RuleState(
        canonical_count=canonical_count,
        alias_counts=alias_counts,
        found_terms=found_terms,
        debt_score=debt_score,
    )


def classify_delta(before: RuleState, after: RuleState) -> RuleDelta:
    if before.debt_score == 0 and after.debt_score == 0:
        status = "clean"
    elif before.debt_score == 0 and after.debt_score > 0:
        status = "introduced"
    elif after.debt_score > before.debt_score:
        status = "worsened"
    elif after.debt_score < before.debt_score and after.debt_score > 0:
        status = "improved"
    elif after.debt_score == 0 and before.debt_score > 0:
        status = "resolved"
    else:
        status = "unchanged"
    return RuleDelta(status=status, before=before, after=after)
