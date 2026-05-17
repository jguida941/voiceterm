"""Packet lookup helpers for event-backed review-channel actions."""

from __future__ import annotations


def packet_by_id(
    review_state: dict[str, object],
    packet_id: object,
) -> dict[str, object] | None:
    for packet_row in review_state.get("packets", []):
        if (
            isinstance(packet_row, dict)
            and packet_row.get("packet_id") == packet_id
        ):
            return packet_row
    return None


__all__ = ["packet_by_id"]
