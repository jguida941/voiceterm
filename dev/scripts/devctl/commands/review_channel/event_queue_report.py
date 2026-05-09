"""Queue report helpers for event-backed review-channel actions."""

from __future__ import annotations

from ...review_channel.agent_sync_readers import agent_sync_pending_packet_ids
from ...review_channel.event_projection_queue import build_event_queue_summary
from ...review_channel.pending_packets import live_pending_packets


def queue_for_event_report(
    *,
    args,
    bundle,
    packets: list[dict[str, object]] | None,
):
    """Return the queue summary for one event-backed action report."""
    queue = bundle.review_state.get("queue", {})
    target = str(getattr(args, "target", "") or "").strip()
    status_filter = str(getattr(args, "status", "") or "").strip()
    if (
        args.action not in {"inbox", "watch", "operator-inbox"}
        or not target
        or packets is None
        or status_filter not in {"", "pending"}
    ):
        return queue
    pending_counts = {
        "codex": 0,
        "claude": 0,
        "cursor": 0,
        "operator": 0,
    }
    pending_counts[target] = len(packets)
    stale_count = 0
    if isinstance(queue, dict):
        stale_count = int(queue.get("stale_packet_count") or 0)
    summary = build_event_queue_summary(
        pending_counts,
        stale_count,
        packets=packets,
    )
    pending_ids = _canonical_agent_sync_pending_ids(
        review_state=bundle.review_state,
        target=target,
    )
    if pending_ids:
        summary["agent_sync_pending_total"] = len(pending_ids)
        summary["agent_sync_pending_packet_ids"] = list(pending_ids)
        if not packets:
            summary["filtered_pending_note"] = (
                "target has pending agent-sync packet attention outside the "
                "actionable inbox filter"
            )
    return summary


def _canonical_agent_sync_pending_ids(
    *,
    review_state: dict[str, object],
    target: str,
) -> tuple[str, ...]:
    """Return agent-sync pending IDs that still exist in canonical live rows."""
    pending_ids = agent_sync_pending_packet_ids(review_state, target)
    packet_rows = review_state.get("packets")
    if not isinstance(packet_rows, list):
        return pending_ids
    canonical_live_ids = {
        str(packet.get("packet_id") or "").strip()
        for packet in live_pending_packets(packet_rows)
        if isinstance(packet, dict)
        and str(packet.get("to_agent") or "").strip() == target
    }
    if not canonical_live_ids:
        return ()
    return tuple(packet_id for packet_id in pending_ids if packet_id in canonical_live_ids)
