"""Rebuild control-decision packet attention from the scoped packet inbox."""

from __future__ import annotations

from collections.abc import Mapping

from .control_decision_packet_ids import packet_id_from_command
from .control_decision_packet_lifecycle import (
    packet_by_id,
    packet_lifecycle_attention,
)
from .review_packet_inbox import packet_inbox_from_review_state
from .review_state_packet_models import AgentAttentionRecord


def packet_inbox_attention(
    payload: Mapping[str, object],
    *,
    actor: str = "",
) -> dict[str, object]:
    """Derive body lifecycle attention from the same inbox used by /develop."""

    if not actor:
        return {}
    inbox = packet_inbox_from_review_state(payload)
    if inbox is None:
        return {}
    record = inbox.for_agent(actor)
    if record is None:
        return {}
    packet_id = _record_packet_id(record)
    if not packet_id:
        return {}
    packet = packet_by_id(payload, packet_id)
    return packet_lifecycle_attention(packet, packet_id=packet_id)


def _record_packet_id(record: object) -> str:
    if not isinstance(record, AgentAttentionRecord):
        return ""
    latest = str(record.latest_finding_packet_id or "").strip()
    if latest:
        return latest
    pending = tuple(record.pending_actionable_packet_ids or ())
    if pending:
        return str(pending[0] or "").strip()
    current = str(record.current_instruction_packet_id or "").strip()
    if current:
        return current
    return packet_id_from_command(str(record.required_command or ""))
