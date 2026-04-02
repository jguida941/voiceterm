"""Queue-derivation helpers for event-backed review-state projections."""

from __future__ import annotations

from datetime import datetime, timezone

from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
)


def derive_event_next_instruction(packets: list[dict[str, object]]) -> str:
    return derive_event_next_instruction_bundle(packets)[0]


def derive_event_next_instruction_bundle(
    packets: list[dict[str, object]],
    *,
    build_event_context_packet_fn=build_event_context_packet,
    append_event_instruction_context_fn=append_event_instruction_context,
    build_instruction_source_fn=build_instruction_source,
) -> tuple[str, dict[str, object]]:
    now_utc = datetime.now(timezone.utc)
    for packet in packets:
        if packet.get("status") != "pending":
            continue
        if _is_expired(packet, now_utc):
            continue
        summary = str(packet.get("summary") or "").strip()
        if summary:
            context_packet = build_event_context_packet_fn(packet)
            instruction = append_event_instruction_context_fn(summary, context_packet)
            return instruction, build_instruction_source_fn(packet, context_packet)
    return "", {}


def derive_event_next_instruction_source(
    packets: list[dict[str, object]],
    **kwargs,
) -> dict[str, object]:
    return derive_event_next_instruction_bundle(packets, **kwargs)[1]


def _is_expired(packet: dict[str, object], now_utc: datetime) -> bool:
    """Return True if the packet's expires_at_utc is in the past."""
    from .event_store import parse_utc

    expires_at = parse_utc(packet.get("expires_at_utc"))
    return expires_at is not None and expires_at <= now_utc
