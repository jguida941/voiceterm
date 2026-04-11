"""Queue-derivation helpers for event-backed review-state projections."""

from __future__ import annotations

from .event_projection_context import (
    append_event_instruction_context,
    build_event_context_packet,
    build_instruction_source,
)
from .packet_control_loop import (
    format_priority_instruction,
    select_priority_pending_packet,
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
    packet, control_metadata = select_priority_pending_packet(packets)
    if packet is not None:
        summary = format_priority_instruction(
            str(packet.get("summary") or ""),
            selection_policy=str(control_metadata.get("selection_policy") or ""),
        )
        if summary:
            context_packet = build_event_context_packet_fn(packet)
            instruction = append_event_instruction_context_fn(summary, context_packet)
            source = build_instruction_source_fn(packet, context_packet)
            source.update(control_metadata)
            return instruction, source
    return "", {}


def derive_event_next_instruction_source(
    packets: list[dict[str, object]],
    **kwargs,
) -> dict[str, object]:
    return derive_event_next_instruction_bundle(packets, **kwargs)[1]
