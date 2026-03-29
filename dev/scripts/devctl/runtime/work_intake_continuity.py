"""Continuity reconciliation helpers for startup work-intake."""

from __future__ import annotations

from .project_governance import PlanRegistryEntry
from .review_state_models import ReviewState
from .work_intake_models import SessionContinuityState


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

    scope_match = _text_overlap(review_scope, entry.scope)
    scope_match = scope_match or _text_overlap(review_scope, entry.title)
    instruction_match = any(
        _text_overlap(review_instruction, candidate)
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


def _text_overlap(left: str, right: str) -> bool:
    lhs = _normalize(left)
    rhs = _normalize(right)
    if not lhs or not rhs:
        return False
    return lhs == rhs or lhs in rhs or rhs in lhs


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _brief_text(value: str, *, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: max(limit - 3, 0)].rstrip()}..."


__all__ = ["build_continuity", "confidence"]
