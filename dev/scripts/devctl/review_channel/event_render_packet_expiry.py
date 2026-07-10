"""Markdown rendering for packet-expiry materialization reports."""

from __future__ import annotations


def append_packet_expiry_materialization(
    lines: list[str],
    materialization: object,
) -> None:
    """Render write-side packet expiry materialization evidence."""
    if not isinstance(materialization, dict):
        return
    lines.append("")
    lines.append("## Packet Expiry Materialization")
    lines.append(
        "- materialized_packet_count: "
        f"{materialization.get('materialized_packet_count', 0)}"
    )
    lines.append(
        "- remaining_expired_pending_count: "
        f"{materialization.get('remaining_expired_pending_count', 0)}"
    )
    event_ids = materialization.get("event_ids")
    if isinstance(event_ids, list | tuple) and event_ids:
        lines.append("- event_ids: " + ", ".join(str(item) for item in event_ids))

