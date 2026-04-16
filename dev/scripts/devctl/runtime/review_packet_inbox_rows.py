"""Shared packet-row helpers for packet-inbox reducers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .review_packet_inbox_lookup import packet_id as _packet_id


def live_packet_ids(packets: Sequence[object] | object) -> frozenset[str]:
    """Return the normalized ids for currently-live packet rows."""
    return frozenset(
        packet_id
        for packet_id in (_packet_id(packet) for packet in _packet_rows(packets))
        if packet_id
    )


def _packet_rows(packets: Sequence[object] | object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))
