"""Queue-derivation helpers for event-backed review-state projections."""

from __future__ import annotations

from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
)
from .pending_packets import live_pending_packets


def derive_event_next_instruction(packets: list[dict[str, object]]) -> str:
    return derive_event_next_instruction_bundle(packets)[0]


def derive_event_next_instruction_bundle(
    packets: list[dict[str, object]],
    *,
    build_event_context_packet_fn=build_event_context_packet,
    append_event_instruction_context_fn=append_event_instruction_context,
    build_instruction_source_fn=build_instruction_source,
) -> tuple[str, dict[str, object]]:
    for packet in live_pending_packets(packets):
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
