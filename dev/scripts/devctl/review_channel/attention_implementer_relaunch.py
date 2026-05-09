"""Implementer relaunch attention classifier."""

from __future__ import annotations

from .attention_helpers import RESETTABLE_IMPLEMENTER_SESSION_STATES
from .conductor_authority import live_implementer_conductor_present
from .peer_liveness import AttentionStatus, CodexPollState, OverallLivenessState


def classify_implementer_relaunch(ctx) -> str | None:
    """Classify fresh-poll implementer relaunch and idle states."""
    if not _fresh_poll(ctx) or ctx.review_needed:
        return None
    if (
        ctx.overall_state == OverallLivenessState.WAITING_ON_PEER
        and not live_implementer_conductor_present(ctx.bridge_liveness)
        and ctx.implementer_state_pending
    ):
        return AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED
    if (
        ctx.overall_state == OverallLivenessState.WAITING_ON_PEER
        and not live_implementer_conductor_present(ctx.bridge_liveness)
        and (not ctx.claude_status_present or not ctx.claude_ack_present)
    ):
        return AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED
    if (
        ctx.overall_state == OverallLivenessState.WAITING_ON_PEER
        and ctx.implementer_completion_stall
        and (not ctx.claude_ack_present or not ctx.claude_ack_current)
    ):
        return AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED
    if (
        ctx.overall_state == OverallLivenessState.WAITING_ON_PEER
        and not ctx.implementer_state_pending
        and ctx.session_hint_state in RESETTABLE_IMPLEMENTER_SESSION_STATES
        and (not ctx.claude_status_present or not ctx.claude_ack_current)
    ):
        return AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED
    if ctx.implementer_completion_stall and ctx.claude_ack_current:
        return AttentionStatus.DUAL_AGENT_IDLE
    return None


def _fresh_poll(ctx) -> bool:
    return ctx.codex_poll_state in {CodexPollState.FRESH, CodexPollState.POLL_DUE}
