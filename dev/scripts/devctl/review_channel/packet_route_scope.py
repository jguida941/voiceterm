"""Actor-role/session route-scope helpers for review packets."""

from __future__ import annotations

from collections.abc import Mapping

from .packet_text_fields import clean_optional_text

_ROLE_ALIASES = dict(
    coder="implementer",
    coding="implementer",
    implementation="implementer",
    implementer="implementer",
    review="reviewer",
    reviewer="reviewer",
    dashboard="dashboard",
    observer="dashboard",
    watcher="dashboard",
    operator="operator",
    remote_operator="operator",
    subagent="subagent",
)


def normalize_packet_route_role(value: object) -> str:
    """Normalize packet route roles for target-role comparisons."""
    role = clean_optional_text(value) or ""
    if not role:
        return ""
    key = role.lower().replace("-", "_").replace(" ", "_")
    return _ROLE_ALIASES.get(key, key)


def packet_route_matches_scope(
    packet: Mapping[str, object],
    *,
    target_role: object = "",
    target_session_id: object = "",
) -> bool:
    """Return whether ``packet`` is visible to the scoped actor/session."""
    packet_role = normalize_packet_route_role(packet.get("target_role"))
    scope_role = normalize_packet_route_role(target_role)
    if packet_role and packet_role != scope_role:
        return False

    packet_session = clean_optional_text(packet.get("target_session_id")) or ""
    scope_session = clean_optional_text(target_session_id) or ""
    return not packet_session or packet_session == scope_session
