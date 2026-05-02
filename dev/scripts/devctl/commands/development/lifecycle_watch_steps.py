"""Actor-watch lifecycle preview steps."""

from __future__ import annotations

from .lifecycle_commands import actor_inbox_command, sync_status_command
from .models import DevelopmentLifecycleStep


def watch_steps(actor: str) -> tuple[DevelopmentLifecycleStep, ...]:
    """Return steps for `/develop watch`."""
    return (
        DevelopmentLifecycleStep(
            "sync-status",
            "Read compact packet/session deltas before acting.",
            "available",
            sync_status_command(),
            "read_only",
        ),
        DevelopmentLifecycleStep(
            "actor-inbox",
            "Watch this actor's typed packet lane.",
            "available",
            actor_inbox_command(actor),
            "read_only_observation",
        ),
    )


__all__ = ["watch_steps"]
