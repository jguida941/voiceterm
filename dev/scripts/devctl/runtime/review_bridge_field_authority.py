"""Authority taxonomy for event-backed ReviewBridgeState projection fields."""

from __future__ import annotations

EVENT_BRIDGE_CANONICAL_FIELDS = frozenset({
    "overall_state",
    "codex_poll_state",
    "reviewer_freshness",
    "reviewer_mode",
    "last_codex_poll_utc",
    "last_codex_poll_age_seconds",
    "current_instruction",
    "open_findings",
    "claude_status",
    "claude_ack",
    "last_reviewed_scope",
    "publisher_running",
    "codex_conductor_active",
    "claude_conductor_active",
    "head_at_push_time",
})

EVENT_BRIDGE_COMPATIBILITY_DERIVED_FIELDS = frozenset({
    "launch_truth",
    "effective_reviewer_mode",
    "implementer_state_hash",
    "implementer_completion_stall",
    "reviewer_capability",
    "implementer_capability",
})

EVENT_BRIDGE_SYNTHETIC_FAIL_CLOSED_FIELDS = frozenset({
    "last_worktree_hash",
    "claude_ack_current",
    "current_instruction_revision",
    "claude_ack_revision",
    "reviewed_hash_current",
    "review_needed",
    "review_accepted",
})

EVENT_BRIDGE_CLASSIFIED_FIELDS = (
    EVENT_BRIDGE_CANONICAL_FIELDS
    | EVENT_BRIDGE_COMPATIBILITY_DERIVED_FIELDS
    | EVENT_BRIDGE_SYNTHETIC_FAIL_CLOSED_FIELDS
)


def event_bridge_field_authority(field_name: str) -> str:
    """Return the declared authority level for one event-backed bridge field."""
    if field_name in EVENT_BRIDGE_CANONICAL_FIELDS:
        return "canonical_runtime"
    if field_name in EVENT_BRIDGE_COMPATIBILITY_DERIVED_FIELDS:
        return "compatibility_derived"
    if field_name in EVENT_BRIDGE_SYNTHETIC_FAIL_CLOSED_FIELDS:
        return "synthetic_fail_closed"
    raise KeyError(f"Unclassified event bridge field: {field_name}")


def event_bridge_roundtrip_required_fields() -> frozenset[str]:
    """Return fields that must preserve meaning through parser round-trip."""
    return EVENT_BRIDGE_CLASSIFIED_FIELDS
