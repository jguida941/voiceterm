"""Recovery decision mapping: AttentionStatus → typed recovery action."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_models import RecoveryDecisionState
from .peer_liveness import AttentionStatus
from .peer_recovery import (
    REVIEW_CHANNEL_GOVERNED_CHECKPOINT_COMMAND,
    REVIEW_CHANNEL_RENDER_BRIDGE_COMMAND,
    build_implementer_recover_command,
    build_live_relaunch_command,
)


def build_decision_state(
    *,
    status: str,
    ctx,
    operator_interaction_mode: str,
    recovery_entry: Mapping[str, object],
) -> RecoveryDecisionState:
    """Map an attention status to a fully typed recovery decision."""
    action_id = resolve_action_id(status=status, ctx=ctx)
    command = resolve_command(
        status=status,
        ctx=ctx,
        action_id=action_id,
        default=str(recovery_entry.get("recommended_command") or ""),
        operator_interaction_mode=operator_interaction_mode,
    )
    return RecoveryDecisionState(
        action_id=action_id,
        command=command,
        execution_owner=str(recovery_entry.get("owner") or ""),
        rationale=str(recovery_entry.get("recovery") or ""),
        blocked_alternatives=resolve_blocked_alternatives(status=status),
        can_auto_fix=action_id in {
            "ensure_runtime",
            "render_bridge",
            "reset_implementer_state",
            "refresh_review_status",
        },
        requires_approval=action_id in {
            "cut_checkpoint",
            "relaunch_review_loop",
            "recover_implementer",
            "resume_live_review_loop",
        },
        next_expected_state="healthy",
    )


def resolve_action_id(*, status: str, ctx) -> str:
    """Return the canonical recovery action ID for the given attention status."""
    if status == AttentionStatus.HEALTHY.value:
        return "continue_scoped_loop"
    if status == AttentionStatus.INACTIVE.value:
        return "resume_live_review_loop"
    if status in {
        AttentionStatus.RUNTIME_MISSING.value,
        "publisher_missing",
        "publisher_failed_start",
        "publisher_detached_exit",
    }:
        return "ensure_runtime"
    if status in {
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE.value,
        AttentionStatus.REVIEWER_OVERDUE.value,
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
    }:
        return "relaunch_review_loop"
    if status in {
        AttentionStatus.REVIEWER_POLL_DUE.value,
        AttentionStatus.WAITING_ON_PEER.value,
    }:
        return "refresh_review_status"
    if status == AttentionStatus.BRIDGE_CONTRACT_ERROR.value:
        return (
            "render_bridge"
            if can_render_bridge(ctx.bridge_liveness)
            else "refresh_review_status"
        )
    if status == AttentionStatus.REVIEWER_SUPERVISOR_REQUIRED.value:
        return "start_reviewer_follow_loop"
    if status in {
        AttentionStatus.CLAUDE_STATUS_MISSING.value,
        AttentionStatus.IMPLEMENTER_COMPLETION_STALL.value,
    }:
        return "resume_implementer_work"
    if status in {
        AttentionStatus.CLAUDE_ACK_MISSING.value,
        AttentionStatus.CLAUDE_ACK_STALE.value,
    }:
        return "acknowledge_current_instruction"
    if status == AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED.value:
        return "reset_implementer_state"
    if status == AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value:
        return "recover_implementer"
    if status == AttentionStatus.CHECKPOINT_REQUIRED.value:
        return "cut_checkpoint"
    if status in {
        AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value,
        AttentionStatus.REVIEWED_HASH_STALE.value,
    }:
        return "refresh_reviewer_verdict"
    if status == AttentionStatus.DUAL_AGENT_IDLE.value:
        return "start_reviewer_follow_loop"
    if status == AttentionStatus.REVIEWER_COMPLETION_UNRECORDED.value:
        return "cut_checkpoint"
    return "refresh_review_status"


def resolve_command(
    *,
    status: str,
    ctx,
    action_id: str,
    default: str,
    operator_interaction_mode: str,
) -> str:
    """Return the shell command for the resolved recovery action."""
    if action_id == "cut_checkpoint":
        return REVIEW_CHANNEL_GOVERNED_CHECKPOINT_COMMAND
    if action_id == "relaunch_review_loop":
        return build_live_relaunch_command(operator_interaction_mode)
    if action_id == "recover_implementer":
        return build_implementer_recover_command(operator_interaction_mode)
    if status == AttentionStatus.BRIDGE_CONTRACT_ERROR.value and can_render_bridge(
        ctx.bridge_liveness
    ):
        return REVIEW_CHANNEL_RENDER_BRIDGE_COMMAND
    return default.strip()


def resolve_blocked_alternatives(*, status: str) -> tuple[str, ...]:
    """Return blocked-alternative labels for the given attention status."""
    if status == AttentionStatus.HEALTHY.value:
        return ()
    if status == AttentionStatus.CHECKPOINT_REQUIRED.value:
        return ("continue_editing_without_checkpoint",)
    if status in {
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE.value,
        AttentionStatus.REVIEWER_OVERDUE.value,
    }:
        return ("treat_detached_or_stale_runtime_as_live",)
    if status == AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED.value:
        return ("launch_or_recover_claude_without_clearing_stale_state",)
    if status == AttentionStatus.BRIDGE_CONTRACT_ERROR.value:
        return ("trust_inconsistent_bridge_sections",)
    if status in {
        AttentionStatus.CLAUDE_ACK_MISSING.value,
        AttentionStatus.CLAUDE_ACK_STALE.value,
    }:
        return ("continue_coding_without_current_ack",)
    if status in {
        AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value,
        AttentionStatus.REVIEWED_HASH_STALE.value,
    }:
        return ("promote_next_slice_without_refreshing_review",)
    if status == AttentionStatus.REVIEWER_COMPLETION_UNRECORDED.value:
        return ("treat_heartbeat_acceptance_as_valid_checkpoint",)
    return ("ignore_recovery_signal",)


def can_render_bridge(bridge_liveness: Mapping[str, object]) -> bool:
    """Return True when at least one conductor is active and can render bridge."""
    return bool(bridge_liveness.get("codex_conductor_active")) or bool(
        bridge_liveness.get("claude_conductor_active")
    )
