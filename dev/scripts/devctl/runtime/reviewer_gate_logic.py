"""Shared reviewer-gate decision helpers for startup and review consumers."""

from __future__ import annotations

from dataclasses import dataclass

from .conductor_capability import normalize_reviewer_mode
from .review_state_semantics import is_pending_implementer_state


def reviewer_loop_block_state(
    *,
    reviewer_mode: str,
    claude_ack_current: bool,
    attention_status: str = "",
    implementer_status: str = "",
    implementer_ack: str = "",
    implementer_ack_state: str = "",
) -> tuple[bool, str]:
    """Return whether the active reviewer loop is blocked on implementer state."""
    if normalize_reviewer_mode(reviewer_mode) != "active_dual_agent":
        return False, ""
    if claude_ack_current:
        return False, ""
    if is_pending_implementer_state(
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_state=implementer_ack_state,
    ):
        return False, ""
    reason = attention_status or "claude_ack_stale"
    return True, reason


@dataclass(frozen=True, slots=True)
class ReviewerRuntimeBlockInputs:
    reviewer_mode: str
    effective_reviewer_mode: str = ""
    implementer_ack_current: bool = False
    attention_status: str = ""
    implementer_status: str = ""
    implementer_ack: str = ""
    implementer_ack_state: str = ""


def reviewer_runtime_block_state(
    inputs: ReviewerRuntimeBlockInputs,
) -> tuple[bool, str]:
    """Return the typed reviewer-runtime implementation block state."""
    if normalize_reviewer_mode(inputs.reviewer_mode) != "active_dual_agent":
        return False, ""
    effective_mode = normalize_reviewer_mode(
        inputs.effective_reviewer_mode or inputs.reviewer_mode
    )
    if effective_mode != "active_dual_agent":
        return True, inputs.attention_status or "review_loop_not_live"
    return reviewer_loop_block_state(
        reviewer_mode=effective_mode,
        claude_ack_current=inputs.implementer_ack_current,
        attention_status=inputs.attention_status,
        implementer_status=inputs.implementer_status,
        implementer_ack=inputs.implementer_ack,
        implementer_ack_state=inputs.implementer_ack_state,
    )
