"""Shared packet-rank helpers for agent coordination projections."""

from __future__ import annotations

from .event_models import event_id_rank


def max_packet_event_rank(packet_rows: list[dict[str, object]]) -> int:
    best = -1
    for row in packet_rows:
        rank = event_id_rank(str(row.get("latest_event_id") or ""))
        if rank > best:
            best = rank
    return best
