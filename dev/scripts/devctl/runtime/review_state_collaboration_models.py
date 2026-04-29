"""Typed collaboration-session dataclasses for the review-state contract."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .agent_session_outcome import AgentSessionOutcomeState
from .session_posture import SessionPosture, session_posture_from_mapping
from .work_intake_models import WorkIntakeOwnershipState


@dataclass(frozen=True, slots=True)
class CapabilityGrantState:
    capability: str
    granted: bool
    source: str
    reason: str = ""
    target_kind: str = ""
    target_ref: str = ""
    target_revision: str = ""
    worktree_identity: str = ""
    packet_id: str = ""
    approval_ref: str = ""
    issued_at_utc: str = ""
    expires_at_utc: str = ""


@dataclass(frozen=True, slots=True)
class ActorAuthorityState:
    actor_id: str
    provider: str
    role: str
    live: bool
    status: str
    source: str
    grants: tuple[CapabilityGrantState, ...] = ()
    source_contract: str = "CollaborationSession"
    source_identity: dict[str, str] = field(default_factory=dict)
    snapshot_id: str = ""
    zref: str = ""
    generation_id: str = ""
    worktree_identity: str = ""
    packet_id: str = ""
    approval_ref: str = ""
    issued_at_utc: str = ""
    expires_at_utc: str = ""


@dataclass(frozen=True, slots=True)
class CollaborationRoleAssignmentState:
    role_id: str
    agent_id: str
    provider: str
    display_name: str
    status: str
    source: str
    session_name: str = ""
    live: bool = False


@dataclass(frozen=True, slots=True)
class CollaborationParticipantState:
    agent_id: str
    provider: str
    display_name: str
    role: str
    session_name: str
    live: bool
    status: str
    capture_mode: str = ""
    approval_mode: str = ""
    supervision_mode: str = ""
    host_wake_mode: str = ""
    wake_interval_seconds: int = 0
    host_wake_summary: str = ""
    prepared_at: str = ""
    metadata_path: str = ""
    log_path: str = ""
    launch_command: str = ""
    requested_worker_budget: int | None = None
    planned_lane_count: int = 0
    lane: str = ""
    mp_scope: str = ""
    worktree: str = ""
    branch: str = ""
    workspace_root: str = ""


@dataclass(frozen=True, slots=True)
class DelegatedWorkReceiptState:
    receipt_id: str
    agent_id: str
    provider: str
    role: str
    owner_session: str
    source: str
    status: str
    lane: str = ""
    mp_scope: str = ""
    worktree: str = ""
    branch: str = ""
    live: bool = False


@dataclass(frozen=True, slots=True)
class CollaborationPeerReviewState:
    current_instruction: str
    current_instruction_revision: str
    open_findings: str
    implementer_status: str
    implementer_ack: str
    implementer_ack_state: str
    implementer_state_hash: str = ""
    last_reviewed_scope: str = ""


@dataclass(frozen=True, slots=True)
class CollaborationArbitrationState:
    status: str
    summary: str
    owner: str = ""


@dataclass(frozen=True, slots=True)
class CollaborationRestartState:
    status: str
    resumable: bool
    source: str
    launch_truth: str = ""
    reviewer_mode: str = ""
    effective_reviewer_mode: str = ""
    last_codex_poll_utc: str = ""
    last_reviewer_poll_utc: str = ""
    last_worktree_hash: str = ""


@dataclass(frozen=True, slots=True)
class CollaborationReadyGateState:
    gate_id: str
    status: str
    summary: str


@dataclass(frozen=True, slots=True)
class CollaborationSessionState:
    schema_version: int
    contract_id: str
    session_id: str
    plan_id: str
    status: str
    reviewer_mode: str
    operator_mode: str
    lead_agent: str
    review_agent: str
    coding_agent: str
    current_slice: str
    peer_review: CollaborationPeerReviewState
    arbitration: CollaborationArbitrationState
    restart: CollaborationRestartState
    ready_gates: tuple[CollaborationReadyGateState, ...]
    role_assignments: tuple[CollaborationRoleAssignmentState, ...]
    participants: tuple[CollaborationParticipantState, ...]
    delegated_work: tuple[DelegatedWorkReceiptState, ...]
    topology_mode: str = "single_agent"
    work_ownership_mode: str = "exclusive_slice"
    ownership: WorkIntakeOwnershipState = field(
        default_factory=WorkIntakeOwnershipState
    )
    mutation_owner: str = ""
    verification_owner: str = ""
    verification_status: str = "inactive"
    watcher_owner: str = ""
    watcher_status: str = "inactive"
    mutation_wake_mode: str = "unknown"
    verification_wake_mode: str = "unknown"
    watcher_wake_mode: str = "unknown"
    wake_continuity_ok: bool = True
    wake_gap_summary: str = ""
    loop_wake_mode: str = "unknown"
    loop_wake_interval_seconds: int = 0
    loop_driver_agent: str = ""
    loop_autonomy_ok: bool = False
    loop_gap_summary: str = ""
    actor_authorities: tuple[ActorAuthorityState, ...] = ()
    session_outcomes: tuple[AgentSessionOutcomeState, ...] = ()
    session_posture: SessionPosture = field(default_factory=SessionPosture)


def actor_authorities_from_value(value: object) -> tuple[ActorAuthorityState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    rows: list[ActorAuthorityState] = []
    for row in value:
        mapping = _mapping(row)
        actor_id = _text(mapping.get("actor_id"))
        if not actor_id:
            continue
        rows.append(
            ActorAuthorityState(
                actor_id=actor_id,
                provider=_text(mapping.get("provider")) or actor_id,
                role=_text(mapping.get("role")),
                live=_bool(mapping.get("live")),
                status=_text(mapping.get("status")) or "unknown",
                source=_text(mapping.get("source")),
                grants=capability_grants_from_value(mapping.get("grants")),
                source_contract=(
                    _text(mapping.get("source_contract")) or "CollaborationSession"
                ),
                source_identity=_dict_of_str(mapping.get("source_identity")),
                snapshot_id=_text(mapping.get("snapshot_id")),
                zref=_text(mapping.get("zref")),
                generation_id=_text(mapping.get("generation_id")),
                worktree_identity=_text(mapping.get("worktree_identity")),
                packet_id=_text(mapping.get("packet_id")),
                approval_ref=_text(mapping.get("approval_ref")),
                issued_at_utc=_text(mapping.get("issued_at_utc")),
                expires_at_utc=_text(mapping.get("expires_at_utc")),
            )
        )
    return tuple(rows)


def session_posture_from_value(value: object) -> SessionPosture:
    return session_posture_from_mapping(value) or SessionPosture()


def capability_grants_from_value(value: object) -> tuple[CapabilityGrantState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    grants: list[CapabilityGrantState] = []
    for row in value:
        mapping = _mapping(row)
        capability = _text(mapping.get("capability"))
        if not capability:
            continue
        grants.append(
            CapabilityGrantState(
                capability=capability,
                granted=_bool(mapping.get("granted")),
                source=_text(mapping.get("source")),
                reason=_text(mapping.get("reason")),
                target_kind=_text(mapping.get("target_kind")),
                target_ref=_text(mapping.get("target_ref")),
                target_revision=_text(mapping.get("target_revision")),
                worktree_identity=_text(mapping.get("worktree_identity")),
                packet_id=_text(mapping.get("packet_id")),
                approval_ref=_text(mapping.get("approval_ref")),
                issued_at_utc=_text(mapping.get("issued_at_utc")),
                expires_at_utc=_text(mapping.get("expires_at_utc")),
            )
        )
    return tuple(grants)


def actor_authority_for_capability(
    authorities: tuple[ActorAuthorityState, ...],
    capability: str,
    *,
    preferred_actor: str = "",
    alternate_capabilities: tuple[str, ...] = (),
) -> ActorAuthorityState | None:
    requested = (
        _normalized(capability),
        *(_normalized(item) for item in alternate_capabilities),
    )
    requested_set = {item for item in requested if item}
    if not requested_set:
        return None
    preferred = _text(preferred_actor)
    if preferred:
        for authority in authorities:
            if not _same_actor(authority, preferred):
                continue
            if actor_authority_grants(authority, requested_set):
                return authority
        return None
    for authority in authorities:
        if actor_authority_grants(authority, requested_set):
            return authority
    return None


def actor_authority_grants(
    authority: ActorAuthorityState,
    capabilities: set[str],
) -> bool:
    if not authority.live:
        return False
    for grant in authority.grants:
        if grant.granted and _normalized(grant.capability) in capabilities:
            return True
    return False


def granted_capabilities_for_actor(
    authorities: tuple[ActorAuthorityState, ...],
    actor_id: str,
) -> tuple[str, ...]:
    actor = _text(actor_id)
    if not actor:
        return ()
    capabilities: list[str] = []
    for authority in authorities:
        if not _same_actor(authority, actor):
            continue
        for grant in authority.grants:
            if grant.granted and grant.capability not in capabilities:
                capabilities.append(grant.capability)
    return tuple(capabilities)


def _same_actor(authority: ActorAuthorityState, actor_id: str) -> bool:
    normalized = _normalized(actor_id)
    return normalized in {
        _normalized(authority.actor_id),
        _normalized(authority.provider),
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _dict_of_str(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {
        _text(key): _text(item)
        for key, item in value.items()
        if _text(key) and _text(item)
    }


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalized(value: object) -> str:
    return _text(value).lower()


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}
