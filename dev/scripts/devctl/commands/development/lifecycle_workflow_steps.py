"""Workflow lifecycle preview steps."""

from __future__ import annotations

from .models import DevelopmentLifecycleStep


def verify_steps(
    required_checks: tuple[str, ...],
) -> tuple[DevelopmentLifecycleStep, ...]:
    """Return steps for `/develop verify`."""
    return tuple(
        DevelopmentLifecycleStep(
            f"check-{index}",
            "Run one required guard/check for this development slice.",
            "ready",
            command,
            "local_verification",
        )
        for index, command in enumerate(required_checks, start=1)
    )


def submit_steps() -> tuple[DevelopmentLifecycleStep, ...]:
    """Return steps for `/develop submit`."""
    return (
        DevelopmentLifecycleStep(
            "verify",
            "Run slice checks before handoff or commit.",
            "ready",
            "python3 dev/scripts/devctl.py develop verify --format md",
            "local_verification",
        ),
        DevelopmentLifecycleStep(
            "handoff",
            "Future writer packages files, checks, risks, and packet refs.",
            "writer_not_enabled",
            "",
            "typed_packet_required",
        ),
    )


def close_steps() -> tuple[DevelopmentLifecycleStep, ...]:
    """Return steps for `/develop close`."""
    return (
        DevelopmentLifecycleStep(
            "retrospective",
            "Record what changed and which guard/probe should prevent recurrence.",
            "writer_not_enabled",
            "",
            "typed_learning_required",
        ),
        DevelopmentLifecycleStep(
            "audit-guards",
            "Review guard/probe learning state after the slice.",
            "ready",
            "python3 dev/scripts/devctl.py develop audit-guards --format md",
            "read_only",
        ),
    )


def rollback_steps() -> tuple[DevelopmentLifecycleStep, ...]:
    """Return steps for `/develop rollback`."""
    return (
        DevelopmentLifecycleStep(
            "recover",
            "Future writer records typed recovery intent before destructive cleanup.",
            "writer_not_enabled",
            "",
            "operator_or_lease_required",
        ),
    )


__all__ = ["close_steps", "rollback_steps", "submit_steps", "verify_steps"]
