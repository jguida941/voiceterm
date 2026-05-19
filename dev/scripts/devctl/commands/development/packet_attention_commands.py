"""Command rendering for packet attention follow-ups."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PacketShowCommandRoute:
    actor: str = ""
    actor_role: str = ""
    session_id: str = ""
    target_role: str = ""
    target_session_id: str = ""
    control_decision_input: str = ""


def required_command_for_record(
    record,
    *,
    pending_packet_ids: tuple[str, ...],
    latest_finding_packet_id: str,
    fallback_command: str = "",
    packet: Mapping[str, object] | None = None,
    route: PacketShowCommandRoute | None = None,
) -> str:
    command = fallback_command or str(record.required_command or "").strip()
    if record.wake_reason == "finding_pending":
        packet_id = latest_finding_packet_id or (
            pending_packet_ids[0] if pending_packet_ids else ""
        )
        if packet_id:
            route = route or PacketShowCommandRoute()
            return show_packet_command(
                packet_id,
                route=PacketShowCommandRoute(
                    actor=str(getattr(record, "agent", "") or "").strip(),
                    actor_role=route.actor_role,
                    session_id=route.session_id,
                    target_role=_packet_text(packet, "target_role"),
                    target_session_id=_packet_text(packet, "target_session_id"),
                    control_decision_input=route.control_decision_input,
                ),
            )
    if record.wake_reason != "expired_unresolved_packet":
        return command
    if pending_packet_ids or latest_finding_packet_id:
        return command
    return "python3 dev/scripts/devctl.py develop audit-packets --format md"


def show_packet_command(
    packet_id: str,
    *,
    route: PacketShowCommandRoute | None = None,
) -> str:
    route = route or PacketShowCommandRoute()
    command = (
        "python3 dev/scripts/devctl.py review-channel --action show "
        f"--packet-id {packet_id}"
    )
    if route.actor:
        command = f"{command} --actor {route.actor}"
    if route.actor_role:
        command = f"{command} --actor-role {route.actor_role}"
    if route.session_id:
        command = f"{command} --session-id {route.session_id}"
    if route.target_role:
        command = f"{command} --target-role {route.target_role}"
    if route.target_session_id:
        command = f"{command} --target-session-id {route.target_session_id}"
    if route.control_decision_input:
        command = (
            f"{command} --control-decision-input {route.control_decision_input}"
        )
    return f"{command} --terminal none --format md"


def _packet_text(packet: Mapping[str, object] | None, field: str) -> str:
    if not isinstance(packet, Mapping):
        return ""
    return str(packet.get(field) or "").strip()


__all__ = [
    "PacketShowCommandRoute",
    "required_command_for_record",
    "show_packet_command",
]
