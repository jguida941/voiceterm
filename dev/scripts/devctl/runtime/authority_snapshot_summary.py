"""Startup authority summary command helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .authority_snapshot_parse_support import mapping_or_empty as _mapping
from .post_checkpoint_dirty_support import (
    COMMIT_CHECKPOINT_COMMAND,
    requires_commit_before_push,
)

_CONTEXT_GRAPH_BOOTSTRAP_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)
_SUMMARY_RERUN_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)
_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)


def summary_blockers(ctx_dict: Mapping[str, object]) -> tuple[str, ...]:
    """Return the canonical startup blocker labels."""
    blockers: list[str] = []
    authority = _mapping(ctx_dict.get("startup_authority"))
    if authority and not bool(authority.get("ok", False)):
        blockers.append("startup_authority")
    _append_governance_blockers(blockers, ctx_dict)
    _append_runtime_blockers(blockers, ctx_dict)
    return tuple(dict.fromkeys(blockers))


def summary_blockers_csv(ctx_dict: Mapping[str, object]) -> str:
    """Return the startup blocker labels as a CSV string."""
    blockers = summary_blockers(ctx_dict)
    return ",".join(blockers) if blockers else "none"


def reviewer_recovery_command(ctx_dict: Mapping[str, object]) -> str:
    """Return the preferred review-loop recovery command when startup says so."""
    action = str(ctx_dict.get("advisory_action") or "").strip()
    if action != "repair_reviewer_loop":
        return ""
    reviewer_gate = _mapping(ctx_dict.get("reviewer_gate"))
    recovery_command = str(reviewer_gate.get("recovery_command") or "").strip()
    if recovery_command:
        return recovery_command
    if not bool(reviewer_gate.get("implementation_blocked", False)):
        return ""
    if bool(reviewer_gate.get("review_gate_allows_push", False)):
        return ""
    block_reason = str(reviewer_gate.get("implementation_block_reason") or "").strip()
    try:
        from ..review_channel.peer_recovery import STALE_PEER_RECOVERY
    except ImportError:
        return _REVIEW_STATUS_COMMAND
    entry = STALE_PEER_RECOVERY.get(block_reason, {})
    command = str(entry.get("recommended_command") or "").strip()
    return command or _REVIEW_STATUS_COMMAND


def summary_next_command(ctx_dict: Mapping[str, object]) -> str:
    """Return the canonical next command for the current startup payload."""
    blockers = summary_blockers(ctx_dict)
    if not blockers:
        command = _push_next_command(ctx_dict)
        return command or _CONTEXT_GRAPH_BOOTSTRAP_COMMAND
    recovery_command = _checkpoint_recovery_command(ctx_dict, blockers)
    if recovery_command:
        return recovery_command
    reviewer_command = reviewer_recovery_command(ctx_dict)
    if reviewer_command:
        return reviewer_command
    if _requires_review_status(ctx_dict, blockers):
        return _REVIEW_STATUS_COMMAND
    next_step_command = _push_next_command(ctx_dict)
    if next_step_command:
        return next_step_command
    return f"resolve blockers, then rerun {_SUMMARY_RERUN_COMMAND}"


def _append_governance_blockers(
    blockers: list[str],
    ctx_dict: Mapping[str, object],
) -> None:
    governance = _mapping(ctx_dict.get("governance"))
    push_enforcement = _mapping(governance.get("push_enforcement"))
    if bool(push_enforcement.get("checkpoint_required", False)):
        blockers.append("checkpoint_required")
    elif push_enforcement and not bool(
        push_enforcement.get("safe_to_continue_editing", True)
    ):
        blockers.append("continuation_blocked")
    if requires_commit_before_push(push_enforcement):
        blockers.append("post_checkpoint_dirty_worktree")


def _append_runtime_blockers(
    blockers: list[str],
    ctx_dict: Mapping[str, object],
) -> None:
    reviewer_gate = _mapping(ctx_dict.get("reviewer_gate"))
    if bool(reviewer_gate.get("implementation_blocked", False)) and not bool(
        reviewer_gate.get("review_gate_allows_push", False)
    ):
        block_reason = str(
            reviewer_gate.get("implementation_block_reason") or ""
        ).strip()
        blockers.append(block_reason or "reviewer_gate")
    coordination = _mapping(ctx_dict.get("coordination"))
    if bool(coordination.get("resync_required", False)):
        blockers.append("coordination_resync_required")
    permission = str(ctx_dict.get("implementation_permission") or "").strip()
    if permission in {"blocked", "suspended"}:
        blockers.append(f"implementation_permission_{permission}")


def _checkpoint_recovery_command(
    ctx_dict: Mapping[str, object],
    blockers: tuple[str, ...],
) -> str:
    recovery_authority = _mapping(ctx_dict.get("recovery_authority"))
    recovery_action = str(recovery_authority.get("decision_action_id") or "").strip()
    recovery_command = str(recovery_authority.get("command") or "").strip()
    if recovery_action == "cut_checkpoint" and recovery_command:
        return recovery_command
    if "post_checkpoint_dirty_worktree" in blockers:
        return COMMIT_CHECKPOINT_COMMAND
    push_decision = _mapping(ctx_dict.get("push_decision"))
    next_step_command = str(push_decision.get("next_step_command") or "").strip()
    if (
        "checkpoint_required" in blockers
        or "continuation_blocked" in blockers
        or str(push_decision.get("action") or "").strip() == "await_checkpoint"
    ):
        return next_step_command or _payload_next_command(ctx_dict) or COMMIT_CHECKPOINT_COMMAND
    return ""


def _requires_review_status(
    ctx_dict: Mapping[str, object],
    blockers: tuple[str, ...],
) -> bool:
    coordination = _mapping(ctx_dict.get("coordination"))
    return bool(coordination.get("resync_required", False)) or any(
        blocker.startswith("implementation_permission_") for blocker in blockers
    )


def _push_next_command(ctx_dict: Mapping[str, object]) -> str:
    push_decision = _mapping(ctx_dict.get("push_decision"))
    next_step_command = str(push_decision.get("next_step_command") or "").strip()
    if str(push_decision.get("action") or "").strip() == "run_devctl_push":
        return next_step_command
    return next_step_command


def _payload_next_command(ctx_dict: Mapping[str, object]) -> str:
    return str(ctx_dict.get("next_command") or "").strip()


__all__ = [
    "reviewer_recovery_command",
    "summary_blockers",
    "summary_blockers_csv",
    "summary_next_command",
]
