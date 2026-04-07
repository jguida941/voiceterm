"""Restart policy helpers for the reviewer-supervisor follow loop."""

from __future__ import annotations

from collections.abc import Mapping

NON_RESTARTABLE_REVIEWER_SUPERVISOR_STOP_REASONS = frozenset(
    {
        "completed",
        "manual_stop",
    }
)


def non_restartable_reviewer_supervisor_stop_reason(
    state: Mapping[str, object] | None,
) -> str:
    """Return the stop reason that blocks implicit supervisor restart, if any."""
    if state is None:
        return ""
    stop_reason = str(state.get("stop_reason") or "").strip()
    if stop_reason in NON_RESTARTABLE_REVIEWER_SUPERVISOR_STOP_REASONS:
        return stop_reason
    return ""
