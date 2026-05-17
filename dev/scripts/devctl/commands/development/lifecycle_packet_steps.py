"""Packet-oriented lifecycle preview steps."""

from __future__ import annotations

from .lifecycle_commands import packet_show_command
from .models import DevelopmentLifecycleStep


def show_steps(packet_id: str) -> tuple[DevelopmentLifecycleStep, ...]:
    """Return steps for `/develop show`."""
    return (
        DevelopmentLifecycleStep(
            "packet",
            "Read the triggering packet body through typed state.",
            "available" if packet_id else "missing_packet_id",
            packet_show_command(packet_id),
            "read_only",
        ),
    )


def start_steps(packet_id: str) -> tuple[DevelopmentLifecycleStep, ...]:
    """Return steps for `/develop start`."""
    return (
        DevelopmentLifecycleStep(
            "inspect",
            "Inspect the selected packet or slice before claiming work.",
            "available",
            packet_show_command(packet_id),
            "read_only",
        ),
        DevelopmentLifecycleStep(
            "claim",
            "Future writer records a WorkerPacket or MutationLease.",
            "writer_not_enabled",
            "",
            "typed_lease_required",
        ),
    )


__all__ = ["show_steps", "start_steps"]
