"""Packet lookup helpers for the typed packet inbox."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone


def latest_packet(
    packets: Sequence[Mapping[str, object]] | object,
) -> Mapping[str, object] | None:
    """Return the latest packet by posted time and packet id."""
    packet_rows = [packet for packet in _packet_rows(packets)]
    if not packet_rows:
        return None
    return max(packet_rows, key=_latest_sort_key)


def packet_id(packet: Mapping[str, object] | None) -> str:
    """Return one normalized packet id."""
    if packet is None:
        return ""
    return _normalized_text(packet.get("packet_id"))


def _latest_sort_key(packet: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _parse_utc(packet.get("posted_at")),
        packet_id(packet),
    )


def _packet_rows(
    packets: Sequence[Mapping[str, object]] | object,
) -> tuple[Mapping[str, object], ...]:
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


def _normalized_text(value: object) -> str:
    return str(value or "").strip()


def _parse_utc(value: object) -> datetime:
    text = _normalized_text(value)
    if not text:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)
