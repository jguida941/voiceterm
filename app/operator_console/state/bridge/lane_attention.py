"""Attention-to-lane health helpers for the Operator Console."""

from __future__ import annotations


def attention_status_hint(attention_status: str | None) -> str | None:
    """Map review attention into the lane health levels used by the UI."""
    if not attention_status or attention_status == "healthy":
        return None
    if attention_status in {
        "reviewer_heartbeat_missing",
        "reviewer_heartbeat_stale",
    }:
        return "stale"
    return "warning"


def prefer_status_hint(primary: str, override: str | None) -> str:
    """Keep the higher-severity lane status when attention degrades the loop."""
    if override is None:
        return primary
    rank = {"idle": 0, "active": 1, "warning": 2, "stale": 3}
    if rank.get(override, 0) > rank.get(primary, 0):
        return override
    return primary


def operator_state_label(
    instruction_summary: str,
    approval_count: int,
    attention_status: str | None,
) -> str:
    """Return the operator lane label after approvals and attention are considered."""
    if approval_count > 0:
        return "Awaiting Approval"
    if attention_status_hint(attention_status) is not None:
        return "Loop Warning"
    if instruction_summary in {"(missing)", "(empty)"}:
        return "Idle"
    return "Supervising"
