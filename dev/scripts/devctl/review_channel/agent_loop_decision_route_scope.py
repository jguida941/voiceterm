"""Route freshness helpers for queue-targeted agent-loop decisions."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.anchor_scope import (
    ANCHOR_SCOPE_PLAN,
    ANCHOR_SCOPE_ROLE,
    effective_anchor_scope,
)
from ..runtime.review_packet_inbox_actionable import (
    is_actionable as _is_runtime_actionable_packet,
)
from ..runtime.review_packet_inbox_liveness import (
    is_live_pending as _is_live_pending_packet,
)
from ..runtime.value_coercion import coerce_mapping, coerce_text
from .packet_loop_attention import packet_requires_runtime_attention
from .packet_route_scope import packet_route_matches_scope

_ROLE_ALIASES = dict(
    (
        ("coder", "implementer"),
        ("coding", "implementer"),
        ("implementation", "implementer"),
        ("implementer", "implementer"),
        ("review", "reviewer"),
        ("reviewer", "reviewer"),
        ("dashboard", "dashboard"),
        ("observer", "dashboard"),
        ("operator", "operator"),
    )
)


def coerce_count(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def first_pending_loop_attention_packet_for_actor(
    review_state: Mapping[str, object],
    actor_id: str,
    *,
    packet_ids: tuple[str, ...] = (),
) -> Mapping[str, object] | None:
    """Return the first pending packet that should wake ``actor_id``."""
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return None
    packet_id_filter = set(packet_ids)
    fallback: Mapping[str, object] | None = None
    for row in packets:
        if not isinstance(row, Mapping):
            continue
        if packet_id_filter and coerce_text(row.get("packet_id")) not in packet_id_filter:
            continue
        if coerce_text(row.get("to_agent")) != actor_id:
            continue
        if not _is_live_pending_packet(row):
            continue
        if not packet_targets_fresh_route(
            row,
            review_state=review_state,
            actor_id=actor_id,
            allow_actor_pending_pressure=bool(packet_id_filter),
        ):
            continue
        if not packet_requires_runtime_attention(
            row,
            actor=actor_id,
            role=role_for_packet(actor_id, row),
            session=coerce_text(row.get("target_session_id")),
        ):
            continue
        if _is_runtime_actionable_packet(row):
            return row
        if fallback is None:
            fallback = row
    return fallback


def packet_targets_fresh_route(
    packet: Mapping[str, object],
    *,
    review_state: Mapping[str, object],
    actor_id: str,
    allow_actor_pending_pressure: bool = False,
) -> bool:
    target_session = coerce_text(packet.get("target_session_id"))
    if not target_session:
        return True
    if effective_anchor_scope(packet) in {ANCHOR_SCOPE_ROLE, ANCHOR_SCOPE_PLAN}:
        return True
    routes = fresh_session_routes(review_state, actor_id=actor_id)
    if not routes:
        if has_session_route_evidence(review_state, actor_id=actor_id):
            return False
        if allow_actor_pending_pressure:
            return True
        return True
    return any(
        packet_route_matches_scope(
            packet,
            target_role=route.get("role"),
            target_session_id=route.get("session_id"),
        )
        for route in routes
    )


def fresh_session_routes(
    review_state: Mapping[str, object],
    *,
    actor_id: str,
) -> tuple[Mapping[str, object], ...]:
    work_board = coerce_mapping(review_state.get("agent_work_board"))
    rows = work_board.get("rows")
    if not isinstance(rows, list):
        return ()
    routes: list[Mapping[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if coerce_text(row.get("actor_id")) != actor_id:
            continue
        if route_freshness(row) != "fresh":
            continue
        role = normalize_role(row.get("role"))
        session_id = coerce_text(row.get("session_id"))
        if not session_id:
            continue
        key = (role, session_id)
        if key in seen:
            continue
        seen.add(key)
        routes.append(dict((("role", role), ("session_id", session_id))))
    return tuple(routes)


def has_session_route_evidence(
    review_state: Mapping[str, object],
    *,
    actor_id: str,
) -> bool:
    work_board = coerce_mapping(review_state.get("agent_work_board"))
    rows = work_board.get("rows")
    if not isinstance(rows, list):
        return False
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if coerce_text(row.get("actor_id")) != actor_id:
            continue
        if coerce_text(row.get("session_id")):
            return True
    return False


def route_freshness(row: Mapping[str, object]) -> str:
    confidence = coerce_text(row.get("confidence_class"))
    status = coerce_text(row.get("status"))
    idle_seconds = coerce_count(row.get("idle_seconds"))
    stale_after = coerce_count(row.get("stale_after_seconds"))
    if confidence == "stale" or (stale_after > 0 and idle_seconds > stale_after):
        return "stale"
    if status in {"working", "polling", "blocked", "checkpointed"}:
        return "fresh"
    if status == "idle":
        return "idle"
    return "unknown"


def normalize_role(value: object) -> str:
    role = coerce_text(value)
    if not role:
        return ""
    key = role.lower().replace("-", "_").replace(" ", "_")
    return _ROLE_ALIASES.get(key, key)


def role_for_packet(actor_id: str, packet: Mapping[str, object]) -> str:
    role = normalize_role(packet.get("target_role"))
    if role:
        return role
    return "operator" if actor_id == "operator" else ""
