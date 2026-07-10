"""Actor-role and identity helpers for the authority snapshot reducer."""

from __future__ import annotations

from collections.abc import Mapping

from .action_routing import normalize_agent_lane
from .authority_snapshot_core import _mapping
from .role_profile import default_provider_for_role, normalize_tandem_role


def authority_actor_role(
    *,
    payload: Mapping[str, object],
    caller_role: object,
) -> str:
    """Resolve the active actor role from the startup payload or caller lane."""
    lane = str(_mapping(payload.get("agent_lane")).get("lane") or "").strip().lower()
    if lane:
        return lane
    return normalize_agent_lane(caller_role)


def authority_actor_identity(
    *,
    coordination: Mapping[str, object],
    actor_role: str,
) -> str:
    """Resolve the current actor identity from coordination actors."""
    desired_roles = _actor_identity_roles(actor_role)
    identity = _matching_actor_identity(
        coordination.get("actors"),
        desired_roles=desired_roles,
        live_only=True,
    )
    if identity:
        return identity
    identity = _matching_actor_identity(
        coordination.get("actors"),
        desired_roles=desired_roles,
        live_only=False,
    )
    if identity:
        return identity
    if actor_role in {"dashboard", "observer"}:
        return "operator"
    normalized_role = normalize_tandem_role(actor_role)
    if normalized_role is not None:
        return default_provider_for_role(normalized_role)
    return actor_role


def _actor_identity_roles(actor_role: str) -> set[str]:
    normalized_lane = normalize_agent_lane(actor_role)
    if normalized_lane in {"dashboard", "observer"}:
        return {"operator"}
    normalized_role = normalize_tandem_role(normalized_lane)
    if normalized_role is None:
        return {normalized_lane}
    return {normalized_role.value}


def _matching_actor_identity(
    actors: object,
    *,
    desired_roles: set[str],
    live_only: bool,
) -> str:
    if not isinstance(actors, list):
        return ""
    for row in actors:
        actor = _mapping(row)
        presence = str(actor.get("presence") or "").strip().lower()
        if live_only and presence != "live":
            continue
        role = str(actor.get("role") or "").strip().lower()
        normalized_role = normalize_tandem_role(role)
        role_key = normalized_role.value if normalized_role is not None else role
        if role_key not in desired_roles:
            continue
        provider = str(actor.get("provider") or "").strip()
        actor_id = str(actor.get("actor_id") or "").strip()
        if provider or actor_id:
            return provider or actor_id
    return ""
