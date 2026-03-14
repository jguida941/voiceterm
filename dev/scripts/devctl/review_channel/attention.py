"""Attention-state policy for bridge-backed review-channel projections.

Routing logic lives here; all payload fields (owner, summary, recovery,
recommended_command) are looked up from the canonical ``STALE_PEER_RECOVERY``
contract in ``peer_liveness``.
"""

from __future__ import annotations

from .peer_liveness import (
    STALE_PEER_RECOVERY,
    AttentionStatus,
    CodexPollState,
    OverallLivenessState,
)


def derive_bridge_attention(bridge_liveness: dict[str, object]) -> dict[str, object]:
    """Translate bridge liveness into one compact operator-facing attention state."""
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    codex_poll_state = str(bridge_liveness.get("codex_poll_state") or "unknown")
    claude_status_present = bool(bridge_liveness.get("claude_status_present"))
    claude_ack_present = bool(bridge_liveness.get("claude_ack_present"))

    if codex_poll_state == CodexPollState.MISSING:
        status = AttentionStatus.REVIEWER_HEARTBEAT_MISSING
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
