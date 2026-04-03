"""Push-decision helpers for review-channel status snapshots."""

from __future__ import annotations

from ..runtime.project_governance_push import push_enforcement_from_mapping
from ..runtime.reviewer_gate_logic import reviewer_loop_block_state
from ..runtime.startup_push_decision import derive_push_decision


def build_status_push_decision(
    *,
    bridge_liveness: dict[str, object],
    attention: dict[str, object],
    current_session,
    reviewer_runtime,
) -> dict[str, object]:
    """Build the current typed push decision from bridge and reviewer state."""
    push_enforcement_payload = bridge_liveness.get("push_enforcement")
    if not isinstance(push_enforcement_payload, dict):
        return {}
    push_enforcement = push_enforcement_from_mapping(push_enforcement_payload)
    implementation_blocked, implementation_block_reason = reviewer_loop_block_state(
        reviewer_mode=str(bridge_liveness.get("reviewer_mode") or ""),
        claude_ack_current=bool(bridge_liveness.get("claude_ack_current")),
        attention_status=str(attention.get("status") or ""),
        implementer_status=str(current_session.implementer_status or "").strip(),
        implementer_ack=str(current_session.implementer_ack or "").strip(),
        implementer_ack_state=str(current_session.implementer_ack_state or "").strip(),
    )
    return derive_push_decision(
        push_enforcement,
        review_gate_allows_push=bool(reviewer_runtime.publish_clear),
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
    ).to_dict()
