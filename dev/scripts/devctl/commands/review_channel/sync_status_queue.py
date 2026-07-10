"""Queue section helpers for event-backed sync-status output."""

from __future__ import annotations

from ...review_channel.pending_packets import partition_live_pending_packets


def sync_status_queue(
    *,
    review_state: dict[str, object],
    agents_block: dict[str, object],
    target_agent: str,
) -> tuple[list[object], dict[str, object]]:
    all_packets = list(review_state.get("packets") or [])
    pending_ids = _pending_packet_ids(
        agents_block=agents_block,
        target_agent=target_agent,
    )
    pending_packets = [
        packet
        for packet in all_packets
        if str(packet.get("packet_id") or "") in pending_ids
    ]
    stale_packets = _stale_packets_for_scope(all_packets, target_agent=target_agent)
    queue = {
        "pending_total": len(pending_packets),
        "stale_packet_count": len(stale_packets),
        "agent_sync_pending_total": sum(
            len((row or {}).get("pending_packets_to_me") or [])
            for row in agents_block.values()
            if isinstance(row, dict)
        ),
    }
    return pending_packets, queue


def _pending_packet_ids(
    *,
    agents_block: dict[str, object],
    target_agent: str,
) -> set[str]:
    pending_ids: set[str] = set()
    for agent_id, agent_row in agents_block.items():
        if not isinstance(agent_row, dict):
            continue
        if target_agent and agent_id != target_agent:
            continue
        for packet_id in agent_row.get("pending_packets_to_me") or []:
            pending_ids.add(str(packet_id))
    return pending_ids


def _stale_packets_for_scope(
    packets: list[object],
    *,
    target_agent: str,
) -> list[object]:
    scoped_packets = [
        packet
        for packet in packets
        if isinstance(packet, dict)
        and (not target_agent or str(packet.get("to_agent") or "") == target_agent)
    ]
    _, stale_packets = partition_live_pending_packets(scoped_packets)
    return stale_packets

