"""Resolve packet post routing against typed agent session state."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace

from .packet_contract import (
    PacketPostRequest,
    normalize_packet_route_role,
    packet_route_matches_scope,
)
from .packet_target_validation import RUNTIME_ACTION_REQUEST_ACTIONS


def resolve_packet_post_route_scope(
    request: PacketPostRequest,
    *,
    review_state: Mapping[str, object] | None,
) -> PacketPostRequest:
    """Return ``request`` with a unique session route or fail closed.

    Packet transport may still address an agent provider like ``claude`` or
    ``codex``, but executable runtime routing must address exactly one fresh
    session whenever more than one matching session is live.
    """
    state = review_state if isinstance(review_state, Mapping) else {}
    nodes = _fresh_session_nodes(state, actor=request.to_agent)
    if not nodes:
        return request

    scoped_matches = tuple(
        node
        for node in nodes
        if packet_route_matches_scope(
            {
                "target_role": request.target.target_role,
                "target_session_id": request.target.target_session_id,
            },
            target_role=node.get("actor_role"),
            target_session_id=node.get("session_id"),
        )
    )
    if request.target.target_session_id:
        session_matches = tuple(
            node
            for node in nodes
            if str(node.get("session_id") or "").strip()
            == request.target.target_session_id
        )
        if len(session_matches) != 1:
            raise ValueError(
                "Packet target_session_id does not resolve to one fresh "
                f"{request.to_agent} session: {request.target.target_session_id}"
            )
        resolved = session_matches[0]
        role = _resolved_role(request.target.target_role, resolved)
        return _replace_route_scope(
            request,
            target_role=role,
            target_session_id=str(resolved.get("session_id") or ""),
        )

    if request.target.target_role:
        if len(scoped_matches) == 1:
            resolved = scoped_matches[0]
            return _replace_route_scope(
                request,
                target_role=_resolved_role(request.target.target_role, resolved),
                target_session_id=str(resolved.get("session_id") or ""),
            )
        if _non_runtime_action_request(request):
            return request
        raise ValueError(
            "Packet target_role does not resolve to exactly one fresh "
            f"{request.to_agent} session; add --target-session-id."
        )

    if len(nodes) == 1:
        resolved = nodes[0]
        return _replace_route_scope(
            request,
            target_role=str(resolved.get("actor_role") or ""),
            target_session_id=str(resolved.get("session_id") or ""),
        )

    raise ValueError(
        f"Packet to-agent {request.to_agent!r} has multiple fresh sessions; "
        "add --target-role and --target-session-id."
    )


def _non_runtime_action_request(request: PacketPostRequest) -> bool:
    return (
        request.kind == "action_request"
        and request.requested_action not in RUNTIME_ACTION_REQUEST_ACTIONS
    )


def _replace_route_scope(
    request: PacketPostRequest,
    *,
    target_role: str,
    target_session_id: str,
) -> PacketPostRequest:
    return replace(
        request,
        target=replace(
            request.target,
            target_role=target_role,
            target_session_id=target_session_id,
        ),
    )


def _resolved_role(requested_role: str, node: Mapping[str, object]) -> str:
    return normalize_packet_route_role(requested_role) or str(
        node.get("actor_role") or ""
    )


def _fresh_session_nodes(
    review_state: Mapping[str, object],
    *,
    actor: str,
) -> tuple[Mapping[str, object], ...]:
    rows = _work_board_rows(review_state)
    nodes: list[Mapping[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if str(row.get("actor_id") or "") != actor:
            continue
        session_id = str(row.get("session_id") or "").strip()
        if not session_id:
            continue
        if _freshness_state(row) != "fresh":
            continue
        role = normalize_packet_route_role(row.get("role"))
        key = (role, session_id)
        if key in seen:
            continue
        seen.add(key)
        nodes.append(
            {
                "actor_id": actor,
                "actor_role": role,
                "session_id": session_id,
            }
        )
    return tuple(nodes)


def _work_board_rows(
    review_state: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = _mapping(review_state.get("agent_work_board")).get("rows")
    if not rows:
        rows = _mapping(review_state.get("work_board")).get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _freshness_state(row: Mapping[str, object]) -> str:
    confidence = str(row.get("confidence_class") or "").strip()
    status = str(row.get("status") or "").strip()
    idle_seconds = _int(row.get("idle_seconds"))
    stale_after = _int(row.get("stale_after_seconds"))
    if confidence == "stale" or (stale_after > 0 and idle_seconds > stale_after):
        return "stale"
    if status in {"working", "polling", "blocked", "checkpointed"}:
        return "fresh"
    if status == "idle":
        return "idle"
    return "unknown"


def _int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value or "").strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
