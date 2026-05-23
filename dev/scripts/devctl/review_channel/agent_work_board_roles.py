"""Role and capability resolution for agent work-board rows.

Provider names are not durable role authority.  A single provider can run
several sessions with different jobs, and a session can be a dashboard or
dogfood lane while another session of the same provider owns repo mutation.
This module keeps that boundary explicit for the work-board projection.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .packet_contract import normalize_packet_route_role

_MUTATION_CAPABILITIES = frozenset({"repo.stage", "repo.commit"})
_REVIEW_CAPABILITIES = frozenset({"review.checkpoint", "review.finding"})
_OBSERVE_CAPABILITIES = frozenset({"runtime.observe", "approval.commit"})


@dataclass(frozen=True, slots=True)
class RuntimeRoleResolution:
    """Resolved runtime role facts for one provider/session row."""

    role: str
    declared_role: str
    authority_role: str
    role_source: str
    role_scope: str
    mutation_mode: str
    granted_capabilities: tuple[str, ...]


class RuntimeRoleIndex:
    """Read-only role index derived from CollaborationSession authority."""

    def __init__(self, collaboration: Mapping[str, object] | None) -> None:
        self._collaboration = collaboration if isinstance(collaboration, Mapping) else {}
        self._authorities = _authority_rows(self._collaboration)
        self._participants = _participant_rows(self._collaboration)

    def resolve(
        self,
        *,
        actor_id: str,
        provider: str,
        declared_role: object = "",
        fallback_role: object = "",
    ) -> RuntimeRoleResolution:
        """Resolve one session row without falling back to provider identity."""
        actor = _text(actor_id) or _text(provider)
        declared = normalize_packet_route_role(declared_role)
        fallback = normalize_packet_route_role(fallback_role)
        capabilities = _capabilities_for_actor(self._authorities, actor)
        authority_role = _authority_role_for_actor(
            self._authorities,
            actor=actor,
            capabilities=capabilities,
        )
        if authority_role:
            return RuntimeRoleResolution(
                role=authority_role,
                declared_role=declared,
                authority_role=authority_role,
                role_source="actor_authority",
                role_scope="actor",
                mutation_mode=_mutation_mode_for_capabilities(capabilities),
                granted_capabilities=capabilities,
            )

        participant = _participant_for_actor(self._participants, actor)
        capture_mode = _text(participant.get("capture_mode")) if participant else ""
        participant_role = normalize_packet_route_role(
            participant.get("role") if participant else ""
        )
        if declared == "subagent":
            return RuntimeRoleResolution(
                role="subagent",
                declared_role=declared,
                authority_role="",
                role_source="session_declared_role",
                role_scope="session",
                mutation_mode="read_only",
                granted_capabilities=capabilities,
            )
        if capture_mode == "remote-control":
            remote_role = participant_role or declared or "operator"
            normalized = "dashboard" if remote_role == "operator" else remote_role
            return RuntimeRoleResolution(
                role=normalized,
                declared_role=declared or participant_role,
                authority_role="",
                role_source="remote_control_attachment",
                role_scope="session",
                mutation_mode="read_only",
                granted_capabilities=capabilities,
            )

        # A declared implementer without repo mutation authority is still the
        # implementer lane, but it is read-only until typed mutation authority
        # is present. Role identity routes packets; capabilities grant edits.
        if (declared or participant_role) == "implementer":
            return RuntimeRoleResolution(
                role="implementer",
                declared_role=declared or participant_role,
                authority_role="",
                role_source="declared_role_without_mutation_authority",
                role_scope="session",
                mutation_mode="read_only",
                granted_capabilities=capabilities,
            )

        if participant_role:
            return RuntimeRoleResolution(
                role=participant_role,
                declared_role=declared or participant_role,
                authority_role="",
                role_source="collaboration_participant",
                role_scope="session",
                mutation_mode="read_only",
                granted_capabilities=capabilities,
            )

        if fallback:
            return RuntimeRoleResolution(
                role=fallback,
                declared_role=fallback,
                authority_role="",
                role_source="legacy_provider_default",
                role_scope="provider_default",
                mutation_mode="read_only",
                granted_capabilities=capabilities,
            )

        return RuntimeRoleResolution(
            role="",
            declared_role="",
            authority_role="",
            role_source="unresolved",
            role_scope="unknown",
            mutation_mode="read_only",
            granted_capabilities=capabilities,
        )


def build_runtime_role_index(
    collaboration: Mapping[str, object] | None,
) -> RuntimeRoleIndex:
    """Build a role index for ``agent_work_board`` projection."""
    return RuntimeRoleIndex(collaboration)


def _authority_rows(
    collaboration: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = collaboration.get("actor_authorities")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _participant_rows(
    collaboration: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = collaboration.get("participants")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _participant_for_actor(
    participants: tuple[Mapping[str, object], ...],
    actor: str,
) -> Mapping[str, object]:
    for participant in participants:
        if _same_actor(participant.get("agent_id"), actor) or _same_actor(
            participant.get("provider"),
            actor,
        ):
            return participant
    return {}


def _capabilities_for_actor(
    authorities: tuple[Mapping[str, object], ...],
    actor: str,
) -> tuple[str, ...]:
    capabilities: list[str] = []
    for authority in authorities:
        if not (
            _same_actor(authority.get("actor_id"), actor)
            or _same_actor(authority.get("provider"), actor)
        ):
            continue
        grants = authority.get("grants")
        if not isinstance(grants, Sequence) or isinstance(grants, (str, bytes)):
            continue
        for grant in grants:
            if not isinstance(grant, Mapping) or not _truthy(grant.get("granted")):
                continue
            capability = _text(grant.get("capability"))
            if capability and capability not in capabilities:
                capabilities.append(capability)
    return tuple(capabilities)


def _authority_role_for_actor(
    authorities: tuple[Mapping[str, object], ...],
    *,
    actor: str,
    capabilities: tuple[str, ...],
) -> str:
    capability_set = set(capabilities)
    if capability_set & _MUTATION_CAPABILITIES:
        return "implementer"
    if capability_set & _REVIEW_CAPABILITIES:
        return "reviewer"
    if capability_set & _OBSERVE_CAPABILITIES:
        return "dashboard"
    for authority in authorities:
        if not (
            _same_actor(authority.get("actor_id"), actor)
            or _same_actor(authority.get("provider"), actor)
        ):
            continue
        role = normalize_packet_route_role(authority.get("role"))
        if role and _truthy(authority.get("live")):
            # A live implementer assignment without grants is lane authority,
            # not mutation authority. Let declared/session role handling keep
            # the lane visible while mutation stays read-only.
            if role == "implementer":
                return ""
            return role
    return ""


def _mutation_mode_for_capabilities(capabilities: tuple[str, ...]) -> str:
    return "live_tree" if set(capabilities) & _MUTATION_CAPABILITIES else "read_only"


def _same_actor(left: object, right: object) -> bool:
    return _text(left).lower() == _text(right).lower() and bool(_text(left))


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return _text(value).lower() in {"1", "true", "yes", "y", "on", "live"}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "RuntimeRoleIndex",
    "RuntimeRoleResolution",
    "build_runtime_role_index",
]
