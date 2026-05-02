"""Agent-loop decision projection for typed review-state consumers."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.value_coercion import (
    coerce_mapping as _mapping,
    coerce_text as _text,
)
from .agent_loop_decision_attention import (
    apply_agent_sync_session_attention_disambiguation,
    apply_scoped_attention_to_ambiguous_packet_attention,
)
from .agent_loop_decision_queue_targets import queue_target_decisions


def agent_loop_decisions_for_work_board(
    *,
    review_state: Mapping[str, object],
    work_board: Mapping[str, object],
    target_agent: str = "",
    dashboard: Mapping[str, object] | None = None,
) -> list[dict[str, object]]:
    """Resolve one ``AgentLoopDecision`` per typed work-board row."""
    from ..runtime.agent_loop_decision import build_agent_loop_decision

    dashboard_payload = dashboard if dashboard is not None else _dashboard_from_review_state(review_state)
    rows = work_board.get("rows")
    if not isinstance(rows, list):
        return []

    decisions: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        actor_id = _text(row.get("actor_id"))
        role = _text(row.get("role"))
        session_id = _text(row.get("session_id"))
        if not actor_id or (target_agent and actor_id != target_agent):
            continue
        key = (actor_id, role, session_id)
        if key in seen:
            continue
        seen.add(key)
        decision = build_agent_loop_decision(
            review_state=review_state,
            dashboard=dashboard_payload,
            actor_id=actor_id,
            actor_role=role,
            session_id=session_id,
        ).to_dict()
        decision["source_work_board_row"] = _source_row(row, key)
        decisions.append(decision)
    for key, decision in queue_target_decisions(
        review_state=review_state,
        dashboard=dashboard_payload,
        target_agent=target_agent,
        seen_keys=seen,
    ):
        seen.add(key)
        decisions.append(decision)
    return decisions


def _dashboard_from_review_state(
    review_state: Mapping[str, object],
) -> dict[str, object]:
    top_blocker, next_action = _blocker_from_review_state(review_state)
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    return {
        "control_plane": {
            "top_blocker": top_blocker,
            "next_action": next_action,
        },
        "now": {
            "top_blocker": top_blocker,
            "next_action": next_action,
        },
        "ack_freshness": {
            "current_instruction_revision": _text(
                _mapping(review_state.get("current_session")).get(
                    "current_instruction_revision"
                )
            ),
        },
        "agent_runtime_clock": dict(
            _mapping(reviewer_runtime.get("agent_runtime_clock"))
        ),
        "packet_attention": dict(_mapping(reviewer_runtime.get("packet_attention"))),
        "authority_snapshot": dict(_mapping(review_state.get("authority_snapshot"))),
        "session_posture": dict(_mapping(reviewer_runtime.get("session_posture"))),
    }


def _blocker_from_review_state(
    review_state: Mapping[str, object],
) -> tuple[str, str]:
    attention = _mapping(review_state.get("attention"))
    status = _text(attention.get("status"))
    if status == "checkpoint_required":
        blocker_kind = _checkpoint_blocker_kind(review_state)
        return (
            f"startup authority: {blocker_kind}",
            f"checkpoint_blocked_by_startup_authority:{blocker_kind}",
        )

    recovery = _mapping(review_state.get("recovery_assessment"))
    diagnosis = _mapping(recovery.get("diagnosis"))
    root_cause = _text(diagnosis.get("root_cause"))
    if status and status not in {"ok", "healthy", "none"}:
        return status, _text(_mapping(recovery.get("decision")).get("command"))
    if root_cause:
        return root_cause, _text(_mapping(recovery.get("decision")).get("command"))

    current_session = _mapping(review_state.get("current_session"))
    findings = _text(current_session.get("open_findings"))
    if findings and findings.lower() != "none":
        return findings.splitlines()[0].lstrip("- ").strip(), ""
    return "none", ""


def _checkpoint_blocker_kind(review_state: Mapping[str, object]) -> str:
    recovery = _mapping(review_state.get("recovery_assessment"))
    diagnosis = _mapping(recovery.get("diagnosis"))
    causes = diagnosis.get("supporting_causes")
    cause_text = " ".join(_text(item) for item in causes or ())
    if "import_index_atomicity" in cause_text:
        return "import_index_atomicity"
    if "checkpoint_budget_exhausted" in cause_text:
        return "staged_index_budget_exceeded"
    return "checkpoint_required"


def _source_row(
    row: Mapping[str, object],
    key: tuple[str, str, str],
) -> dict[str, object]:
    return {
        "route_key": "|".join(key),
        "status": _text(row.get("status")),
        "confidence_class": _text(row.get("confidence_class")),
        "source_event_id": _text(row.get("source_event_id")),
        "source_surface": _text(row.get("source_surface")),
    }


__all__ = [
    "agent_loop_decisions_for_work_board",
    "apply_scoped_attention_to_ambiguous_packet_attention",
    "apply_agent_sync_session_attention_disambiguation",
]
