"""Agent-loop consistency checks for the multi-agent sync guard."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_text,
)
from dev.scripts.devctl.review_channel.packet_loop_attention import (
    packet_requires_runtime_attention,
)

if __package__:
    from .runtime_truth_agent_loop_focus import packet_focus_errors
    from .runtime_truth_agent_loop_pending import packet_rows, pending_packet_agents
    from .runtime_truth_agent_loop_attention import (
        agent_sync_attention_scope_errors,
    )
    from .runtime_truth_agent_loop_instruction import (
        instruction_authority_mismatch_errors,
    )
    from .runtime_truth_agent_loop_packet_attention import (
        ambiguous_packet_attention_errors,
    )
else:  # pragma: no cover - standalone package fallback
    from runtime_truth_agent_loop_focus import packet_focus_errors
    from runtime_truth_agent_loop_pending import packet_rows, pending_packet_agents
    from runtime_truth_agent_loop_attention import agent_sync_attention_scope_errors
    from runtime_truth_agent_loop_instruction import instruction_authority_mismatch_errors
    from runtime_truth_agent_loop_packet_attention import ambiguous_packet_attention_errors


def agent_loop_decision_errors(payload: Mapping[str, object]) -> list[str]:
    """Validate agent-loop rows against work-board, queue, and inbox state."""
    work_board = coerce_mapping(payload.get("agent_work_board"))
    rows = work_board.get("rows")
    work_rows = (
        [row for row in rows if isinstance(row, Mapping)]
        if isinstance(rows, list)
        else []
    )
    decision_rows = agent_loop_decision_rows(payload)
    if not work_rows:
        return []
    if not decision_rows:
        return [
            "Typed agent_work_board has rows but agent_loop_decisions is empty; "
            "runtime readers may be hiding wake/attention state."
        ]

    errors: list[str] = []
    packet_index = _packet_index_by_id(packet_rows(payload))
    errors.extend(_work_board_decision_errors(work_rows, decision_rows, packet_index))
    sync_agents = coerce_mapping(coerce_mapping(payload.get("agent_sync")).get("agents"))
    pending_agents = {
        agent
        for agent in pending_packet_agents(sync_agents, packet_rows=packet_rows(payload))
        if _pending_agent_requires_loop_decision(agent, work_rows, packet_index)
    }
    decision_pending_agents = {
        coerce_text(row.get("actor_id"))
        for row in decision_rows
        if coerce_int(row.get("pending_packet_count")) > 0
    }
    missing_pending = sorted(pending_agents - decision_pending_agents)
    if missing_pending:
        errors.append(
            "Agent sync reports pending packets but agent_loop_decisions carry "
            "no pending count for: "
            + ", ".join(missing_pending)
        )
    errors.extend(
        ambiguous_packet_attention_errors(
            payload,
            decision_rows,
            pending_agents=pending_agents,
        )
    )
    errors.extend(agent_sync_attention_scope_errors(payload, decision_rows))
    errors.extend(instruction_authority_mismatch_errors(payload, decision_rows))
    return errors


def agent_loop_decision_rows(
    payload: Mapping[str, object],
) -> list[Mapping[str, object]]:
    rows = payload.get("agent_loop_decisions")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _work_board_decision_errors(
    work_rows: list[Mapping[str, object]],
    decision_rows: list[Mapping[str, object]],
    packet_index: Mapping[str, Mapping[str, object]],
) -> list[str]:
    decisions_by_key = {
        _agent_loop_key(row): row
        for row in decision_rows
        if _agent_loop_key(row)
    }
    errors: list[str] = []
    for row in work_rows:
        if not _work_board_row_requires_loop_decision(row, packet_index):
            continue
        key = _work_board_key(row)
        if not key:
            continue
        decision = decisions_by_key.get(key)
        if decision is None:
            errors.append(
                "Typed agent_work_board row has no matching agent_loop_decision: "
                f"{key}"
            )
            continue
        errors.extend(packet_focus_errors(key, row, decision))
    return errors


def _work_board_row_requires_loop_decision(
    row: Mapping[str, object],
    packet_index: Mapping[str, Mapping[str, object]] | None = None,
) -> bool:
    packet_ids = _work_board_packet_ids(row)
    if not packet_ids and _is_demoted_helper_subagent(row):
        return False
    if packet_ids:
        if packet_index is None:
            return True
        actor = coerce_text(row.get("actor_id"))
        role = coerce_text(row.get("role"))
        session = coerce_text(row.get("session_id"))
        for packet_id in packet_ids:
            packet = packet_index.get(packet_id)
            if packet is None:
                return True
            if packet_requires_runtime_attention(
                packet,
                actor=actor,
                role=role,
                session=session,
            ):
                return True
        return False
    if coerce_text(row.get("confidence_class")) == "stale":
        return False
    stale_after = coerce_int(row.get("stale_after_seconds"))
    idle_seconds = coerce_int(row.get("idle_seconds"))
    return not (stale_after > 0 and idle_seconds > stale_after)


def _pending_agent_requires_loop_decision(
    agent: str,
    work_rows: list[Mapping[str, object]],
    packet_index: Mapping[str, Mapping[str, object]],
) -> bool:
    """Mirror work-board loop authority for pending packet count checks."""
    routed_rows = [
        row
        for row in work_rows
        if coerce_text(row.get("actor_id")) == agent
    ]
    if not routed_rows:
        return True
    return any(
        _work_board_row_requires_loop_decision(row, packet_index)
        for row in routed_rows
    )


def _work_board_packet_ids(row: Mapping[str, object]) -> tuple[str, ...]:
    packet_ids: list[str] = []
    for key in ("active_packet_id", "attention_packet_id", "executing_packet_id"):
        packet_id = coerce_text(row.get(key))
        if packet_id and packet_id not in packet_ids:
            packet_ids.append(packet_id)
    return tuple(packet_ids)


def _is_demoted_helper_subagent(row: Mapping[str, object]) -> bool:
    return (
        coerce_text(row.get("role")) == "subagent"
        and coerce_text(row.get("role_source")) == "helper_session_demotion"
    )


def _packet_index_by_id(
    rows: list[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        packet_id = coerce_text(row.get("packet_id"))
        if packet_id:
            indexed[packet_id] = row
    return indexed


def _work_board_key(row: Mapping[str, object]) -> str:
    actor = coerce_text(row.get("actor_id"))
    role = coerce_text(row.get("role"))
    session = coerce_text(row.get("session_id"))
    if not actor:
        return ""
    return "|".join([actor, role, session])


def _agent_loop_key(row: Mapping[str, object]) -> str:
    actor = coerce_text(row.get("actor_id"))
    role = coerce_text(row.get("actor_role"))
    session = coerce_text(row.get("session_id"))
    if not actor:
        return ""
    return "|".join([actor, role, session])
