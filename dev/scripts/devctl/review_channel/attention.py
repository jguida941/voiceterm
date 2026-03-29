"""Attention-state policy for bridge-backed review-channel projections.

Routing logic and constants live in ``attention_classify``; all payload fields
(owner, summary, recovery, recommended_command) are looked up from the
canonical ``STALE_PEER_RECOVERY`` contract in ``peer_liveness``.
"""

from __future__ import annotations

from .attention_classify import (
    classify_attention_status,
    extract_attention_context,
)
from .peer_liveness import (
    STALE_PEER_RECOVERY,
    AttentionStatus,
)


def derive_bridge_attention(
    bridge_liveness: dict[str, object],
    *,
    push_state: dict[str, object] | None = None,
    contract_errors: list[str] | None = None,
) -> dict[str, object]:
    """Translate bridge liveness into one compact operator-facing attention state."""
    ctx = extract_attention_context(
        bridge_liveness,
        push_state=push_state,
        contract_errors=contract_errors,
    )
    return _attention_from_contract(classify_attention_status(ctx))


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
