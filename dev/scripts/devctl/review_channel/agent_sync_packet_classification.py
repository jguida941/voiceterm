"""Packet classification helpers for the agent-sync projection."""

from __future__ import annotations

from .agent_sync_models import ACTIVE_LIFECYCLE_STATES
from .agent_packet_ranking import max_packet_event_rank
from .event_models import event_id_rank as _event_id_rank
from .packet_contract import packet_route_matches_scope
from .packet_terminal_lifecycle_states import TERMINAL_LIFECYCLE_STATES
from .pending_packets import live_pending_packets

_STALE_ACTIVE_PACKET_RANK_GAP = 1000
_ATTENTION_LIFECYCLE_PRIORITY: dict[str, int] = {
    "delivery_pending": 4,
    "execution_pending": 3,
    "apply_pending_after_execution": 3,
    "acknowledged": 2,
    "pending": 2,
    "in_progress": 1,
}
_EXECUTING_LIFECYCLES: frozenset[str] = frozenset(
    {"in_progress", "execution_pending", "apply_pending_after_execution"}
)


def _classify_active_split(
    *,
    agent_id: str,
    packet_rows: list[dict[str, object]],
) -> tuple[list[str], list[str]]:
    """Return delivery-pending and executing action-request packet ids."""
    head_rank = max_packet_event_rank(packet_rows)
    delivery_pending: list[str] = []
    executing: list[str] = []
    for row in packet_rows:
        if not _is_live_action_request_for_agent(row, agent_id):
            continue
        if not packet_route_matches_scope(row):
            continue
        packet_id = str(row.get("packet_id") or "")
        lifecycle = str(row.get("lifecycle_current_state") or "")
        rank = _event_id_rank(str(row.get("latest_event_id") or ""))
        if _is_stale_rank(head_rank, rank):
            continue
        if lifecycle == "delivery_pending":
            delivery_pending.append(packet_id)
            continue
        if lifecycle in _EXECUTING_LIFECYCLES and str(
            row.get("execution_started_by") or ""
        ).strip():
            executing.append(packet_id)
    return delivery_pending, executing


def _select_attention_packet(
    *,
    agent_id: str,
    packet_rows: list[dict[str, object]],
) -> str:
    """Pick the highest-priority live action_request for an unscoped agent."""
    head_rank = max_packet_event_rank(packet_rows)
    candidates: list[tuple[int, int, str]] = []
    for row in packet_rows:
        if not _is_live_action_request_for_agent(row, agent_id):
            continue
        if not packet_route_matches_scope(row):
            continue
        packet_id = str(row.get("packet_id") or "")
        lifecycle = str(row.get("lifecycle_current_state") or "")
        priority = _ATTENTION_LIFECYCLE_PRIORITY.get(lifecycle, 0)
        rank = _event_id_rank(str(row.get("latest_event_id") or ""))
        if priority and not _is_stale_rank(head_rank, rank):
            candidates.append((priority, rank, packet_id))
    if not candidates:
        return ""
    candidates.sort(reverse=True)
    return candidates[0][2]


def _classify_inbound_packets(
    *,
    agent_id: str,
    packet_rows: list[dict[str, object]],
) -> tuple[list[str], list[str]]:
    """Return pending inventory and unscoped active action-request ids."""
    head_rank = max_packet_event_rank(packet_rows)
    live_pending_ids = _live_pending_packet_ids(packet_rows)
    pending: list[str] = []
    active: list[str] = []
    for row in packet_rows:
        if str(row.get("to_agent") or "") != agent_id:
            continue
        packet_id = str(row.get("packet_id") or "")
        lifecycle = str(row.get("lifecycle_current_state") or "")
        if not packet_id or lifecycle in TERMINAL_LIFECYCLE_STATES:
            continue
        status = str(row.get("status") or "").strip()
        kind = str(row.get("kind") or "")
        if packet_id in live_pending_ids:
            pending.append(packet_id)
            if kind != "action_request":
                continue
        elif status == "pending":
            continue
        elif status == "" and lifecycle in ("", "pending", "delivery_pending"):
            pending.append(packet_id)
            if kind != "action_request":
                continue
        elif status:
            continue
        if not packet_route_matches_scope(row):
            continue
        if kind == "action_request" and lifecycle in ACTIVE_LIFECYCLE_STATES:
            rank = _event_id_rank(str(row.get("latest_event_id") or ""))
            if lifecycle != "delivery_pending" and not _is_stale_rank(head_rank, rank):
                active.append(packet_id)
    return pending, active


def _derive_awaiting(
    *,
    agent_id: str,
    packet_rows: list[dict[str, object]],
) -> tuple[str, str]:
    """Weakly derive the newest unresolved outbound action_request."""
    candidates: list[tuple[int, str, dict[str, object]]] = []
    for row in packet_rows:
        if str(row.get("from_agent") or "") != agent_id:
            continue
        if str(row.get("kind") or "") != "action_request":
            continue
        if str(row.get("lifecycle_current_state") or "") in TERMINAL_LIFECYCLE_STATES:
            continue
        if str(row.get("status") or "").strip() not in ("", "pending"):
            continue
        packet_id = str(row.get("packet_id") or "")
        rank = _event_id_rank(str(row.get("latest_event_id") or ""))
        candidates.append((rank, packet_id, row))
    if not candidates:
        return "", ""
    newest = sorted(candidates, reverse=True)[0][2]
    return str(newest.get("packet_id") or ""), str(newest.get("to_agent") or "")


def _is_live_action_request_for_agent(
    row: dict[str, object],
    agent_id: str,
) -> bool:
    if str(row.get("to_agent") or "") != agent_id:
        return False
    if str(row.get("kind") or "") != "action_request":
        return False
    if not str(row.get("packet_id") or ""):
        return False
    lifecycle = str(row.get("lifecycle_current_state") or "")
    return lifecycle not in TERMINAL_LIFECYCLE_STATES


def _is_stale_rank(head_rank: int, row_rank: int) -> bool:
    return (
        head_rank > 0
        and row_rank > 0
        and (head_rank - row_rank) > _STALE_ACTIVE_PACKET_RANK_GAP
    )


def _live_pending_packet_ids(packet_rows: list[dict[str, object]]) -> frozenset[str]:
    return frozenset(
        str(packet.get("packet_id") or "").strip()
        for packet in live_pending_packets(packet_rows)
        if isinstance(packet, dict) and str(packet.get("packet_id") or "").strip()
    )
