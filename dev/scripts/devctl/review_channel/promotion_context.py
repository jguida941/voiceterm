"""Context-packet helpers for review-channel promotion candidates."""

from __future__ import annotations

from dataclasses import asdict

from ..context_graph.escalation import (
    ContextEscalationPacket,
    build_context_escalation_packet,
    collect_query_terms,
)


def promotion_candidate_to_dict(
    candidate,
) -> dict[str, object] | None:
    """Convert a promotion candidate into JSON-friendly data."""
    if candidate is None:
        return None
    return asdict(candidate)


def build_promotion_context_packet(
    *,
    source_path: str,
    phase_heading: str | None,
    checklist_item: str,
    build_context_escalation_packet_fn=build_context_escalation_packet,
    collect_query_terms_fn=collect_query_terms,
) -> ContextEscalationPacket | None:
    query_terms = collect_query_terms_fn(
        [source_path, phase_heading, checklist_item],
        max_terms=4,
    )
    return build_context_escalation_packet_fn(
        trigger="review-channel-promotion",
        query_terms=query_terms,
        options={
            "max_chars": 700,
            "allow_full_scan": 0,
            "max_cached_bytes": 12_000_000,
        },
    )
