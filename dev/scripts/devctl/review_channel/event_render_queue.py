"""Markdown rendering helpers for event-backed queue summaries."""

from __future__ import annotations


def append_event_queue_summary(lines: list[str], queue: dict) -> None:
    """Append the compact queue summary to a markdown report."""
    lines.append(f"- pending_total: {queue.get('pending_total', 0)}")
    if queue.get("agent_sync_pending_total"):
        lines.append(
            "- agent_sync_pending_total: "
            f"{queue.get('agent_sync_pending_total', 0)}"
        )
        packet_ids = queue.get("agent_sync_pending_packet_ids")
        if isinstance(packet_ids, list) and packet_ids:
            lines.append(
                "- agent_sync_pending_packet_ids: "
                + ", ".join(str(packet_id) for packet_id in packet_ids)
            )
    if queue.get("filtered_pending_note"):
        lines.append(f"- filtered_pending_note: {queue.get('filtered_pending_note')}")
    lines.append(
        "- stale_packet_count: "
        f"{queue.get('stale_packet_count', 0)} (expired pending packets)"
    )

