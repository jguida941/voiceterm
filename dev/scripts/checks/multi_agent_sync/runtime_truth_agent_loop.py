"""Agent-loop consistency checks for the multi-agent sync guard."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_text,
)

if __package__:
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
    errors.extend(_work_board_decision_errors(work_rows, decision_rows))
    sync_agents = coerce_mapping(coerce_mapping(payload.get("agent_sync")).get("agents"))
    pending_agents = set(
        pending_packet_agents(sync_agents, packet_rows=_packet_rows(payload))
    )
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
) -> list[str]:
    decisions_by_key = {
        _agent_loop_key(row): row
        for row in decision_rows
        if _agent_loop_key(row)
    }
    errors: list[str] = []
    for row in work_rows:
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
        errors.extend(_packet_focus_errors(key, row, decision))
    return errors


def _packet_focus_errors(
    key: str,
    row: Mapping[str, object],
    decision: Mapping[str, object],
) -> list[str]:
    errors: list[str] = []
    active = coerce_text(row.get("active_packet_id"))
    decision_active = coerce_text(decision.get("active_packet_id"))
    if active and not _decision_packet_matches(decision, active, "active_packet_id"):
        errors.append(
            "Typed agent_loop_decision active packet does not match "
            f"agent_work_board for {key}: work_board={active}; "
            f"decision={decision_active or 'none'}"
        )
    attention = coerce_text(row.get("attention_packet_id"))
    decision_attention = coerce_text(decision.get("attention_packet_id"))
    if attention and not _decision_packet_matches(
        decision,
        attention,
        "attention_packet_id",
    ):
        errors.append(
            "Typed agent_loop_decision attention packet does not match "
            f"agent_work_board for {key}: work_board={attention}; "
            f"decision={decision_attention or 'none'}"
        )
    return errors


def _decision_packet_matches(
    decision: Mapping[str, object],
    expected_packet_id: str,
    field: str,
) -> bool:
    if coerce_text(decision.get(field)) == expected_packet_id:
        return True
    return coerce_text(decision.get("legacy_unscoped_packet_id")) == expected_packet_id


def pending_packet_agents(
    agents: Mapping[str, object],
    packet_rows: list[Mapping[str, object]] | None = None,
) -> list[str]:
    """Return actors with typed pending packets that should wake agent loops."""
    packet_index = _packet_index(packet_rows or [])
    pending: list[str] = []
    for agent_id, row in agents.items():
        if not isinstance(row, Mapping):
            continue
        packets = row.get("pending_packets_to_me")
        if not isinstance(packets, list):
            continue
        packet_ids = [coerce_text(packet_id) for packet_id in packets]
        if _has_runtime_attention_packet(packet_ids, packet_index):
            pending.append(str(agent_id))
    return sorted(pending)


def _packet_rows(payload: Mapping[str, object]) -> list[Mapping[str, object]]:
    rows = payload.get("packets")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _packet_index(
    packet_rows: list[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in packet_rows:
        packet_id = coerce_text(row.get("packet_id"))
        if packet_id:
            indexed[packet_id] = row
    return indexed


def _has_runtime_attention_packet(
    packet_ids: list[str],
    packet_index: Mapping[str, Mapping[str, object]],
) -> bool:
    for packet_id in packet_ids:
        if not packet_id:
            continue
        packet = packet_index.get(packet_id)
        if packet is None:
            return True
        if _requires_runtime_loop_attention(packet):
            return True
    return False


def _requires_runtime_loop_attention(packet: Mapping[str, object]) -> bool:
    if coerce_text(packet.get("to_agent")) != "operator":
        return True
    if coerce_text(packet.get("kind")) != "system_notice":
        return True
    if bool(packet.get("approval_required")):
        return True
    requested_action = coerce_text(packet.get("requested_action"))
    policy_hint = coerce_text(packet.get("policy_hint"))
    return requested_action not in {"", "review_only"} or policy_hint not in {
        "",
        "review_only",
    }


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
