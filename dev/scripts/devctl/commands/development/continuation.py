"""Continuation and watcher-lease state for `/develop`."""

from __future__ import annotations

from .continuation_commands import next_required_command
from .models import (
    DevelopmentContinuationRequiredSignal,
    DevelopmentOrchestrationSnapshot,
    DevelopmentPacketAttention,
    DevelopmentWatcherLease,
)
from .watcher import watcher_lease_status


def continuation_signal(
    *,
    packet_attention: DevelopmentPacketAttention,
    orchestration: DevelopmentOrchestrationSnapshot,
    watcher_lease: DevelopmentWatcherLease,
    current_action: str,
    fallback_commands: tuple[str, ...],
) -> DevelopmentContinuationRequiredSignal:
    """Return whether `/develop` has authority to stop."""
    reasons = _continuation_reasons(
        packet_attention=packet_attention,
        orchestration=orchestration,
        watcher_lease=watcher_lease,
    )
    next_command = next_required_command(
        packet_attention=packet_attention,
        orchestration=orchestration,
        watcher_lease=watcher_lease,
        current_action=current_action,
        fallback_commands=fallback_commands,
    )
    required = bool(reasons)
    return DevelopmentContinuationRequiredSignal(
        continuation_required=required,
        status="continue_required" if required else "closed",
        final_response_allowed=not required,
        reasons=reasons,
        next_required_command=next_command if required else "",
        stop_policy="stop_only_when_typed_controller_closed",
        summary=_continuation_summary(required=required, next_command=next_command),
    )


def _continuation_reasons(
    *,
    packet_attention: DevelopmentPacketAttention,
    orchestration: DevelopmentOrchestrationSnapshot,
    watcher_lease: DevelopmentWatcherLease,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if packet_attention.attention_required:
        reasons.append(f"packet_attention:{packet_attention.wake_reason or 'required'}")
    if orchestration.action_required_count:
        reasons.append(f"orchestration_action_required:{orchestration.action_required_count}")
    if orchestration.stale_projection_count:
        reasons.append(f"stale_orchestration_inputs:{orchestration.stale_projection_count}")
    if orchestration.missing_projection_count:
        reasons.append(f"missing_orchestration_inputs:{orchestration.missing_projection_count}")
    if watcher_lease.status != "live":
        reasons.append(f"watcher_{watcher_lease.status}:{watcher_lease.watched_actor}")
    return tuple(reasons)


def _continuation_summary(*, required: bool, next_command: str) -> str:
    if not required:
        return "Typed controller closure allows a terminal response."
    return f"Do not stop here; run `{next_command}` next."


__all__ = ["continuation_signal", "watcher_lease_status"]
