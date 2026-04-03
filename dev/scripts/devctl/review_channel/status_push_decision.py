"""Push-decision helpers for review-channel status snapshots."""

from __future__ import annotations

from ..runtime.project_governance_push import push_enforcement_from_mapping
from ..runtime.startup_push_decision import derive_push_decision


def build_status_push_decision(
    *,
    bridge_liveness: dict[str, object],
    reviewer_runtime,
) -> dict[str, object]:
    """Build the current typed push decision from push enforcement plus runtime."""
    push_enforcement_payload = bridge_liveness.get("push_enforcement")
    if not isinstance(push_enforcement_payload, dict):
        return {}
    push_enforcement = push_enforcement_from_mapping(push_enforcement_payload)
    return derive_push_decision(
        push_enforcement,
        review_gate_allows_push=bool(reviewer_runtime.publish_clear),
        implementation_blocked=bool(reviewer_runtime.implementation_blocked),
        implementation_block_reason=str(
            reviewer_runtime.implementation_block_reason or ""
        ),
    ).to_dict()
