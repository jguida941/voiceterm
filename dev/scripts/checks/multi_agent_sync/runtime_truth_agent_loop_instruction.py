"""Instruction authority checks for multi-agent runtime truth."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import (
    coerce_mapping,
    coerce_text,
)
from dev.scripts.devctl.review_channel.agent_loop_decision_queue_targets import (
    _normalize_role,
)


def instruction_authority_mismatch_errors(
    payload: Mapping[str, object],
    decision_rows: list[Mapping[str, object]],
) -> list[str]:
    """Catch queue/inbox instructions drifting from typed active packet focus."""
    active_rows = _active_packet_rows(decision_rows)
    if not active_rows:
        return []

    errors: list[str] = []
    packet_index = _packet_index(payload)
    queue = coerce_mapping(payload.get("queue"))
    source = coerce_mapping(queue.get("derived_next_instruction_source"))
    queue_actor = coerce_text(source.get("to_agent"))
    queue_packet = coerce_text(source.get("packet_id"))
    queue_scope = _packet_scope(source, packet_index.get(queue_packet))
    active_packets = _active_packets_for_scope(
        active_rows,
        actor=queue_actor,
        role=queue_scope[0],
        session=queue_scope[1],
    )
    if active_packets and queue_packet and queue_packet not in active_packets:
        errors.append(
            "Queue-derived current instruction disagrees with typed "
            f"agent_loop_decision for {queue_actor}: queue={queue_packet}; "
            f"active_packets={_render_packet_set(active_packets)}"
        )
    errors.extend(_packet_inbox_mismatch_errors(payload, active_rows, packet_index))
    return errors


def _packet_inbox_mismatch_errors(
    payload: Mapping[str, object],
    active_rows: tuple[Mapping[str, str], ...],
    packet_index: Mapping[str, Mapping[str, object]],
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
        role, session = _packet_scope(record, packet_index.get(inbox_packet))
        active_packets = _active_packets_for_scope(
            active_rows,
            actor=actor,
            role=role,
            session=session,
        )
        if active_packets and inbox_packet and inbox_packet not in active_packets:
            errors.append(
                "Packet inbox current instruction disagrees with typed "
                f"agent_loop_decision for {actor}: inbox={inbox_packet}; "
                f"active_packets={_render_packet_set(active_packets)}"
            )
    return errors


def _active_packet_rows(
    decision_rows: list[Mapping[str, object]],
) -> tuple[Mapping[str, str], ...]:
    rows: list[Mapping[str, str]] = []
    for row in decision_rows:
        actor = coerce_text(row.get("actor_id"))
        packet_id = coerce_text(row.get("active_packet_id"))
        if not actor or not packet_id:
            continue
        rows.append(
            {
                "actor": actor,
                "role": _normalize_role(row.get("actor_role")),
                "session": coerce_text(row.get("session_id")),
                "packet_id": packet_id,
            }
        )
    return tuple(rows)


def _active_packets_for_scope(
    active_rows: tuple[Mapping[str, str], ...],
    *,
    actor: str,
    role: str,
    session: str,
) -> frozenset[str]:
    if not actor:
        return frozenset()
    packet_ids: set[str] = set()
    scoped = bool(role or session)
    for row in active_rows:
        if row.get("actor") != actor:
            continue
        if scoped and role and row.get("role") != role:
            continue
        if scoped and session and row.get("session") != session:
            continue
        packet_id = row.get("packet_id", "")
        if packet_id:
            packet_ids.add(packet_id)
    return frozenset(packet_ids)


def _packet_index(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    packets = payload.get("packets")
    if not isinstance(packets, list):
        return {}
    indexed: dict[str, Mapping[str, object]] = {}
    for row in packets:
        if not isinstance(row, Mapping):
            continue
        packet_id = coerce_text(row.get("packet_id"))
        if packet_id:
            indexed[packet_id] = row
    return indexed


def _packet_scope(
    source: Mapping[str, object],
    packet: Mapping[str, object] | None,
) -> tuple[str, str]:
    role = _normalize_role(source.get("target_role"))
    session = coerce_text(source.get("target_session_id"))
    if packet:
        role = role or _normalize_role(packet.get("target_role"))
        session = session or coerce_text(packet.get("target_session_id"))
    return role, session


def _render_packet_set(packet_ids: frozenset[str]) -> str:
    return ",".join(sorted(packet_ids)) or "none"
