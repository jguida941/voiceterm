"""Restart policy helpers for the reviewer-supervisor follow loop."""

from __future__ import annotations

from collections.abc import Mapping

NON_RESTARTABLE_REVIEWER_SUPERVISOR_STOP_REASONS = frozenset(
    {
        "completed",
        "manual_stop",
    }
)

_AUTO_RESTARTABLE_ACTION_IDS = frozenset(
    {
        "ensure_runtime",
        "relaunch_review_loop",
    }
)
_AUTO_RESTARTABLE_COMMAND_FLAGS = (
    "--action ensure",
    "--action launch",
)


def non_restartable_reviewer_supervisor_stop_reason(
    state: Mapping[str, object] | None,
    *,
    allow_manual_stop_recovery: bool = False,
) -> str:
    """Return the stop reason that blocks implicit supervisor restart, if any."""
    if state is None:
        return ""
    stop_reason = str(state.get("stop_reason") or "").strip()
    if stop_reason == "manual_stop" and (
        allow_manual_stop_recovery or bool(state.get("recoverable"))
    ):
        return ""
    if stop_reason in NON_RESTARTABLE_REVIEWER_SUPERVISOR_STOP_REASONS:
        return stop_reason
    return ""


def manual_stop_recovery_allowed(report: Mapping[str, object] | None) -> bool:
    """Return true when typed recovery authority permits healing a manual stop."""
    if not isinstance(report, Mapping):
        return False
    recovery_assessment = report.get("recovery_assessment")
    if not isinstance(recovery_assessment, Mapping):
        return False
    decision = recovery_assessment.get("decision")
    if not isinstance(decision, Mapping):
        return False
    if "can_auto_fix" in decision and not bool(decision.get("can_auto_fix")):
        return False
    if "requires_approval" in decision and bool(decision.get("requires_approval")):
        return False
    action_id = str(decision.get("action_id") or "").strip()
    if action_id in _AUTO_RESTARTABLE_ACTION_IDS:
        return True
    command = str(decision.get("command") or "").strip()
    return any(flag in command for flag in _AUTO_RESTARTABLE_COMMAND_FLAGS)
