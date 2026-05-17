"""Pending packet readers for the multi-agent sync guard."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import coerce_text
from dev.scripts.devctl.review_channel.agent_sync_readers import (
    agent_sync_pending_packet_ids_from_row,
)
from dev.scripts.devctl.review_channel.packet_loop_attention import (
    packet_requires_runtime_attention,
)

_NON_AGENT_LOOP_TARGETS = frozenset({"operator", "system"})


def pending_packet_agents(
    agents: Mapping[str, object],
    packet_rows: list[Mapping[str, object]] | None = None,
) -> list[str]:
    """Return actors with typed pending packets that should wake agent loops."""
    packet_index = packet_index_by_id(packet_rows or [])
    pending: list[str] = []
    for agent_id, row in agents.items():
        if not isinstance(row, Mapping):
            continue
        agent = coerce_text(agent_id)
        if agent in _NON_AGENT_LOOP_TARGETS:
            continue
        packet_ids = agent_sync_pending_packet_ids_from_row(row)
        if has_runtime_attention_packet(
            packet_ids,
            packet_index,
            actor_id=agent,
        ):
            pending.append(agent)
    return sorted(pending)


def packet_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    rows = payload.get("packets")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def packet_index_by_id(
    packet_rows: list[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in packet_rows:
        packet_id = coerce_text(row.get("packet_id"))
        if packet_id:
            indexed[packet_id] = row
    return indexed


def has_runtime_attention_packet(
    packet_ids: tuple[str, ...],
    packet_index: Mapping[str, Mapping[str, object]],
    *,
    actor_id: str = "",
) -> bool:
    for packet_id in packet_ids:
        if not packet_id:
            continue
        packet = packet_index.get(packet_id)
        if packet is None:
            return True
        if packet_requires_runtime_attention(
            packet,
            actor=actor_id,
            role=coerce_text(packet.get("target_role")),
            session=coerce_text(packet.get("target_session_id")),
        ):
            return True
    return False
