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
    if watcher_lease.status != "live":
        return watcher_lease.next_report_command
    for signal in orchestration.signals:
        if signal.suggested_command:
            return signal.suggested_command
    return fallback_commands[0] if fallback_commands else ""


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


__all__ = ["next_required_command"]
