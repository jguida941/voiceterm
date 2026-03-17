"""Attention-state policy for bridge-backed review-channel projections.

Routing logic lives here; all payload fields (owner, summary, recovery,
recommended_command) are looked up from the canonical ``STALE_PEER_RECOVERY``
contract in ``peer_liveness``.
"""

from __future__ import annotations

from .peer_liveness import (
    CODEX_POLL_OVERDUE_AFTER_SECONDS,
    STALE_PEER_RECOVERY,
    AttentionStatus,
    CodexPollState,
    OverallLivenessState,
    reviewer_mode_is_active,
)


def derive_bridge_attention(bridge_liveness: dict[str, object]) -> dict[str, object]:
    """Translate bridge liveness into one compact operator-facing attention state."""
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    codex_poll_state = str(bridge_liveness.get("codex_poll_state") or "unknown")
    claude_status_present = bool(bridge_liveness.get("claude_status_present"))
    claude_ack_present = bool(bridge_liveness.get("claude_ack_present"))

    reviewed_hash_current = bridge_liveness.get("reviewed_hash_current")
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    poll_age = bridge_liveness.get("last_codex_poll_age_seconds")
    overdue_threshold = bridge_liveness.get(
        "reviewer_overdue_threshold_seconds",
        CODEX_POLL_OVERDUE_AFTER_SECONDS,
    )

    if not reviewer_mode_is_active(reviewer_mode):
        status = AttentionStatus.INACTIVE
    elif codex_poll_state == CodexPollState.MISSING:
        status = AttentionStatus.REVIEWER_HEARTBEAT_MISSING
    elif (
        overall_state == OverallLivenessState.STALE
        and isinstance(poll_age, (int, float))
        and isinstance(overdue_threshold, (int, float))
        and poll_age > overdue_threshold
    ):
        status = AttentionStatus.REVIEWER_OVERDUE
    elif overall_state == OverallLivenessState.STALE:
        status = AttentionStatus.REVIEWER_HEARTBEAT_STALE
    elif codex_poll_state == CodexPollState.POLL_DUE:
        status = AttentionStatus.REVIEWER_POLL_DUE
    elif overall_state == OverallLivenessState.WAITING_ON_PEER and not claude_status_present:
        status = AttentionStatus.CLAUDE_STATUS_MISSING
    elif overall_state == OverallLivenessState.WAITING_ON_PEER and not claude_ack_present:
        status = AttentionStatus.CLAUDE_ACK_MISSING
    elif overall_state == OverallLivenessState.WAITING_ON_PEER:
        status = AttentionStatus.WAITING_ON_PEER
    elif reviewed_hash_current is False:
        status = AttentionStatus.REVIEWED_HASH_STALE
    elif bool(bridge_liveness.get("implementer_completion_stall")):
        status = AttentionStatus.IMPLEMENTER_COMPLETION_STALL
    elif (
        reviewer_mode_is_active(reviewer_mode)
        and not bool(bridge_liveness.get("publisher_running"))
    ):
        stop_reason = str(bridge_liveness.get("publisher_stop_reason") or "")
        if stop_reason == "failed_start":
            status = AttentionStatus.PUBLISHER_FAILED_START
        elif stop_reason == "detached_exit":
            status = AttentionStatus.PUBLISHER_DETACHED_EXIT
        else:
            status = AttentionStatus.PUBLISHER_MISSING
    else:
        status = AttentionStatus.HEALTHY

    return _attention_from_contract(status)


def _attention_from_contract(status: str) -> dict[str, object]:
    """Build an attention payload from the canonical stale-peer recovery contract."""
    entry = STALE_PEER_RECOVERY.get(status, STALE_PEER_RECOVERY[AttentionStatus.HEALTHY])
    return {
        "status": status,
        "owner": entry["owner"],
        "summary": entry["summary"],
        "recommended_action": entry["recovery"],
        "recommended_command": entry.get("recommended_command"),
    }
