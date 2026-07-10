"""Continuity reconciliation helpers for startup work-intake."""

from __future__ import annotations

import re

from .project_governance import PlanRegistryEntry
from .review_state_models import ReviewState
from .work_intake_models import SessionContinuityState

_MP_TOKEN_RE = re.compile(r"\bMP-\d+\b", re.IGNORECASE)
# Token-set Jaccard threshold for instruction-level fuzzy match. Tuned to
# accept short paraphrases of the plan's current goal while rejecting
# drive-by substring hits from unrelated review prose.
_JACCARD_THRESHOLD = 0.4


def build_continuity(
    entry: PlanRegistryEntry | None,
    review_state: ReviewState | None,
) -> SessionContinuityState:
    """Reconcile selected plan continuity against live review state."""
    session_resume = entry.session_resume if entry is not None else None
    review_scope, review_instruction, review_open_findings, implementer_status = (
        _review_texts(review_state)
    )

    if session_resume is None and review_state is None:
        return SessionContinuityState(
            alignment_status="missing",
            alignment_reason="no_plan_resume_or_review_state",
        )
    unresolved_plan_references = _extract_mp_token_labels(review_scope)
    if session_resume is None and entry is None and unresolved_plan_references:
        return SessionContinuityState(
            review_scope=review_scope,
            review_instruction=review_instruction,
            review_open_findings=review_open_findings,
            implementer_status=implementer_status,
            alignment_status="needs_review",
            alignment_reason="unresolved_review_plan_reference",
            unresolved_plan_references=unresolved_plan_references,
        )
    if session_resume is None:
        return SessionContinuityState(
            source_plan_path=entry.path if entry is not None else "",
            source_plan_title=entry.title if entry is not None else "",
            source_scope=entry.scope if entry is not None else "",
            review_scope=review_scope,
            review_instruction=review_instruction,
            review_open_findings=review_open_findings,
            implementer_status=implementer_status,
            alignment_status="review_only",
            alignment_reason="no_plan_session_resume",
        )
    if review_state is None:
        return SessionContinuityState(
            source_plan_path=entry.path if entry is not None else "",
            source_plan_title=entry.title if entry is not None else "",
            source_scope=entry.scope if entry is not None else "",
            summary=_brief_text(session_resume.summary, limit=240),
            current_goal=_brief_text(session_resume.current_goal, limit=200),
            next_action=_brief_text(session_resume.next_action, limit=240),
            alignment_status="plan_only",
            alignment_reason="no_typed_review_state",
        )

    # A non-None ReviewState whose scope AND instruction are both empty is
    # shaped the same as `review_state is None` from the continuity lens.
    # Collapsing to `needs_review` would falsely blame the plan. Classify
    # as `plan_only` so downstream confidence stays on the plan surface.
    if not review_scope.strip() and not review_instruction.strip():
        return SessionContinuityState(
            source_plan_path=entry.path if entry is not None else "",
            source_plan_title=entry.title if entry is not None else "",
            source_scope=entry.scope if entry is not None else "",
            summary=_brief_text(session_resume.summary, limit=240),
            current_goal=_brief_text(session_resume.current_goal, limit=200),
            next_action=_brief_text(session_resume.next_action, limit=240),
            review_scope=review_scope,
            review_instruction=review_instruction,
            review_open_findings=review_open_findings,
            implementer_status=implementer_status,
            alignment_status="plan_only",
            alignment_reason="empty_review_state",
        )

    alignment_status, alignment_reason = _alignment_result(
        entry,
        review_scope=review_scope,
        review_instruction=review_instruction,
    )
    return SessionContinuityState(
        source_plan_path=entry.path if entry is not None else "",
        source_plan_title=entry.title if entry is not None else "",
        source_scope=entry.scope if entry is not None else "",
        summary=_brief_text(session_resume.summary, limit=240),
        current_goal=_brief_text(session_resume.current_goal, limit=200),
        next_action=_brief_text(session_resume.next_action, limit=240),
        review_scope=review_scope,
        review_instruction=review_instruction,
        review_open_findings=review_open_findings,
        implementer_status=implementer_status,
        alignment_status=alignment_status,
        alignment_reason=alignment_reason,
    )


def confidence(
    *,
    active_entry: PlanRegistryEntry | None,
    review_state: ReviewState | None,
    continuity: SessionContinuityState,
) -> tuple[str, str]:
    """Return startup confidence and fallback reason for the intake packet."""
    if continuity.alignment_reason == "unresolved_review_plan_reference":
        return "low", "unresolved_review_plan_reference"
    if active_entry is None:
        return "low", "no_plan_registry_target"
    if continuity.alignment_status in {"aligned", "scope_aligned", "instruction_aligned"}:
        return "high", ""
    if continuity.alignment_status == "plan_only":
        return "medium", "no_review_state"
    if review_state is None:
        return "medium", "tracker_fallback_without_review_state"
    if continuity.alignment_status == "needs_review":
        return "medium", "plan_review_mismatch"
    return "medium", ""


def _review_texts(review_state: ReviewState | None) -> tuple[str, str, str, str]:
    if review_state is None:
        return "", "", "", ""
    return (
        _brief_text(review_state.current_session.last_reviewed_scope, limit=200),
        _brief_text(review_state.current_session.current_instruction, limit=240),
        _brief_text(review_state.current_session.open_findings, limit=160),
        _brief_text(review_state.current_session.implementer_status, limit=200),
    )


def _alignment_result(
    entry: PlanRegistryEntry | None,
    *,
    review_scope: str,
    review_instruction: str,
) -> tuple[str, str]:
    if entry is None or entry.session_resume is None:
        return "missing", "no_plan_target"

    scope_match = _scope_match(review_scope, entry.scope) or _scope_match(
        review_scope, entry.title
    )
    instruction_match = any(
        _instruction_match(review_instruction, candidate)
        for candidate in (
            entry.session_resume.next_action,
            entry.session_resume.current_goal,
            entry.session_resume.summary,
        )
        if candidate
    )
    if scope_match and instruction_match:
        return "aligned", "scope_and_instruction_match"
    if scope_match:
        return "scope_aligned", "review_scope_matches_plan_target"
    if instruction_match:
        return "instruction_aligned", "review_instruction_matches_session_resume"
    return "needs_review", "plan_review_mismatch"


def _scope_match(left: str, right: str) -> bool:
    """Compare scope fields with MP-token priority, then Jaccard fallback."""
    lhs_tokens = _extract_mp_tokens(left)
    rhs_tokens = _extract_mp_tokens(right)
    # If either side advertises MP identifiers, those are the only signal
    # that matters. `MP-3` must not absorb `MP-377` via substring leniency.
    if lhs_tokens and rhs_tokens:
        return bool(lhs_tokens & rhs_tokens)
    if lhs_tokens or rhs_tokens:
        return False
    return _token_set_similarity(left, right) >= _JACCARD_THRESHOLD


def _instruction_match(left: str, right: str) -> bool:
    """Compare instruction strings with MP-token priority, then Jaccard."""
    lhs_tokens = _extract_mp_tokens(left)
    rhs_tokens = _extract_mp_tokens(right)
    if lhs_tokens and rhs_tokens and lhs_tokens & rhs_tokens:
        return True
    return _token_set_similarity(left, right) >= _JACCARD_THRESHOLD


def _extract_mp_tokens(text: str) -> frozenset[str]:
    """Return the casefolded set of `MP-<digits>` identifiers in ``text``."""
    if not text:
        return frozenset()
    return frozenset(match.group(0).casefold() for match in _MP_TOKEN_RE.finditer(text))


def _extract_mp_token_labels(text: str) -> tuple[str, ...]:
    if not text:
        return ()
    tokens = {match.group(0).upper() for match in _MP_TOKEN_RE.finditer(text)}
    return tuple(sorted(tokens))


def _token_set_similarity(left: str, right: str) -> float:
    """Jaccard similarity over casefolded whitespace tokens (length >= 2)."""
    lhs = _word_tokens(left)
    rhs = _word_tokens(right)
    if not lhs or not rhs:
        return 0.0
    intersection = lhs & rhs
    if not intersection:
        return 0.0
    union = lhs | rhs
    return len(intersection) / len(union)


def _word_tokens(value: str) -> frozenset[str]:
    """Cheap word-tokenizer for fuzzy instruction comparison."""
    if not value:
        return frozenset()
    return frozenset(
        token for token in re.findall(r"[A-Za-z0-9]+", value.casefold()) if len(token) > 1
    )


def _brief_text(value: str, *, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: max(limit - 3, 0)].rstrip()}..."


__all__ = ["build_continuity", "confidence"]
