"""Typed peer-collaboration edge resolution for agent peer awareness."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .enum_compat import StrEnum
from .review_state_collaboration_models import (
    ActorAuthorityState,
    actor_authorities_from_value,
)
from .session_route_scope import normalize_route_role
from .value_coercion import coerce_text


class DevelopRole(StrEnum):
    """Normalized collaboration roles used by peer edge resolution."""

    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"
    WATCHER = "watcher"
    OPERATOR = "operator"
    DASHBOARD = "dashboard"
    SUBAGENT = "subagent"


class PeerRelation(StrEnum):
    """Relationship from the current actor to the resolved peer."""

    REVIEWS = "reviews"
    IS_REVIEWED_BY = "is_reviewed_by"
    WATCHES = "watches"
    IS_WATCHED_BY = "is_watched_by"
    COORDINATES_WITH = "coordinates_with"


@dataclass(frozen=True, slots=True)
class ActorRef:
    """Typed actor identity resolved from collaboration authority."""

    actor_id: str
    provider: str = ""
    session_id: str = ""
    worktree_identity: str = ""
    source_contract: str = ""
    zref: str = ""

    @property
    def peer_command_id(self) -> str:
        """Return the stable provider/actor token used by command projections."""
        return self.provider or self.actor_id


@dataclass(frozen=True, slots=True)
class PeerCollaborationEdge:
    """Resolved active collaboration edge between two authority-backed actors."""

    actor: ActorRef
    peer: ActorRef
    actor_role: DevelopRole
    peer_role: DevelopRole
    relation: PeerRelation
    scope_ref: str
    source_ref: str
    evidence_refs: tuple[str, ...] = ()


_MUTATION_CAPABILITIES = frozenset({"repo.stage", "repo.commit"})
_REVIEW_CAPABILITIES = frozenset({"review.checkpoint", "review.finding"})
_WATCH_CAPABILITIES = frozenset({"runtime.observe", "approval.commit"})


def resolve_peer_collaboration_edge(
    *,
    actor: str,
    actor_role: str = "",
    session_id: str = "",
    sources: Sequence[tuple[str, Mapping[str, object]]],
) -> PeerCollaborationEdge | None:
    """Resolve the active peer edge from typed collaboration authority.

    Provider names and role aliases are projections. This resolver only returns
    an edge when a current collaboration source supplies live actor authority
    rows, optionally constrained by the owner lanes on the same source.
    """

    actor_id = coerce_text(actor)
    if not actor_id:
        return None
    declared_role = normalize_develop_role(actor_role)
    for source_ref, source in sources:
        edge = _edge_from_source(
            actor=actor_id,
            declared_role=declared_role,
            session_id=coerce_text(session_id),
            source_ref=source_ref,
            source=source,
        )
        if edge is not None:
            return edge
    return None


def normalize_develop_role(value: object) -> DevelopRole | None:
    """Normalize route-role aliases into the collaboration role enum."""

    raw = coerce_text(value).lower().replace("-", "_").replace(" ", "_")
    if raw in {"verification", "verifier"}:
        return DevelopRole.REVIEWER
    if raw == "remote_operator":
        return DevelopRole.OPERATOR
    normalized = normalize_route_role(raw)
    if normalized == "implementer":
        return DevelopRole.IMPLEMENTER
    if normalized == "reviewer":
        return DevelopRole.REVIEWER
    if normalized == "dashboard":
        if raw == "watcher":
            return DevelopRole.WATCHER
        return DevelopRole.DASHBOARD
    if normalized == "operator":
        return DevelopRole.OPERATOR
    if normalized == "subagent":
        return DevelopRole.SUBAGENT
    return None


def _edge_from_source(
    *,
    actor: str,
    declared_role: DevelopRole | None,
    session_id: str,
    source_ref: str,
    source: Mapping[str, object],
) -> PeerCollaborationEdge | None:
    authorities = _live_authorities(source.get("actor_authorities"))
    if not authorities:
        return None
    actor_authority = _authority_for_actor(authorities, actor)
    if actor_authority is None:
        return None
    owner_lanes = _owner_lanes(source, authorities)
    if owner_lanes:
        edge = _edge_from_owner_lanes(
            actor_authority=actor_authority,
            declared_role=declared_role,
            session_id=session_id,
            authorities=authorities,
            owner_lanes=owner_lanes,
            source_ref=source_ref,
            source=source,
        )
        if edge is not None:
            return edge
    return _edge_from_authority_roles(
        actor_authority=actor_authority,
        declared_role=declared_role,
        session_id=session_id,
        authorities=authorities,
        source_ref=source_ref,
        source=source,
    )


def _edge_from_owner_lanes(
    *,
    actor_authority: ActorAuthorityState,
    declared_role: DevelopRole | None,
    session_id: str,
    authorities: tuple[ActorAuthorityState, ...],
    owner_lanes: Mapping[str, str],
    source_ref: str,
    source: Mapping[str, object],
) -> PeerCollaborationEdge | None:
    actor_lane = _lane_for_authority(actor_authority, owner_lanes)
    if not actor_lane:
        return None
    actor_role = _role_for_authority(actor_authority) or declared_role
    actor_role = actor_role or _role_for_lane(actor_lane)
    if actor_role is None:
        return None
    for lane in _candidate_lanes(actor_lane):
        peer_owner = owner_lanes.get(lane, "")
        if not peer_owner:
            continue
        peer_authority = _authority_for_actor(authorities, peer_owner)
        if peer_authority is None or _same_authority(actor_authority, peer_authority):
            continue
        peer_role = _role_for_authority(peer_authority) or _role_for_lane(lane)
        if peer_role is None:
            continue
        return _edge(
            actor_authority=actor_authority,
            peer_authority=peer_authority,
            actor_role=actor_role,
            peer_role=peer_role,
            source_ref=source_ref,
            source=source,
        )
    return None


def _edge_from_authority_roles(
    *,
    actor_authority: ActorAuthorityState,
    declared_role: DevelopRole | None,
    session_id: str,
    authorities: tuple[ActorAuthorityState, ...],
    source_ref: str,
    source: Mapping[str, object],
) -> PeerCollaborationEdge | None:
    actor_role = _role_for_authority(actor_authority) or declared_role
    if actor_role is None:
        return None
    for peer_authority in authorities:
        if _same_authority(actor_authority, peer_authority):
            continue
        peer_role = _role_for_authority(peer_authority)
        if peer_role is None:
            continue
        if not _roles_are_complementary(actor_role, peer_role):
            continue
        if session_id and actor_authority.session_id == session_id:
            return _edge(
                actor_authority=actor_authority,
                peer_authority=peer_authority,
                actor_role=actor_role,
                peer_role=peer_role,
                source_ref=source_ref,
                source=source,
            )
        return _edge(
            actor_authority=actor_authority,
            peer_authority=peer_authority,
            actor_role=actor_role,
            peer_role=peer_role,
            source_ref=source_ref,
            source=source,
        )
    return None


def _edge(
    *,
    actor_authority: ActorAuthorityState,
    peer_authority: ActorAuthorityState,
    actor_role: DevelopRole,
    peer_role: DevelopRole,
    source_ref: str,
    source: Mapping[str, object],
) -> PeerCollaborationEdge | None:
    scope_ref = _scope_ref(source, actor_authority, peer_authority)
    if not scope_ref:
        return None
    return PeerCollaborationEdge(
        actor=_actor_ref(actor_authority),
        peer=_actor_ref(peer_authority),
        actor_role=actor_role,
        peer_role=peer_role,
        relation=_relation(actor_role, peer_role),
        scope_ref=scope_ref,
        source_ref=source_ref,
        evidence_refs=_evidence_refs(
            source_ref,
            scope_ref,
            actor_authority,
            peer_authority,
        ),
    )


def _live_authorities(value: object) -> tuple[ActorAuthorityState, ...]:
    rows: list[ActorAuthorityState] = []
    for authority in actor_authorities_from_value(value):
        if not authority.actor_id:
            continue
        if not authority.live:
            continue
        if authority.status.lower() in {"dead", "inactive", "stopped"}:
            continue
        rows.append(authority)
    return tuple(rows)


def _owner_lanes(
    source: Mapping[str, object],
    authorities: tuple[ActorAuthorityState, ...],
) -> dict[str, str]:
    lanes = {
        "mutation": coerce_text(source.get("mutation_owner")),
        "verification": coerce_text(source.get("verification_owner")),
        "watcher": coerce_text(source.get("watcher_owner")),
    }
    if any(lanes.values()):
        return {key: value for key, value in lanes.items() if value}
    for authority in authorities:
        identity = authority.source_identity
        lanes = {
            "mutation": coerce_text(identity.get("mutation_owner")),
            "verification": coerce_text(identity.get("verification_owner")),
            "watcher": coerce_text(identity.get("watcher_owner")),
        }
        if any(lanes.values()):
            return {key: value for key, value in lanes.items() if value}
    return {}


def _lane_for_authority(
    authority: ActorAuthorityState,
    owner_lanes: Mapping[str, str],
) -> str:
    for lane, owner in owner_lanes.items():
        if _same_actor(authority, owner):
            return lane
    return ""


def _candidate_lanes(actor_lane: str) -> tuple[str, ...]:
    if actor_lane == "mutation":
        return ("verification", "watcher")
    if actor_lane == "verification":
        return ("mutation", "watcher")
    if actor_lane == "watcher":
        return ("mutation", "verification")
    return ()


def _role_for_lane(lane: str) -> DevelopRole | None:
    if lane == "mutation":
        return DevelopRole.IMPLEMENTER
    if lane == "verification":
        return DevelopRole.REVIEWER
    if lane == "watcher":
        return DevelopRole.WATCHER
    return None


def _role_for_authority(authority: ActorAuthorityState) -> DevelopRole | None:
    capabilities = {
        coerce_text(grant.capability)
        for grant in authority.grants
        if grant.granted and coerce_text(grant.capability)
    }
    if capabilities & _MUTATION_CAPABILITIES:
        return DevelopRole.IMPLEMENTER
    if capabilities & _REVIEW_CAPABILITIES:
        return DevelopRole.REVIEWER
    normalized = normalize_develop_role(authority.role)
    if normalized in {
        DevelopRole.WATCHER,
        DevelopRole.OPERATOR,
        DevelopRole.DASHBOARD,
    }:
        return normalized
    if capabilities & _WATCH_CAPABILITIES:
        return DevelopRole.WATCHER
    return normalized


def _roles_are_complementary(
    actor_role: DevelopRole,
    peer_role: DevelopRole,
) -> bool:
    actor_family = _role_family(actor_role)
    peer_family = _role_family(peer_role)
    if actor_family == "implementation":
        return peer_family in {"review", "watch"}
    if actor_family == "review":
        return peer_family in {"implementation", "watch"}
    if actor_family == "watch":
        return peer_family in {"implementation", "review"}
    return False


def _role_family(role: DevelopRole) -> str:
    if role == DevelopRole.IMPLEMENTER:
        return "implementation"
    if role == DevelopRole.REVIEWER:
        return "review"
    if role in {DevelopRole.WATCHER, DevelopRole.OPERATOR, DevelopRole.DASHBOARD}:
        return "watch"
    return ""


def _relation(actor_role: DevelopRole, peer_role: DevelopRole) -> PeerRelation:
    actor_family = _role_family(actor_role)
    peer_family = _role_family(peer_role)
    if actor_family == "review" and peer_family == "implementation":
        return PeerRelation.REVIEWS
    if actor_family == "implementation" and peer_family == "review":
        return PeerRelation.IS_REVIEWED_BY
    if actor_family == "watch":
        return PeerRelation.WATCHES
    if peer_family == "watch":
        return PeerRelation.IS_WATCHED_BY
    return PeerRelation.COORDINATES_WITH


def _authority_for_actor(
    authorities: tuple[ActorAuthorityState, ...],
    actor: str,
) -> ActorAuthorityState | None:
    for authority in authorities:
        if _same_actor(authority, actor):
            return authority
    return None


def _same_actor(authority: ActorAuthorityState, actor: str) -> bool:
    actor_key = coerce_text(actor).lower()
    return bool(actor_key) and actor_key in {
        authority.actor_id.lower(),
        authority.provider.lower(),
    }


def _same_authority(
    left: ActorAuthorityState,
    right: ActorAuthorityState,
) -> bool:
    return bool(
        {
            left.actor_id.lower(),
            left.provider.lower(),
        }
        & {
            right.actor_id.lower(),
            right.provider.lower(),
        }
    )


def _actor_ref(authority: ActorAuthorityState) -> ActorRef:
    return ActorRef(
        actor_id=authority.actor_id,
        provider=authority.provider,
        session_id=authority.session_id,
        worktree_identity=authority.worktree_identity,
        source_contract=authority.source_contract,
        zref=authority.zref,
    )


def _scope_ref(
    source: Mapping[str, object],
    actor_authority: ActorAuthorityState,
    peer_authority: ActorAuthorityState,
) -> str:
    source_scope = _source_scope_ref(source)
    if source_scope:
        return source_scope
    actor_scopes = _authority_scope_refs(actor_authority)
    peer_scopes = _authority_scope_refs(peer_authority)
    for scope in actor_scopes:
        if scope in peer_scopes:
            return scope
    return ""


def _source_scope_ref(source: Mapping[str, object]) -> str:
    for key in (
        "current_slice",
        "slice_id",
        "target_ref",
        "plan_id",
        "reviewer_mode",
    ):
        value = coerce_text(source.get(key))
        if value:
            return _typed_scope_ref(key, value)
    return ""


def _authority_scope_refs(authority: ActorAuthorityState) -> tuple[str, ...]:
    refs: list[str] = []
    for grant in authority.grants:
        if not grant.granted:
            continue
        ref = _typed_scope_ref(grant.target_kind, grant.target_ref)
        if ref:
            refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _typed_scope_ref(kind: object, value: object) -> str:
    ref = coerce_text(value)
    if not ref:
        return ""
    scope_kind = coerce_text(kind)
    if scope_kind and ":" not in ref:
        return f"{scope_kind}:{ref}"
    return ref


def _evidence_refs(
    source_ref: str,
    scope_ref: str,
    actor_authority: ActorAuthorityState,
    peer_authority: ActorAuthorityState,
) -> tuple[str, ...]:
    refs = [
        source_ref,
        scope_ref,
        f"{actor_authority.source_contract or 'CollaborationSession'}:actor_authorities",
        actor_authority.zref,
        peer_authority.zref,
        _prefixed("packet", actor_authority.packet_id),
        _prefixed("packet", peer_authority.packet_id),
        _prefixed("approval", actor_authority.approval_ref),
        _prefixed("approval", peer_authority.approval_ref),
    ]
    return tuple(dict.fromkeys(ref for ref in refs if ref))


def _prefixed(prefix: str, value: object) -> str:
    text = coerce_text(value)
    return f"{prefix}:{text}" if text else ""


__all__ = [
    "ActorRef",
    "DevelopRole",
    "PeerCollaborationEdge",
    "PeerRelation",
    "normalize_develop_role",
    "resolve_peer_collaboration_edge",
]
