"""Canonical predicate for "what is agent X actively working on right now?".

Per Codex rev_pkt_2326: review_state queue, bridge-poll, claude-loop,
sync-status MD, dashboard typed-state, and recovery_eligibility currently
DISAGREE on the live answer. queue picks rev_pkt_2270 while work-board
shows Claude executing rev_pkt_2288. The architectural fix is a single
canonical predicate that all consumers call.

Reading order, highest authority first:

1. ``agent_work_board.rows`` — the typed observed-runtime evidence.
   When a work-board row exists for ``agent_id`` with non-empty
   ``active_packet_id``, that is the current active packet. The
   work-board projection (rev_pkt_2287/2293/2297/2324) already filters
   stale historical packets and validates against typed lifecycle.

2. ``agent_sync.agents[agent_id].active_action_requests_to_me`` — fall
   back to the v1 active list, but pick the NEWEST (highest event_id
   rank) survivor that's not in terminal lifecycle. Same selection logic
   as ``agent_work_board_projection._select_current_active_packet_id``
   but without the work-board's session-level decomposition.

NEVER reads from ``review_state.queue`` (the priority selector — picks
oldest matching packet), ``bridge`` (compatibility projection, not
authority), or ``current_session`` (legacy single-instruction surface).

This is the canonical answer. Consumers that diverge from it MUST
either consume this predicate or document a typed reason for the
disagreement (e.g., bridge-poll intentionally lags by one tick).
"""

from __future__ import annotations

from collections.abc import Mapping

from .event_models import event_id_rank as _event_id_rank
from .packet_contract import (
    normalize_packet_route_role,
    packet_route_matches_scope,
)


_TERMINAL_LIFECYCLE_STATES = frozenset(
    {"applied", "dismissed", "failed", "archived", "expired"}
)
_STALE_LIFECYCLE_RANK_GAP = 1000

# Per Codex rev_pkt_2396: delivery_pending must outrank in_progress so a
# freshly routed action_request wins over an older one the agent stalled on.
# Mirrors agent_work_board_projection._ACTIVE_LIFECYCLE_PRIORITY.
_ACTIVE_LIFECYCLE_PRIORITY: dict[str, int] = {
    "delivery_pending": 4,
    "execution_pending": 3,
    "apply_pending_after_execution": 3,
    "acknowledged": 2,
    "pending": 2,
    "in_progress": 1,
}


def current_active_packet_for_agent(
    review_state: Mapping[str, object] | None,
    agent_id: str,
    *,
    target_role: object = "",
    target_session_id: object = "",
) -> str:
    """Return the typed active packet_id for ``agent_id``, or empty string.

    Authority order:
    1. ``review_state["agent_work_board"]["rows"]`` rows where
       ``actor_id == agent_id`` and ``active_packet_id != ""``. When
       ``target_role`` or ``target_session_id`` is supplied, the row and
       packet must match that scoped identity. Picks the row whose
       ``active_packet_id`` has the highest event-id rank.
    2. ``review_state["agent_sync"]["agents"][agent_id].active_action_requests_to_me``
       newest non-terminal entry that matches the same scoped packet route.
    3. Empty string when no live active packet exists.
    """
    if not isinstance(review_state, Mapping) or not agent_id:
        return ""

    packets = review_state.get("packets")
    packet_rows = packets if isinstance(packets, (list, tuple)) else []

    work_board = review_state.get("agent_work_board")
    if isinstance(work_board, Mapping):
        candidate = _from_work_board(
            work_board,
            agent_id,
            packet_rows=packet_rows,
            target_role=target_role,
            target_session_id=target_session_id,
        )
        if candidate:
            return candidate

    agent_sync = review_state.get("agent_sync")
    if isinstance(agent_sync, Mapping):
        candidate = _from_agent_sync(
            agent_sync,
            agent_id,
            packet_rows=packet_rows,
            target_role=target_role,
            target_session_id=target_session_id,
        )
        if candidate:
            return candidate

    return ""


def _from_work_board(
    work_board: Mapping[str, object],
    agent_id: str,
    *,
    packet_rows: list,
    target_role: object = "",
    target_session_id: object = "",
) -> str:
    rows = work_board.get("rows")
    if not isinstance(rows, list):
        return ""
    candidates: list[tuple[int, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("actor_id") or "") != agent_id:
            continue
        if not _work_board_row_matches_scope(
            row,
            target_role=target_role,
            target_session_id=target_session_id,
        ):
            continue
        active = str(row.get("active_packet_id") or "").strip()
        if not active:
            continue
        packet = _packet_row_by_id(packet_rows, active)
        if packet is not None and not packet_route_matches_scope(
            packet,
            target_role=target_role,
            target_session_id=target_session_id,
        ):
            continue
        if packet is None and (target_role or target_session_id):
            continue
        rank = _event_id_rank(str(row.get("source_event_id") or ""))
        candidates.append((rank, active))
    if not candidates:
        return ""
    candidates.sort(reverse=True)
    return candidates[0][1]


def _from_agent_sync(
    agent_sync: Mapping[str, object],
    agent_id: str,
    *,
    packet_rows: list,
    target_role: object = "",
    target_session_id: object = "",
) -> str:
    """Pick the highest-priority live action_request for ``agent_id``.

    Per Codex rev_pkt_2396: the v1 ``active_action_requests_to_me``
    aggregate excludes ``delivery_pending``, so the previous fall-back
    iterated only over packets the aggregate already missed. The
    canonical predicate now consults ``packet_rows`` directly (mirroring
    ``agent_work_board_projection._select_current_active_packet_id``)
    so a freshly routed ``delivery_pending`` action_request outranks an
    older ``in_progress`` one of the same agent.
    """
    del agent_sync  # legacy aggregate hint no longer required for selection
    if not packet_rows:
        return ""

    current_head_rank = _max_packet_event_rank(packet_rows)

    candidates: list[tuple[int, int, str]] = []
    for row in packet_rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("to_agent") or "") != agent_id:
            continue
        if str(row.get("kind") or "") != "action_request":
            continue
        if not packet_route_matches_scope(
            row,
            target_role=target_role,
            target_session_id=target_session_id,
        ):
            continue
        packet_id = str(row.get("packet_id") or "").strip()
        if not packet_id:
            continue
        lifecycle = str(row.get("lifecycle_current_state") or "")
        if lifecycle in _TERMINAL_LIFECYCLE_STATES:
            continue
        priority = _ACTIVE_LIFECYCLE_PRIORITY.get(lifecycle, 0)
        if priority == 0:
            continue
        rank = _event_id_rank(str(row.get("latest_event_id") or ""))
        if (
            current_head_rank > 0
            and rank > 0
            and (current_head_rank - rank) > _STALE_LIFECYCLE_RANK_GAP
        ):
            continue
        candidates.append((priority, rank, packet_id))

    if not candidates:
        return ""
    candidates.sort(reverse=True)
    return candidates[0][2]


def _work_board_row_matches_scope(
    row: Mapping[str, object],
    *,
    target_role: object = "",
    target_session_id: object = "",
) -> bool:
    scope_role = normalize_packet_route_role(target_role)
    if scope_role:
        row_role = normalize_packet_route_role(row.get("role"))
        if row_role and row_role != scope_role:
            return False
    scope_session = str(target_session_id or "").strip()
    if scope_session:
        row_session = str(row.get("session_id") or "").strip()
        if row_session and row_session != scope_session:
            return False
    return True


def _packet_row_by_id(
    packet_rows: list,
    packet_id: str,
) -> Mapping[str, object] | None:
    for row in packet_rows:
        if isinstance(row, Mapping) and str(row.get("packet_id") or "") == packet_id:
            return row
    return None


def _max_packet_event_rank(packet_rows: list) -> int:
    best = -1
    for row in packet_rows:
        if not isinstance(row, Mapping):
            continue
        rank = _event_id_rank(str(row.get("latest_event_id") or ""))
        if rank > best:
            best = rank
    return best
