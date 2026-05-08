"""Startup-context publication deferral options."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from ...runtime.action_routing_publication_defer import (
    DIRTY_EDIT_DEFER_REASONS,
    DIRTY_EDIT_DEFER_TOPOLOGIES,
)


@dataclass(frozen=True, slots=True)
class StartupRoutingOptions:
    """Action-routing options for a startup-context invocation."""

    caller_role: str | None = None
    reviewer_override: bool = False
    defer_publication: bool = False


def defer_publication_requested(args) -> bool:
    if bool(getattr(args, "defer_publication", False)):
        return True
    return os.environ.get("DEVCTL_DEFER_PUBLICATION") == "1"


def auto_defer_publication_for_development(
    *,
    ctx: object,
    caller_role: object,
) -> bool:
    """Return whether startup should prefer edit-only development deferral.

    This is the automatic counterpart to ``--defer-publication``. It only
    applies to implementer startup when the worktree is safe for edits and the
    next pressure is publication/preflight, not checkpoint or safety repair.
    """
    if str(caller_role or "").strip() != "implementer":
        return False

    push = _attr(_attr(ctx, "governance"), "push_enforcement")
    if push is None:
        return False
    if _bool(_attr(push, "checkpoint_required")):
        return False
    if not _bool(_attr(push, "safe_to_continue_editing"), default=True):
        return False
    if _int(_attr(push, "staged_path_count")) > 0:
        return False

    push_decision = _attr(ctx, "push_decision")
    worktree_has_edits = _worktree_has_edit_debt(push)
    if worktree_has_edits:
        if not _dirty_edit_defer_context(ctx=ctx, push_decision=push_decision):
            return False
    elif _text(_attr(push_decision, "action")) != "run_devctl_push":
        return False

    backlog = _attr(push_decision, "publication_backlog")
    pending = _int(
        _attr(backlog, "pending_publication_commits"),
        fallback=_int(_attr(push, "pending_publication_commits")),
    )
    if pending <= 0:
        return False

    prior_push_failed = _text(_attr(push, "latest_push_report_status")) == "blocked"
    prior_validation_failed = (
        _text(_attr(push, "latest_push_report_reason")) == "validation_failed"
    )
    backlog_urgent = _bool(_attr(backlog, "backlog_urgent")) or _bool(
        _attr(push, "publication_backlog_urgent")
    )
    return prior_push_failed or prior_validation_failed or backlog_urgent


def _dirty_edit_defer_context(*, ctx: object, push_decision: object) -> bool:
    topology = _text(_attr(ctx, "observed_control_topology"))
    if topology not in DIRTY_EDIT_DEFER_TOPOLOGIES:
        return False
    reviewer_gate = _attr(ctx, "reviewer_gate")
    mode = _text(_attr(reviewer_gate, "effective_reviewer_mode")) or _text(
        _attr(reviewer_gate, "reviewer_mode")
    )
    if mode not in {"tools_only", "single_agent"}:
        return False
    action = _text(_attr(push_decision, "action"))
    reason = _text(_attr(push_decision, "reason"))
    return action == "await_checkpoint" and reason in DIRTY_EDIT_DEFER_REASONS


def _worktree_has_edit_debt(push: object) -> bool:
    return (
        _bool(_attr(push, "worktree_dirty"))
        or _int(_attr(push, "dirty_path_count")) > 0
        or _int(_attr(push, "unstaged_path_count")) > 0
        or _int(_attr(push, "untracked_path_count")) > 0
    )


def _attr(value: object, name: str = "") -> Any:
    if not name:
        return value
    return getattr(value, name, None)


def _text(value: object) -> str:
    return str(value or "").strip()


def _bool(value: object, *, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _int(value: object, *, fallback: int = 0) -> int:
    if value is None:
        return fallback
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return fallback


__all__ = [
    "StartupRoutingOptions",
    "auto_defer_publication_for_development",
    "defer_publication_requested",
]
