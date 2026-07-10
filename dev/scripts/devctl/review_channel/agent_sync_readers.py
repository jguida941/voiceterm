"""Shared readers for the review-channel ``agent_sync`` projection."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.value_coercion import coerce_mapping, coerce_text


def agent_sync_row_for_actor(
    review_state: Mapping[str, object],
    actor_id: str,
) -> Mapping[str, object]:
    """Return the typed agent_sync row for ``actor_id`` when present."""
    actor = coerce_text(actor_id)
    if not actor:
        return {}
    agents = coerce_mapping(coerce_mapping(review_state.get("agent_sync")).get("agents"))
    row = agents.get(actor)
    return row if isinstance(row, Mapping) else {}


def agent_sync_pending_packet_ids(
    review_state: Mapping[str, object],
    actor_id: str,
) -> tuple[str, ...]:
    """Return pending packet IDs for ``actor_id`` from ``agent_sync``."""
    return agent_sync_pending_packet_ids_from_row(
        agent_sync_row_for_actor(review_state, actor_id)
    )


def agent_sync_pending_packet_ids_from_row(
    row: Mapping[str, object],
) -> tuple[str, ...]:
    """Return normalized ``pending_packets_to_me`` values from one row."""
    packet_ids = row.get("pending_packets_to_me")
    if not isinstance(packet_ids, list):
        return ()
    return tuple(
        packet_id
        for packet_id in (coerce_text(value) for value in packet_ids)
        if packet_id
    )


def agent_sync_pending_packet_count_from_row(row: Mapping[str, object]) -> int:
    """Return the number of normalized pending packets in one sync row."""
    return len(agent_sync_pending_packet_ids_from_row(row))

