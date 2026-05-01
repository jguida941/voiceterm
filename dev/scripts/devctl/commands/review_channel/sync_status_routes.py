"""Route-scoped active packet rows for sync-status output."""

from __future__ import annotations


def canonical_active_packet_routes(
    *,
    review_state: dict[str, object],
    target_agent: str = "",
) -> list[dict[str, object]]:
    """Return per-role/session active packet rows for scoped consumers."""
    from ...review_channel.active_packet_authority import (
        current_active_packet_for_agent,
    )

    work_board = review_state.get("agent_work_board")
    rows = work_board.get("rows") if isinstance(work_board, dict) else []
    if not isinstance(rows, list):
        return []
    routes: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        actor_id = str(row.get("actor_id") or "").strip()
        if not actor_id or (target_agent and actor_id != target_agent):
            continue
        role = str(row.get("role") or "").strip()
        session_id = str(row.get("session_id") or "").strip()
        key = (actor_id, role, session_id)
        if key in seen:
            continue
        seen.add(key)
        routes.append(
            {
                "actor_id": actor_id,
                "role": role,
                "session_id": session_id,
                "active_packet_id": current_active_packet_for_agent(
                    review_state,
                    actor_id,
                    target_role=role,
                    target_session_id=session_id,
                ),
                "route_key": "|".join(key),
            }
        )
    queue_route = _queue_target_route(review_state, target_agent=target_agent)
    if queue_route:
        key = (
            str(queue_route.get("actor_id") or ""),
            str(queue_route.get("role") or ""),
            str(queue_route.get("session_id") or ""),
        )
        if key not in seen:
            routes.append(queue_route)
    return routes


def _queue_target_route(
    review_state: dict[str, object],
    *,
    target_agent: str,
) -> dict[str, object]:
    queue = review_state.get("queue")
    source = queue.get("derived_next_instruction_source") if isinstance(queue, dict) else {}
    if not isinstance(source, dict):
        return {}
    actor_id = str(source.get("to_agent") or "").strip()
    if not actor_id or (target_agent and actor_id != target_agent):
        return {}
    role = str(source.get("target_role") or "").strip()
    session_id = str(source.get("target_session_id") or "").strip()
    packet_id = str(source.get("packet_id") or "").strip()
    if not packet_id or not (role or session_id):
        return {}
    return {
        "actor_id": actor_id,
        "role": role,
        "session_id": session_id,
        "active_packet_id": packet_id,
        "route_key": "|".join([actor_id, role, session_id]),
        "source": "queue.derived_next_instruction_source",
    }
