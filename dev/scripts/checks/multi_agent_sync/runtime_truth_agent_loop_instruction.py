"""Instruction authority checks for multi-agent runtime truth."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import (
    coerce_mapping,
    coerce_text,
)


def instruction_authority_mismatch_errors(
    payload: Mapping[str, object],
    decision_rows: list[Mapping[str, object]],
) -> list[str]:
    """Catch queue/inbox instructions drifting from typed active packet focus."""
    active_by_actor = _active_packets_by_actor(decision_rows)
    if not active_by_actor:
        return []

    errors: list[str] = []
    queue = coerce_mapping(payload.get("queue"))
    source = coerce_mapping(queue.get("derived_next_instruction_source"))
    queue_actor = coerce_text(source.get("to_agent"))
    queue_packet = coerce_text(source.get("packet_id"))
    active_packets = active_by_actor.get(queue_actor, frozenset())
    if active_packets and queue_packet and queue_packet not in active_packets:
        errors.append(
            "Queue-derived current instruction disagrees with typed "
            f"agent_loop_decision for {queue_actor}: queue={queue_packet}; "
            f"active_packets={_render_packet_set(active_packets)}"
        )
    errors.extend(_packet_inbox_mismatch_errors(payload, active_by_actor))
    return errors


def _packet_inbox_mismatch_errors(
    payload: Mapping[str, object],
    active_by_actor: Mapping[str, frozenset[str]],
) -> list[str]:
    inbox = coerce_mapping(payload.get("packet_inbox"))
    agents = inbox.get("agents")
    if not isinstance(agents, list):
        return []
    errors: list[str] = []
    for record in agents:
        if not isinstance(record, Mapping):
            continue
        actor = coerce_text(record.get("agent"))
        inbox_packet = coerce_text(record.get("current_instruction_packet_id"))
        active_packets = active_by_actor.get(actor, frozenset())
        if active_packets and inbox_packet and inbox_packet not in active_packets:
            errors.append(
                "Packet inbox current instruction disagrees with typed "
                f"agent_loop_decision for {actor}: inbox={inbox_packet}; "
                f"active_packets={_render_packet_set(active_packets)}"
            )
    return errors


def _active_packets_by_actor(
    decision_rows: list[Mapping[str, object]],
) -> dict[str, frozenset[str]]:
    grouped: dict[str, set[str]] = {}
    for row in decision_rows:
        actor = coerce_text(row.get("actor_id"))
        packet_id = coerce_text(row.get("active_packet_id"))
        if actor and packet_id:
            grouped.setdefault(actor, set()).add(packet_id)
    return {actor: frozenset(packet_ids) for actor, packet_ids in grouped.items()}


def _render_packet_set(packet_ids: frozenset[str]) -> str:
    return ",".join(sorted(packet_ids)) or "none"
