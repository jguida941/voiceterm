"""Instruction authority checks for multi-agent runtime truth."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import (
    coerce_mapping,
    coerce_text,
)
from dev.scripts.devctl.review_channel.packet_body_observation import (
    packet_body_observed_by,
)
from dev.scripts.devctl.review_channel.agent_loop_decision_queue_targets import (
    _normalize_role,
)

from .runtime_truth_agent_loop_communication import (
    _active_focus_is_communication_only,
    _packet_is_communication_only,
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
    queue_packet_record = packet_index.get(queue_packet)
    queue_scope = _packet_scope(source, packet_index.get(queue_packet))
    active_packets = _active_packets_for_scope(
        active_rows,
        actor=queue_actor,
        role=queue_scope[0],
        session=queue_scope[1],
    )
    if (
        active_packets
        and queue_packet
        and queue_packet not in active_packets
        and not _packet_is_communication_only(queue_packet_record)
        and not _active_focus_is_communication_only(
            active_rows,
            active_packets,
            packet_index,
        )
        and not _body_open_subqueue_matches(
            active_rows,
            actor=queue_actor,
            role=queue_scope[0],
            session=queue_scope[1],
            current_packet=queue_packet_record,
        )
        and not _scope_has_executing_packet(
            active_rows,
            actor=queue_actor,
            role=queue_scope[0],
            session=queue_scope[1],
        )
    ):
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
        inbox_packet_record = packet_index.get(inbox_packet)
        role, session = _packet_scope(record, inbox_packet_record)
        pending_ids = _string_rows(record.get("pending_actionable_packet_ids"))
        active_packets = _active_packets_for_scope(
            active_rows,
            actor=actor,
            role=role,
            session=session,
        )
        if (
            active_packets
            and inbox_packet
            and inbox_packet not in active_packets
            and not _packet_is_communication_only(inbox_packet_record)
            and not _active_focus_is_communication_only(
                active_rows,
                active_packets,
                packet_index,
            )
            and not _body_open_subqueue_matches(
                active_rows,
                actor=actor,
                role=role,
                session=session,
                current_packet=inbox_packet_record,
                candidate_packet_ids=pending_ids,
            )
            and not _scope_has_executing_packet(
                active_rows,
                actor=actor,
                role=role,
                session=session,
            )
        ):
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
                "executing_packet_id": coerce_text(row.get("executing_packet_id")),
                "required_action": coerce_text(row.get("required_action")),
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


def _scope_has_executing_packet(
    active_rows: tuple[Mapping[str, str], ...],
    *,
    actor: str,
    role: str,
    session: str,
) -> bool:
    """Return whether this role/session is already executing a packet.

    In the role-neutral lifecycle model, "current instruction" can describe
    the next pending packet while an older packet remains in execution. That is
    a live lifecycle state, not an authority contradiction.
    """
    if not actor:
        return False
    scoped = bool(role or session)
    for row in active_rows:
        if row.get("actor") != actor:
            continue
        if session and row.get("session") == session and row.get("executing_packet_id"):
            return True
        if scoped and role and row.get("role") != role:
            continue
        if scoped and session and row.get("session") != session:
            continue
        if row.get("executing_packet_id"):
            return True
    return False


def _body_open_subqueue_matches(
    active_rows: tuple[Mapping[str, str], ...],
    *,
    actor: str,
    role: str,
    session: str,
    current_packet: Mapping[str, object] | None,
    candidate_packet_ids: tuple[str, ...] = (),
) -> bool:
    """Allow body-open focus to advance past an already-opened pending packet.

    The inbox/queue current-instruction packet can remain the highest pending
    unresolved item after its body was opened. Agent-loop must still focus the
    next unread body packet before mutation. That stricter body-ingestion
    subqueue is not an authority disagreement as long as it is scoped to the
    same actor/role/session. Some inbox projections list only the top
    actionable delivery packet and omit older body-open work, so the typed
    ``open_packet_body`` action is the stricter proof than candidate-list
    membership.
    """
    if not _packet_body_observed(
        current_packet,
        actor=actor,
        role=role,
        session=session,
    ):
        return False
    active_packets = _active_packets_for_scope(
        active_rows,
        actor=actor,
        role=role,
        session=session,
    )
    if not active_packets:
        return False
    for row in active_rows:
        if row.get("actor") != actor:
            continue
        if role and row.get("role") != role:
            continue
        if session and row.get("session") != session:
            continue
        if (
            row.get("packet_id") in active_packets
            and row.get("required_action") == "open_packet_body"
        ):
            return True
    return False


def _packet_body_observed(
    packet: Mapping[str, object] | None,
    *,
    actor: str,
    role: str,
    session: str,
) -> bool:
    if not packet:
        return False
    if packet_body_observed_by(
        packet,
        actor=actor,
        role=role,
        session=session,
    ):
        return True
    return _legacy_packet_body_observed_by_scope(
        packet,
        actor=actor,
        role=role,
        session=session,
    )


def _legacy_packet_body_observed_by_scope(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> bool:
    if _observation_row_matches_scope(
        packet,
        actor=actor,
        role=role,
        session=session,
    ):
        return True
    return any(
        isinstance(event, Mapping)
        and _observation_row_matches_scope(
            event,
            actor=actor,
            role=role,
            session=session,
        )
        for event in _legacy_body_observation_events(packet)
    )


def _legacy_body_observation_events(
    packet: Mapping[str, object],
) -> tuple[object, ...]:
    events = packet.get("body_observation_events")
    if isinstance(events, (list, tuple)):
        return tuple(events)
    return ()


def _observation_row_matches_scope(
    row: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> bool:
    if not actor or coerce_text(row.get("body_observed_by")) != actor:
        return False
    if role and coerce_text(row.get("body_observed_role")) not in {"", role}:
        return False
    if session and coerce_text(row.get("body_observed_session_id")) not in {"", session}:
        return False
    return bool(
        coerce_text(row.get("body_observed_event_id"))
        or coerce_text(row.get("body_observed_at_utc"))
        or coerce_text(row.get("body_observed_by"))
    )


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


def _string_rows(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(coerce_text(row) for row in value if coerce_text(row))


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
