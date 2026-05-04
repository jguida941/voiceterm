"""Next-command selection for `/develop` continuation."""

from __future__ import annotations

from .models import (
    DevelopmentOrchestrationSnapshot,
    DevelopmentPacketAttention,
    DevelopmentWatcherLease,
)


def next_required_command(
    *,
    packet_attention: DevelopmentPacketAttention,
    orchestration: DevelopmentOrchestrationSnapshot,
    watcher_lease: DevelopmentWatcherLease,
    packet_pressure: object | None = None,
    current_action: str,
    fallback_commands: tuple[str, ...],
) -> str:
    """Return the concrete command that keeps the controller moving."""
    if _packet_attention_command_is_current_action(
        packet_attention,
        current_action=current_action,
    ):
        return fallback_commands[0] if fallback_commands else packet_attention.required_command
    if packet_attention.attention_required and packet_attention.required_command:
        return packet_attention.required_command
    if watcher_report_needed(
        packet_attention=packet_attention,
        watcher_lease=watcher_lease,
        packet_pressure=packet_pressure,
    ):
        return watcher_lease.next_report_command
    for signal in orchestration.signals:
        if signal.suggested_command:
            return signal.suggested_command
    return fallback_commands[0] if fallback_commands else ""


def watcher_report_needed(
    *,
    packet_attention: DevelopmentPacketAttention,
    watcher_lease: DevelopmentWatcherLease,
    packet_pressure: object | None = None,
) -> bool:
    """Return whether a stopped watcher is blocking live packet attention."""
    if watcher_lease.status == "live":
        return False
    if packet_attention.attention_required:
        return True
    if packet_attention.pending_delivery_packet_ids:
        return True
    if packet_attention.pending_actionable_packet_ids:
        return True
    if packet_attention.expired_unresolved_count:
        return True
    if packet_pressure is None:
        return True
    return any(
        _packet_pressure_count(packet_pressure, field_name) > 0
        for field_name in (
            "live_total",
            "actionable_total",
            "near_ttl_total",
            "expired_unresolved_total",
            "durable_owner_gap_total",
        )
    )


def _packet_attention_command_is_current_action(
    packet_attention: DevelopmentPacketAttention,
    *,
    current_action: str,
) -> bool:
    command = packet_attention.required_command
    if not packet_attention.attention_required or not command:
        return False
    if current_action == "audit-packets" and "develop audit-packets" in command:
        return True
    return False


def _packet_pressure_count(packet_pressure: object | None, field_name: str) -> int:
    if packet_pressure is None:
        return 0
    if isinstance(packet_pressure, dict):
        value = packet_pressure.get(field_name, 0)
    else:
        value = getattr(packet_pressure, field_name, 0)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


__all__ = ["next_required_command", "watcher_report_needed"]
