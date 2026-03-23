"""Context-escalation support for `devctl loop-packet`."""

from __future__ import annotations

from typing import Any

from ...context_graph.escalation import (
    ContextEscalationPacket,
    build_context_escalation_packet,
    collect_query_terms,
    normalize_query_terms,
)

_TRIAGE_LOOP = "triage-loop"
_MUTATION_LOOP = "mutation-loop"


def build_loop_packet_context_packet(
    *,
    source_command: str,
    payload: dict[str, Any],
) -> ContextEscalationPacket | None:
    """Build a bounded context packet from loop-packet source payloads."""
    query_terms = _context_terms_for_payload(
        source_command=source_command,
        payload=payload,
    )
    return build_context_escalation_packet(
        trigger="loop-packet",
        query_terms=query_terms,
        options={"max_chars": 1200},
    )


def _context_terms_for_payload(
    *,
    source_command: str,
    payload: dict[str, Any],
) -> tuple[str, ...]:
    values: list[Any] = []
    if source_command == _TRIAGE_LOOP:
        attempts = payload.get("attempts")
        if isinstance(attempts, list):
            values.extend(attempts[-3:])
        values.extend([payload.get("issues"), payload.get("next_actions")])
    elif source_command == _MUTATION_LOOP:
        hotspots = payload.get("last_hotspots")
        if isinstance(hotspots, list):
            values.extend(hotspots[:3])
    else:
        values.extend([payload.get("issues"), payload.get("next_actions")])
    return normalize_query_terms(
        (source_command, *collect_query_terms(values, max_terms=3)),
        max_terms=4,
    )
