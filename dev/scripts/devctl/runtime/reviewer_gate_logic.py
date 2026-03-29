"""Shared reviewer-gate decision helpers for startup and review consumers."""

from __future__ import annotations

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
    from ..review_channel.peer_liveness import reviewer_mode_is_active

    if not reviewer_mode_is_active(reviewer_mode):
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
