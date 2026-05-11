"""Shared reviewer-gate decision helpers for startup and review consumers."""

from __future__ import annotations

from dataclasses import dataclass

from .reviewer_mode import reviewer_mode_is_active
from .review_state_semantics import is_pending_implementer_state


@dataclass(frozen=True, slots=True)
class ReviewerRuntimeBlockInputs:
    reviewer_mode: str
    effective_reviewer_mode: str = ""
    implementer_ack_current: bool = False
    attention_status: str = ""
    current_instruction: str = ""
    implementer_status: str = ""
    implementer_ack: str = ""
    implementer_ack_state: str = ""


def reviewer_loop_block_state(
    inputs: ReviewerRuntimeBlockInputs,
) -> tuple[bool, str]:
    """Return whether the active reviewer loop is blocked on implementer state."""
    if not reviewer_mode_is_active(inputs.reviewer_mode):
        return False, ""
    if str(inputs.current_instruction or "").strip() in {"", "(missing)"}:
        return False, ""
    ack_state = str(inputs.implementer_ack_state or "").strip().lower()
    if ack_state == "current":
        return False, ""
    if ack_state in {"pending", "reset"}:
        return False, ""
    if inputs.implementer_ack_current:
        return False, ""
    if is_pending_implementer_state(
        implementer_status=inputs.implementer_status,
        implementer_ack=inputs.implementer_ack,
        implementer_ack_state=inputs.implementer_ack_state,
    ):
        return False, ""
    reason = inputs.attention_status or "claude_ack_stale"
    return True, reason


def reviewer_runtime_block_state(
    inputs: ReviewerRuntimeBlockInputs,
) -> tuple[bool, str]:
    """Return the typed reviewer-runtime implementation block state."""
    if not reviewer_mode_is_active(inputs.reviewer_mode):
        return False, ""
    effective_mode = inputs.effective_reviewer_mode or inputs.reviewer_mode
    if not reviewer_mode_is_active(effective_mode):
        return True, inputs.attention_status or "review_loop_not_live"
    return reviewer_loop_block_state(
        ReviewerRuntimeBlockInputs(
            reviewer_mode=effective_mode,
            effective_reviewer_mode=effective_mode,
            implementer_ack_current=inputs.implementer_ack_current,
            attention_status=inputs.attention_status,
            current_instruction=inputs.current_instruction,
            implementer_status=inputs.implementer_status,
            implementer_ack=inputs.implementer_ack,
            implementer_ack_state=inputs.implementer_ack_state,
        )
    )
