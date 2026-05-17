"""Lifecycle previews for the typed `/develop` controller."""

from __future__ import annotations

from typing import Any

from .lifecycle_commands import sync_status_command
from .lifecycle_packet_steps import show_steps, start_steps
from .lifecycle_watch_steps import watch_steps
from .lifecycle_workflow_steps import (
    close_steps,
    rollback_steps,
    submit_steps,
    verify_steps,
)
from .models import (
    DevelopmentLifecyclePlan,
    DevelopmentNextSlice,
    DevelopmentPacketAttention,
)

LIFECYCLE_ACTIONS = frozenset(
    {
        "show",
        "start",
        "watch",
        "verify",
        "submit",
        "close",
        "rollback",
    }
)


def lifecycle_plan(
    *,
    action: str,
    actor: str,
    args: Any,
    next_slice: DevelopmentNextSlice,
    packet_attention: DevelopmentPacketAttention,
    required_checks: tuple[str, ...],
) -> DevelopmentLifecyclePlan | None:
    """Build a read-only lifecycle preview for one `/develop` action."""
    if action not in LIFECYCLE_ACTIONS:
        return None
    slice_id = str(getattr(args, "slice_id", "") or next_slice.slice_id or "").strip()
    packet_id = str(
        getattr(args, "packet_id", "")
        or packet_attention.latest_finding_packet_id
        or ""
    ).strip()
    return DevelopmentLifecyclePlan(
        action=action,
        actor=actor,
        slice_id=slice_id,
        packet_id=packet_id,
        state="preview_only",
        summary=lifecycle_summary(action),
        steps=lifecycle_steps(
            action=action,
            actor=actor,
            packet_id=packet_id,
            required_checks=required_checks,
        ),
    )


def lifecycle_steps(
    *,
    action: str,
    actor: str,
    packet_id: str,
    required_checks: tuple[str, ...],
) -> tuple[DevelopmentLifecycleStep, ...]:
    """Return lifecycle steps for one preview action."""
    if action == "show":
        return show_steps(packet_id)
    if action == "watch":
        return watch_steps(actor)
    if action == "verify":
        return verify_steps(required_checks)
    if action == "start":
        return start_steps(packet_id)
    if action == "submit":
        return submit_steps()
    if action == "close":
        return close_steps()
    if action == "rollback":
        return rollback_steps()
    return ()


def lifecycle_summary(action: str) -> str:
    """Return a compact lifecycle summary."""
    if action == "show":
        return "Read the packet/slice evidence before acting."
    if action == "start":
        return "Preview the claim and lease prerequisites for a slice."
    if action == "watch":
        return "Keep the actor on typed packet/session state."
    if action == "verify":
        return "List the checks that prove the active development slice."
    if action == "submit":
        return "Preview governed handoff before review or commit."
    if action == "close":
        return "Preview learning capture after the slice lands."
    if action == "rollback":
        return "Preview typed recovery without destructive git commands."
    return "Preview the development lifecycle action."


def lifecycle_next_commands(action: str) -> tuple[str, ...] | None:
    """Return lifecycle-specific next commands, if this is a lifecycle action."""
    if action == "show":
        return ("python3 dev/scripts/devctl.py develop watch --format md",)
    if action == "start":
        return ("python3 dev/scripts/devctl.py develop verify --format md",)
    if action == "watch":
        return (sync_status_command(),)
    if action == "verify":
        return ("python3 dev/scripts/checks/check_active_plan_sync.py",)
    if action == "submit":
        return ("python3 dev/scripts/devctl.py develop verify --format md",)
    if action == "close":
        return ("python3 dev/scripts/devctl.py develop audit-guards --format md",)
    if action == "rollback":
        return (sync_status_command(),)
    return None


__all__ = [
    "LIFECYCLE_ACTIONS",
    "lifecycle_next_commands",
    "lifecycle_plan",
]
