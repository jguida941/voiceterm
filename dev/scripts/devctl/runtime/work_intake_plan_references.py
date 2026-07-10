"""Review-scope plan-reference checks for startup work-intake."""

from __future__ import annotations

import re

from .project_governance import PlanRegistryEntry
from .review_state_models import ReviewState

_MP_TOKEN_RE = re.compile(r"\bMP-\d+\b", re.IGNORECASE)


def unresolved_review_scope_plan_references(
    entries: tuple[PlanRegistryEntry, ...],
    review_state: ReviewState | None,
) -> tuple[str, ...]:
    if review_state is None:
        return ()
    scope_tokens = _extract_mp_tokens(
        review_state.current_session.last_reviewed_scope
    )
    if not scope_tokens:
        return ()

    known_tokens: set[str] = set()
    for entry in entries:
        known_tokens.update(_extract_mp_tokens(entry.path))
        known_tokens.update(_extract_mp_tokens(entry.title))
        known_tokens.update(_extract_mp_tokens(entry.scope))
        known_tokens.update(_extract_mp_tokens(entry.authority))
    return tuple(token.upper() for token in sorted(scope_tokens - known_tokens))


def _extract_mp_tokens(text: str) -> set[str]:
    if not text:
        return set()
    return {match.group(0).casefold() for match in _MP_TOKEN_RE.finditer(text)}


__all__ = ["unresolved_review_scope_plan_references"]
