"""Packet selection helpers for typed agent work-board rows."""

from __future__ import annotations

from .agent_sync_models import (
    TERMINAL_NON_SUCCESS_STATES,
    TERMINAL_SUCCESS_STATES,
)
from .agent_packet_ranking import max_packet_event_rank
from .event_models import event_id_rank as _event_id_rank
from .packet_contract import packet_route_matches_scope


_TERMINAL_LIFECYCLE_STATES: frozenset[str] = (
    TERMINAL_NON_SUCCESS_STATES | TERMINAL_SUCCESS_STATES
)
_STALE_LIFECYCLE_RANK_GAP = 1000
_ACTIVE_LIFECYCLE_PRIORITY: dict[str, int] = {
    "delivery_pending": 4,
    "execution_pending": 3,
    "apply_pending_after_execution": 3,
    "acknowledged": 2,
    "pending": 2,
    "in_progress": 1,
}
_EXECUTING_LIFECYCLES_FROZENSET: frozenset[str] = frozenset(
    {"in_progress", "execution_pending", "apply_pending_after_execution"}
)


def _select_executing_packet_id(
    *,
    actor_id: str,
    packet_rows: list[dict[str, object]],
    target_role: object = "",
    target_session_id: object = "",
) -> str:
    head_rank = max_packet_event_rank(packet_rows)
    candidates: list[tuple[int, str]] = []
    for row in packet_rows:
        if not _packet_matches_actor_scope(
            row,
            actor_id=actor_id,
            target_role=target_role,
            target_session_id=target_session_id,
        ):
            continue
        packet_id = str(row.get("packet_id") or "").strip()
        lifecycle = str(row.get("lifecycle_current_state") or "")
        if not packet_id or lifecycle not in _EXECUTING_LIFECYCLES_FROZENSET:
            continue
        started_by = str(row.get("execution_started_by") or "").strip()
        if not started_by or started_by != actor_id:
            continue
        rank = _event_id_rank(str(row.get("latest_event_id") or ""))
        if _stale_by_rank_gap(head_rank, rank):
            continue
        candidates.append((rank, packet_id))
    if not candidates:
        return ""
    candidates.sort(reverse=True)
    return candidates[0][1]


def _select_current_active_packet_id(
    *,
    actor_id: str,
    packet_rows: list[dict[str, object]],
    target_role: object = "",
    target_session_id: object = "",
) -> str:
    current_head_rank = max_packet_event_rank(packet_rows)
    candidates: list[tuple[int, int, str]] = []
    for row in packet_rows:
        if not _packet_matches_actor_scope(
            row,
            actor_id=actor_id,
            target_role=target_role,
            target_session_id=target_session_id,
        ):
            continue
        packet_id = str(row.get("packet_id") or "").strip()
        lifecycle = str(row.get("lifecycle_current_state") or "")
        if not packet_id or lifecycle in _TERMINAL_LIFECYCLE_STATES:
            continue
        priority = _ACTIVE_LIFECYCLE_PRIORITY.get(lifecycle, 0)
        if priority == 0:
            continue
        rank = _event_id_rank(str(row.get("latest_event_id") or ""))
        if _stale_by_rank_gap(current_head_rank, rank):
            continue
        candidates.append((priority, rank, packet_id))

    if not candidates:
        return ""
    candidates.sort(reverse=True)
    return candidates[0][2]


def plan_row_for(
    *,
    packet_id: str,
    packet_rows: list[dict[str, object]],
) -> str:
    if not packet_id:
        return ""
    for row in packet_rows:
        if str(row.get("packet_id") or "") != packet_id:
            continue
        target_kind = str(row.get("target_kind") or "").strip()
        target_ref = str(row.get("target_ref") or "").strip()
        if target_kind == "plan" and target_ref:
            return target_ref
        plan_proposal = row.get("plan_proposal")
        if isinstance(plan_proposal, dict):
            proposal_target = str(plan_proposal.get("target_ref") or "").strip()
            if proposal_target:
                return proposal_target
        return ""
    return ""


def _packet_matches_actor_scope(
    row: dict[str, object],
    *,
    actor_id: str,
    target_role: object,
    target_session_id: object,
) -> bool:
    return (
        str(row.get("to_agent") or "") == actor_id
        and str(row.get("kind") or "") == "action_request"
        and packet_route_matches_scope(
            row,
            target_role=target_role,
            target_session_id=target_session_id,
        )
    )


def _stale_by_rank_gap(head_rank: int, rank: int) -> bool:
    return head_rank > 0 and rank > 0 and (head_rank - rank) > _STALE_LIFECYCLE_RANK_GAP

