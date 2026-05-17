"""Packet-target selection for the compact authority snapshot contract."""

from __future__ import annotations

from collections.abc import Mapping

from .authority_snapshot_core import (
    AuthorityPacketTarget,
    authority_packet_target_from_attention_record,
)
from .review_state_packet_models import AgentAttentionRecord, packet_inbox_from_mapping


def select_packet_target(
    packet_inbox: Mapping[str, object],
) -> AuthorityPacketTarget | None:
    inbox = packet_inbox_from_mapping(packet_inbox)
    if inbox is None:
        return None

    best_record: AgentAttentionRecord | None = None
    best_key: tuple[object, ...] | None = None
    for record in inbox.agents:
        sort_key = _attention_sort_key(record)
        if best_key is None or sort_key < best_key:
            best_key = sort_key
            best_record = record
    if best_record is None:
        return None
    return authority_packet_target_from_attention_record(
        best_record,
        attention_revision=inbox.attention_revision,
    )


def _attention_sort_key(record: AgentAttentionRecord) -> tuple[object, ...]:
    return (
        0 if record.current_instruction_packet_id else 1,
        0 if record.pending_actionable_packet_ids else 1,
        0 if record.required_command else 1,
        0 if record.attention_status not in {"", "none"} else 1,
        record.agent,
    )
