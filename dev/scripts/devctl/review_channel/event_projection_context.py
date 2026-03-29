"""Context-packet helpers for event-backed review-channel projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict

from ..context_graph.escalation import (
    ContextEscalationPacket,
    build_context_escalation_packet,
    collect_query_terms,
)
from ..context_graph.escalation_render import append_compact_context_packet_markdown


def build_event_context_packet(
    packet: Mapping[str, object],
) -> ContextEscalationPacket | None:
    """Build a bounded context packet from one pending review packet."""
    query_terms = collect_query_terms(
        [
            packet.get("plan_id"),
            packet.get("summary"),
            packet.get("body"),
            packet.get("kind"),
        ],
        max_terms=4,
    )
    return build_context_escalation_packet(
        trigger="review-channel-event",
        query_terms=query_terms,
        options={"max_chars": 1200},
    )


def append_event_instruction_context(
    summary: str,
    context_packet: ContextEscalationPacket | None,
) -> str:
    """Render event-backed instructions as flat markdown safe for projections."""
    return append_compact_context_packet_markdown(summary, context_packet)


def build_instruction_source(
    packet: Mapping[str, object],
    context_packet: ContextEscalationPacket | None,
) -> dict[str, object]:
    """Return queue-source metadata for the derived next instruction."""
    packet_id = str(packet.get("packet_id") or "").strip()
    summary = str(packet.get("summary") or "").strip()
    if not packet_id or not summary:
        return {}
    source: dict[str, object] = {
        "source_type": "review_packet",
        "packet_id": packet_id,
        "from_agent": packet.get("from_agent"),
        "to_agent": packet.get("to_agent"),
    }
    if context_packet is not None:
        source["context_packet"] = asdict(context_packet)
        if context_packet.guidance_refs:
            source["guidance_refs"] = list(context_packet.guidance_refs)
    return source
