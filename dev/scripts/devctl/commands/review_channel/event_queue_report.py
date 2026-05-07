"""Queue report helpers for event-backed review-channel actions."""

from __future__ import annotations

from ...review_channel.agent_sync_readers import agent_sync_pending_packet_ids
from ...review_channel.event_projection_queue import build_event_queue_summary


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
    pending_ids = agent_sync_pending_packet_ids(bundle.review_state, target)
    if pending_ids:
        summary["agent_sync_pending_total"] = len(pending_ids)
        summary["agent_sync_pending_packet_ids"] = list(pending_ids)
        if not packets:
            summary["filtered_pending_note"] = (
                "target has pending agent-sync packet attention outside the "
                "actionable inbox filter"
            )
    return summary

