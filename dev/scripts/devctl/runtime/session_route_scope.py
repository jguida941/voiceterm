"""Route-scope matching for session continuation packets."""

from __future__ import annotations

from collections.abc import Mapping

from .plan_ref import canonical_plan_ref
from .anchor_scope import (
    ANCHOR_SCOPE_PLAN,
    ANCHOR_SCOPE_ROLE,
    ANCHOR_SCOPE_SESSION,
    effective_anchor_scope,
)


_IMPLEMENTER_ALIASES = frozenset(
    (
        "coder",
        "coding",
        "implementation",
        "implementer",
    )
)
_REVIEWER_ALIASES = frozenset(("review", "reviewer"))
_DASHBOARD_ALIASES = frozenset(("dashboard", "observer", "watcher"))
_OPERATOR_ALIASES = frozenset(("operator", "remote_operator"))
_SUBAGENT_ALIASES = frozenset(("subagent",))


def packet_matches_session_route(
    packet: Mapping[str, object],
    *,
    session_id: str,
    actor: str = "",
    actor_role: str = "",
    target_ref: str = "",
) -> bool:
    """Return whether a packet is scoped to the active actor/session route."""
    target_actor = _text(packet.get("to_agent")).lower()
    normalized_actor = _text(actor).lower()
    if target_actor and (not normalized_actor or target_actor != normalized_actor):
        return False

    target_role = normalize_route_role(packet.get("target_role"))
    normalized_role = normalize_route_role(actor_role)
    if target_role and (not normalized_role or target_role != normalized_role):
        return False

    target_session = _text(packet.get("target_session_id"))
    anchor_scope = effective_anchor_scope(packet)
    if anchor_scope == ANCHOR_SCOPE_SESSION:
        return bool(target_session) and bool(session_id) and target_session == session_id
    if anchor_scope == ANCHOR_SCOPE_ROLE:
        return True
    if anchor_scope == ANCHOR_SCOPE_PLAN:
        packet_target_ref = canonical_plan_ref(packet.get("target_ref"))
        scoped_target_ref = canonical_plan_ref(target_ref)
        return bool(packet_target_ref) and bool(scoped_target_ref) and (
            packet_target_ref == scoped_target_ref
        )
    if target_session and (not session_id or target_session != session_id):
        return False
    return True


def normalize_route_role(value: object) -> str:
    """Normalize packet target-role aliases without importing review-channel code."""
    role = _text(value).lower().replace("-", "_").replace(" ", "_")
    if role in _IMPLEMENTER_ALIASES:
        return "implementer"
    if role in _REVIEWER_ALIASES:
        return "reviewer"
    if role in _DASHBOARD_ALIASES:
        return "dashboard"
    if role in _OPERATOR_ALIASES:
        return "operator"
    if role in _SUBAGENT_ALIASES:
        return "subagent"
    return role


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "normalize_route_role",
    "packet_matches_session_route",
]
