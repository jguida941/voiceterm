"""Recovery decision mapping: AttentionStatus → typed recovery action."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_models import RecoveryDecisionState
from .conductor_authority import (
    conductor_signal_present,
    live_reviewer_conductor_present,
)
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
            "relaunch_review_loop",
        },
        requires_approval=action_id in {
            "cut_checkpoint",
            "recover_implementer",
            "rebind_verification_capability",
            "resume_live_review_loop",
        },
        next_expected_state="healthy",
    )


_STATUS_TO_ACTION_ID: Mapping[str, str] = {
    AttentionStatus.HEALTHY.value: "continue_scoped_loop",
    AttentionStatus.INACTIVE.value: "resume_live_review_loop",
    AttentionStatus.RUNTIME_MISSING.value: "ensure_runtime",
    "publisher_missing": "ensure_runtime",
    "publisher_failed_start": "ensure_runtime",
    "publisher_detached_exit": "ensure_runtime",
    AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value: "relaunch_review_loop",
    AttentionStatus.REVIEWER_HEARTBEAT_STALE.value: "relaunch_review_loop",
    AttentionStatus.REVIEWER_OVERDUE.value: "relaunch_review_loop",
    AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value: "relaunch_review_loop",
    AttentionStatus.VERIFICATION_CAPABILITY_MISSING.value: (
        "rebind_verification_capability"
    ),
    AttentionStatus.REVIEWER_POLL_DUE.value: "refresh_review_status",
    AttentionStatus.WAITING_ON_PEER.value: "refresh_review_status",
    AttentionStatus.REVIEWER_SUPERVISOR_REQUIRED.value: "start_reviewer_follow_loop",
    AttentionStatus.CLAUDE_STATUS_MISSING.value: "resume_implementer_work",
    AttentionStatus.IMPLEMENTER_COMPLETION_STALL.value: "resume_implementer_work",
    AttentionStatus.CLAUDE_ACK_MISSING.value: "acknowledge_current_instruction",
    AttentionStatus.CLAUDE_ACK_STALE.value: "acknowledge_current_instruction",
    AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED.value: "reset_implementer_state",
    AttentionStatus.CHECKPOINT_REQUIRED.value: "cut_checkpoint",
    AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED.value: "refresh_reviewer_verdict",
    AttentionStatus.REVIEWED_HASH_STALE.value: "refresh_reviewer_verdict",
    AttentionStatus.DUAL_AGENT_IDLE.value: "start_reviewer_follow_loop",
    AttentionStatus.REVIEWER_COMPLETION_UNRECORDED.value: "cut_checkpoint",
}


def resolve_action_id(*, status: str, ctx) -> str:
    """Return the canonical recovery action ID for the given attention status."""
    if status == AttentionStatus.BRIDGE_CONTRACT_ERROR.value:
        return (
            "render_bridge"
            if can_render_bridge(ctx.bridge_liveness)
            else "refresh_review_status"
        )
    if status == AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value:
        if conductor_signal_present(
            ctx.bridge_liveness
        ) and not live_reviewer_conductor_present(ctx.bridge_liveness):
            return "relaunch_review_loop"
        return "recover_implementer"
    return _STATUS_TO_ACTION_ID.get(status, "refresh_review_status")


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
    if status == AttentionStatus.VERIFICATION_CAPABILITY_MISSING.value:
        return ("relaunch_provider_pair_for_verification_gap",)
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
