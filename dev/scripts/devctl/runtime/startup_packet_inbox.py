"""Compact startup-context packet-inbox payload helpers."""

from __future__ import annotations

from typing import TypedDict

from .review_state_models import PacketInboxState


class StartupPacketInboxAgentRow(TypedDict):
    """Compact startup-facing packet-inbox row for one agent."""

    agent: str
    attention_status: str
    wake_reason: str
    required_command: str
    delivery_state: str
    current_instruction_packet_id: str
    latest_finding_packet_id: str
    pending_actionable_total: int
    expired_unresolved_total: int


class StartupPacketInboxPayload(TypedDict):
    """Compact startup-facing packet-inbox payload."""

    attention_revision: str
    agents: list[StartupPacketInboxAgentRow]


def startup_packet_inbox_dict(
    packet_inbox: PacketInboxState,
) -> StartupPacketInboxPayload:
    """Keep bootstrap packet truth load-bearing without serializing the full inbox."""
    agent_rows: list[StartupPacketInboxAgentRow] = []
    for record in packet_inbox.agents:
        has_packet_signal = bool(
            record.current_instruction_packet_id
            or record.latest_finding_packet_id
            or record.pending_actionable_packet_ids
            or record.expired_unresolved_packet_ids
        )
        if not has_packet_signal and record.attention_status in {"", "none"}:
            continue
        agent_rows.append(
            StartupPacketInboxAgentRow(
                agent=record.agent,
                attention_status=record.attention_status,
                wake_reason=record.wake_reason,
                required_command=record.required_command,
                delivery_state=record.delivery_state,
                current_instruction_packet_id=record.current_instruction_packet_id,
                latest_finding_packet_id=record.latest_finding_packet_id,
                pending_actionable_total=len(record.pending_actionable_packet_ids),
                expired_unresolved_total=len(record.expired_unresolved_packet_ids),
            )
        )
    return StartupPacketInboxPayload(
        attention_revision=packet_inbox.attention_revision,
        agents=agent_rows,
    )
