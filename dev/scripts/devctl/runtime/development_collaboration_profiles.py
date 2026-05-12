"""Provider-neutral collaboration profile contracts for ``/develop``."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from .development_collaboration_modes import (
    DevelopCollaborationModeSpec,
    RoleCountBudget,
    build_default_collaboration_mode_topology,
)
from .provider_registry import is_valid_provider_id, normalize_provider_id
from .review_packet_inbox import packet_inbox_from_review_state
from .review_state_collaboration_models import CollaborationSessionState
from .review_state_parser import review_state_from_payload
from .reviewer_runtime_models import WakeEvidence, derive_wake_evidence_for_actor
from .role_topology import resolve_role_topology
from .session_termination_policy import (
    CONTINUATION_ANCHOR_PACKET_KIND,
    STOP_ANCHOR_PACKET_KIND,
)
from .session_posture import SessionPosture, session_posture_from_mapping

PROFILE_CONTRACT_ID = "AgentCollaborationProfile"
PROFILE_SCHEMA_VERSION = 1
DEFAULT_PROFILE_ID = "default"
DEFAULT_PROFILE_PROVIDERS = ("codex", "claude")
COORDINATION_SURFACES = (
    "AgentMindSlice",
    "PacketInboxState",
    "ReviewPacketState",
    "AgentWorkBoardProjection",
    "AgentLoopDecision",
    "CollaborationSessionState",
)
PEER_POLLING_POLICY = (
    "agent-mind polling is advisory attention context only; packets, session "
    "posture, authority snapshots, and leases remain the authority path"
)
AUTHORITY_POLICY = (
    "role bindings and provider ids request a lane; they never grant mutation, "
    "review acceptance, staging, commit, push, or operator approval"
)
STOP_ANCHOR_POLICY = (
    "stop_at flags only describe the stop condition; an actual session stop is "
    "authorized by SessionTerminationPolicy plus scoped stop_anchor packets"
)


@dataclass(frozen=True, slots=True)
class CollaborationRoleBinding:
    """One requested role-to-provider binding for a collaboration profile."""

    role: str
    provider: str
    session_id: str = ""
    source: str = "request"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CollaborationRoleCountRequest:
    """One requested role fanout count from CLI, repo-pack, or shortcuts."""

    role: str
    requested_count: int
    source: str = "request"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CollaborationResolvedRoleBudget:
    """Resolved role budget after applying the selected mode policy."""

    role: str
    requested_count: int
    resolved_count: int
    max_count: int
    mutable_lane_limit: int
    budget_kind: str
    status: str
    live_capacity: int = -1
    capacity_source: str = ""
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        return payload


@dataclass(frozen=True, slots=True)
class CollaborationStopAnchorRequest:
    """Operator-requested stop condition for an ``agent_sync`` profile."""

    stop_at_packet_id: str = ""
    stop_at_mp_row_id: str = ""
    status: str = "not_configured"
    reasons: tuple[str, ...] = ()
    validation_errors: tuple[str, ...] = ()
    continuation_packet_kind: str = CONTINUATION_ANCHOR_PACKET_KIND
    stop_packet_kind: str = STOP_ANCHOR_PACKET_KIND
    authority_policy: str = STOP_ANCHOR_POLICY

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["reasons"] = list(self.reasons)
        payload["validation_errors"] = list(self.validation_errors)
        return payload


@dataclass(frozen=True, slots=True)
class CollaborationProfileActorAuthority:
    """Compact authority evidence surfaced by a collaboration profile."""

    actor_id: str
    provider: str
    role: str
    live: bool
    status: str
    source: str
    session_id: str = ""
    capabilities: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["capabilities"] = list(self.capabilities)
        return payload


@dataclass(frozen=True, slots=True)
class CollaborationProfilePeerReview:
    """Small peer-review receipt without full instruction bodies."""

    current_instruction_revision: str = ""
    open_findings: str = ""
    implementer_status: str = ""
    implementer_ack: str = ""
    implementer_ack_state: str = ""
    last_reviewed_scope: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CollaborationProfileArbitration:
    """Compact arbitration state for profile consumers."""

    status: str = ""
    owner: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CollaborationProfileReadyGate:
    """One compact ready-gate row for profile consumers."""

    gate_id: str
    status: str
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CollaborationProfileWakeEvidence:
    """Advisory wake evidence for one requested profile binding."""

    role: str
    provider: str
    actor_id: str
    session_id: str = ""
    arrival_kind: str = "none"
    latest_relevant_event_id: str = ""
    latest_relevant_event_at_utc: str = ""
    latest_relevant_packet_id: str = ""
    attention_status: str = "none"
    wake_reason: str = ""
    required_command: str = ""
    pending_packet_ids: tuple[str, ...] = ()
    source: str = "WakeEvidence+PacketInboxState"
    authority_policy: str = PEER_POLLING_POLICY

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["pending_packet_ids"] = list(self.pending_packet_ids)
        return payload


@dataclass(frozen=True, slots=True)
class CollaborationProfileSession:
    """Compact ``CollaborationSessionState`` evidence for the profile."""

    contract_id: str
    session_id: str
    status: str
    plan_id: str = ""
    reviewer_mode: str = ""
    operator_mode: str = ""
    topology_mode: str = ""
    work_ownership_mode: str = ""
    lead_agent: str = ""
    review_agent: str = ""
    coding_agent: str = ""
    current_slice: str = ""
    owners: Mapping[str, str] | None = None
    actor_authorities: tuple[CollaborationProfileActorAuthority, ...] = ()
    peer_review: CollaborationProfilePeerReview | None = None
    arbitration: CollaborationProfileArbitration | None = None
    ready_gates: tuple[CollaborationProfileReadyGate, ...] = ()
    session_posture_actor_count: int = 0

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["owners"] = dict(self.owners or {})
        payload["actor_authorities"] = [
            item.to_dict() for item in self.actor_authorities
        ]
        payload["peer_review"] = (
            self.peer_review.to_dict() if self.peer_review is not None else {}
        )
        payload["arbitration"] = (
            self.arbitration.to_dict() if self.arbitration is not None else {}
        )
        payload["ready_gates"] = [item.to_dict() for item in self.ready_gates]
        return payload


@dataclass(frozen=True, slots=True)
class AgentCollaborationProfile:
    """Portable request profile consumed by the existing ``/develop`` runtime."""

    profile_id: str
    selected_mode_id: str
    selected_role_preset_id: str
    providers: tuple[str, ...]
    role_bindings: tuple[CollaborationRoleBinding, ...]
    role_count_requests: tuple[CollaborationRoleCountRequest, ...]
    resolved_role_budgets: tuple[CollaborationResolvedRoleBudget, ...]
    agent_mind_providers: tuple[str, ...]
    remote_provider: str = ""
    architecture_agent_count: int = 0
    review_agent_count: int = 0
    max_architecture_agent_count: int = 0
    source_packet_id: str = ""
    target_packet_id: str = ""
    stop_at_packet_id: str = ""
    stop_at_mp_row_id: str = ""
    stop_anchor_request: CollaborationStopAnchorRequest | None = None
    collaboration_session: CollaborationProfileSession | None = None
    advisory_wake_evidence: tuple[CollaborationProfileWakeEvidence, ...] = ()
    source_ref: str = ""
    target_ref: str = ""
    coordination_surfaces: tuple[str, ...] = COORDINATION_SURFACES
    peer_polling_policy: str = PEER_POLLING_POLICY
    authority_policy: str = AUTHORITY_POLICY
    command_plan: tuple[str, ...] = ()
    validation_errors: tuple[str, ...] = ()
    validation_warnings: tuple[str, ...] = ()
    ok: bool = True
    template: Mapping[str, object] | None = None
    schema_version: int = PROFILE_SCHEMA_VERSION
    contract_id: str = PROFILE_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["role_bindings"] = [item.to_dict() for item in self.role_bindings]
        payload["role_count_requests"] = [
            item.to_dict() for item in self.role_count_requests
        ]
        payload["resolved_role_budgets"] = [
            item.to_dict() for item in self.resolved_role_budgets
        ]
        payload["providers"] = list(self.providers)
        payload["agent_mind_providers"] = list(self.agent_mind_providers)
        payload["coordination_surfaces"] = list(self.coordination_surfaces)
        payload["stop_anchor_request"] = (
            self.stop_anchor_request.to_dict()
            if self.stop_anchor_request is not None
            else None
        )
        payload["collaboration_session"] = (
            self.collaboration_session.to_dict()
            if self.collaboration_session is not None
            else None
        )
        payload["advisory_wake_evidence"] = [
            item.to_dict() for item in self.advisory_wake_evidence
        ]
        payload["command_plan"] = list(self.command_plan)
        payload["validation_errors"] = list(self.validation_errors)
        payload["validation_warnings"] = list(self.validation_warnings)
        return payload


def build_agent_collaboration_profile(
    *,
    profile_id: object = "",
    selected_mode_id: str,
    selected_role_preset_id: str,
    providers: Sequence[object] = (),
    role_bindings: Sequence[object] = (),
    role_counts: Sequence[object] = (),
    agent_mind_providers: Sequence[object] = (),
    remote_provider: object = "",
    architecture_agent_count: int = 0,
    review_agent_count: int = 0,
    source_packet_id: object = "",
    target_packet_id: object = "",
    stop_at_packet_id: object = "",
    stop_at_mp_row_id: object = "",
    source_ref: object = "",
    target_ref: object = "",
    max_workers: int = 0,
    emit_template: bool = False,
    review_state: Mapping[str, object] | None = None,
    events: Sequence[Mapping[str, object]] = (),
    plan_rows: Sequence[object] = (),
    session_posture: SessionPosture | None = None,
) -> AgentCollaborationProfile:
    """Build a portable profile over existing typed collaboration surfaces."""
    state, collaboration_state = _profile_review_state(review_state)
    collaboration_session = _collaboration_profile_session(collaboration_state)
    topology = build_default_collaboration_mode_topology()
    modes = {item.mode_id: item for item in topology.modes}
    posture = (
        session_posture
        or _session_posture_from_review_state(state)
        or _session_posture_from_collaboration(collaboration_state)
    )
    roles = _known_roles(topology, state, posture)
    selected_mode = modes.get(selected_mode_id)
    role_count_requests, role_count_errors = _role_count_requests(
        role_counts,
        architecture_agent_count=architecture_agent_count,
        review_agent_count=review_agent_count,
        max_workers=max_workers,
        selected_mode=selected_mode,
        selected_mode_id=selected_mode_id,
        known_roles=roles,
    )
    resolved_budgets = _resolved_role_budgets(
        requests=role_count_requests,
        selected_mode=selected_mode,
        live_capacity_by_role=_live_capacity_by_role(state),
    )
    architecture_count = _resolved_count_for(resolved_budgets, "architect")
    review_count = _resolved_count_for(resolved_budgets, "reviewer")
    bindings, binding_errors = _role_bindings(
        role_bindings,
        known_roles=roles,
        review_state=state,
        session_posture=posture,
    )
    advisory_wake_evidence = _advisory_wake_evidence(
        role_bindings=bindings,
        review_state=state,
        events=events,
    )
    provider_ids = _providers(
        requested=providers,
        role_bindings=bindings,
        agent_mind_providers=agent_mind_providers,
        remote_provider=remote_provider,
    )
    mind_providers = _agent_mind_providers(
        requested=agent_mind_providers,
        providers=provider_ids,
    )
    errors = [
        *binding_errors,
        *role_count_errors,
        *_provider_errors(provider_ids),
        *_provider_errors(mind_providers, label="agent-mind provider"),
    ]
    remote = normalize_provider_id(remote_provider)
    if remote and not is_valid_provider_id(remote):
        errors.append(f"remote provider `{remote}` is not a valid provider id")
    max_architects = _max_architecture_agents(selected_mode)
    invalid_roles = tuple(
        row
        for row in resolved_budgets
        if row.status in {"capped", "capacity_limited", "invalid"}
    )
    for row in invalid_roles:
        if row.status == "capacity_limited":
            errors.append(
                f"role count `{row.role}` exceeds live topology capacity "
                f"({row.requested_count}>{row.live_capacity})"
            )
            continue
        errors.append(
            f"role count `{row.role}` exceeds selected mode max "
            f"({row.requested_count}>{row.max_count})"
        )
    warnings = _validation_warnings(
        selected_mode_id=selected_mode_id,
        selected_role_preset_id=selected_role_preset_id,
        role_bindings=bindings,
        agent_mind_providers=mind_providers,
    )
    stop_anchor = _stop_anchor_request(
        stop_at_packet_id=stop_at_packet_id,
        stop_at_mp_row_id=stop_at_mp_row_id,
        selected_mode=selected_mode,
        review_state=state,
        plan_rows=plan_rows,
    )
    if stop_anchor is not None and stop_anchor.validation_errors:
        errors.extend(stop_anchor.validation_errors)
    if stop_anchor is not None and stop_anchor.status in {
        "waiting_packet_not_found",
        "waiting_plan_row_not_found",
        "waiting_stop_target_not_found",
    }:
        warnings = (*warnings, *stop_anchor.reasons)
    profile = AgentCollaborationProfile(
        profile_id=str(profile_id or DEFAULT_PROFILE_ID).strip() or DEFAULT_PROFILE_ID,
        selected_mode_id=selected_mode_id,
        selected_role_preset_id=selected_role_preset_id,
        providers=provider_ids,
        role_bindings=bindings,
        role_count_requests=role_count_requests,
        resolved_role_budgets=resolved_budgets,
        agent_mind_providers=mind_providers,
        remote_provider=remote,
        architecture_agent_count=architecture_count,
        review_agent_count=review_count,
        max_architecture_agent_count=max_architects,
        source_packet_id=str(source_packet_id or "").strip(),
        target_packet_id=str(target_packet_id or "").strip(),
        stop_at_packet_id=str(stop_at_packet_id or "").strip(),
        stop_at_mp_row_id=str(stop_at_mp_row_id or "").strip(),
        stop_anchor_request=stop_anchor,
        collaboration_session=collaboration_session,
        advisory_wake_evidence=advisory_wake_evidence,
        source_ref=str(source_ref or "").strip(),
        target_ref=str(target_ref or "").strip(),
        command_plan=_command_plan(
            role_bindings=bindings,
            agent_mind_providers=mind_providers,
            source_packet_id=str(source_packet_id or "").strip(),
            target_packet_id=str(target_packet_id or "").strip(),
            stop_anchor_request=stop_anchor,
            source_ref=str(source_ref or "").strip(),
            target_ref=str(target_ref or "").strip(),
            advisory_wake_evidence=advisory_wake_evidence,
        ),
        validation_errors=tuple(errors),
        validation_warnings=warnings,
        ok=not errors,
        template=profile_template() if emit_template else None,
    )
    return profile


def profile_template() -> dict[str, object]:
    """Return a starter profile shape for repo-pack or command-line adapters."""
    return {
        "profile_id": "agent-sync",
        "collaboration_mode": "agent_sync",
        "role_preset": "architect",
        "providers": ["codex", "claude"],
        "role_bindings": [
            "implementer=claude",
            "reviewer=codex",
            "architect=codex",
            "researcher=codex",
            "tester=codex",
            "watcher=claude",
            "intake=claude",
        ],
        "role_counts": ["architect=3", "researcher=2", "watcher=1", "tester=2"],
        "agent_mind_providers": ["codex", "claude"],
        "remote_provider": "claude",
        "architecture_agents": 3,
        "review_agents": 1,
        "stop_at_packet": "rev_pkt_done",
        "stop_at_mp_row": "MP377-P0-DONE",
    }


def _profile_review_state(
    review_state: Mapping[str, object] | None,
) -> tuple[Mapping[str, object], CollaborationSessionState | None]:
    raw = review_state if isinstance(review_state, Mapping) else {}
    if not raw:
        return {}, None
    try:
        parsed = review_state_from_payload(raw)
    except (AttributeError, TypeError, ValueError):
        return raw, None
    if parsed is None:
        return raw, None
    normalized = parsed.to_dict()
    for key in ("bridge_liveness",):
        value = raw.get(key)
        nested = raw.get("review_state")
        if value is None and isinstance(nested, Mapping):
            value = nested.get(key)
        if value is not None and key not in normalized:
            normalized[key] = value
    return normalized, parsed.collaboration


def _collaboration_profile_session(
    state: CollaborationSessionState | None,
) -> CollaborationProfileSession | None:
    if state is None:
        return None
    return CollaborationProfileSession(
        contract_id=state.contract_id,
        session_id=state.session_id,
        status=state.status,
        plan_id=state.plan_id,
        reviewer_mode=state.reviewer_mode,
        operator_mode=state.operator_mode,
        topology_mode=state.topology_mode,
        work_ownership_mode=state.work_ownership_mode,
        lead_agent=state.lead_agent,
        review_agent=state.review_agent,
        coding_agent=state.coding_agent,
        current_slice=state.current_slice,
        owners={
            "mutation_owner": state.mutation_owner,
            "verification_owner": state.verification_owner,
            "watcher_owner": state.watcher_owner,
        },
        actor_authorities=_profile_actor_authorities(state),
        peer_review=CollaborationProfilePeerReview(
            current_instruction_revision=(
                state.peer_review.current_instruction_revision
            ),
            open_findings=state.peer_review.open_findings,
            implementer_status=state.peer_review.implementer_status,
            implementer_ack=state.peer_review.implementer_ack,
            implementer_ack_state=state.peer_review.implementer_ack_state,
            last_reviewed_scope=state.peer_review.last_reviewed_scope,
        ),
        arbitration=CollaborationProfileArbitration(
            status=state.arbitration.status,
            owner=state.arbitration.owner,
            summary=state.arbitration.summary,
        ),
        ready_gates=tuple(
            CollaborationProfileReadyGate(
                gate_id=gate.gate_id,
                status=gate.status,
                summary=gate.summary,
            )
            for gate in state.ready_gates
        ),
        session_posture_actor_count=len(state.session_posture.actors),
    )


def _profile_actor_authorities(
    state: CollaborationSessionState,
) -> tuple[CollaborationProfileActorAuthority, ...]:
    rows: list[CollaborationProfileActorAuthority] = []
    for authority in state.actor_authorities:
        rows.append(
            CollaborationProfileActorAuthority(
                actor_id=authority.actor_id,
                provider=authority.provider,
                role=authority.role,
                live=authority.live,
                status=authority.status,
                source=authority.source,
                session_id=authority.session_id,
                capabilities=tuple(
                    grant.capability
                    for grant in authority.grants
                    if grant.granted and grant.capability
                ),
            )
        )
    return tuple(rows)


def _advisory_wake_evidence(
    *,
    role_bindings: tuple[CollaborationRoleBinding, ...],
    review_state: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
) -> tuple[CollaborationProfileWakeEvidence, ...]:
    if not role_bindings:
        return ()
    packet_inbox = packet_inbox_from_review_state(review_state)
    rows: list[CollaborationProfileWakeEvidence] = []
    event_rows = [dict(event) for event in events if isinstance(event, Mapping)]
    for binding in role_bindings:
        actor_id = f"{binding.role}-{binding.provider}" if binding.role else binding.provider
        evidence = derive_wake_evidence_for_actor(
            events=event_rows,
            actor_id=actor_id,
            session_id=binding.session_id,
        )
        record = packet_inbox.for_agent(binding.provider) if packet_inbox else None
        pending_packet_ids = _wake_pending_packet_ids(evidence, record)
        attention_status = getattr(record, "attention_status", "none") if record else "none"
        wake_reason = getattr(record, "wake_reason", "") if record else ""
        required_command = getattr(record, "required_command", "") if record else ""
        if (
            evidence.arrival_kind == "none"
            and attention_status == "none"
            and not wake_reason
            and not required_command
            and not pending_packet_ids
        ):
            continue
        rows.append(
            CollaborationProfileWakeEvidence(
                role=binding.role,
                provider=binding.provider,
                actor_id=actor_id,
                session_id=binding.session_id,
                arrival_kind=evidence.arrival_kind,
                latest_relevant_event_id=evidence.latest_relevant_event_id,
                latest_relevant_event_at_utc=evidence.latest_relevant_event_at_utc,
                latest_relevant_packet_id=evidence.latest_relevant_packet_id,
                attention_status=attention_status,
                wake_reason=wake_reason,
                required_command=required_command,
                pending_packet_ids=pending_packet_ids,
            )
        )
    return tuple(rows)


def _wake_pending_packet_ids(
    evidence: WakeEvidence,
    record: object,
) -> tuple[str, ...]:
    packet_ids: list[str] = []
    _append_packet_id(packet_ids, evidence.latest_relevant_packet_id)
    if record is not None:
        _append_packet_id(packet_ids, getattr(record, "current_instruction_packet_id", ""))
        _append_packet_id(packet_ids, getattr(record, "latest_finding_packet_id", ""))
        for packet_id in getattr(record, "pending_actionable_packet_ids", ()):
            _append_packet_id(packet_ids, packet_id)
        for packet_id in getattr(record, "expired_unresolved_packet_ids", ()):
            _append_packet_id(packet_ids, packet_id)
    return tuple(packet_ids)


def _role_bindings(
    values: Sequence[object],
    *,
    known_roles: set[str],
    review_state: Mapping[str, object],
    session_posture: SessionPosture | None,
) -> tuple[tuple[CollaborationRoleBinding, ...], tuple[str, ...]]:
    bindings: list[CollaborationRoleBinding] = []
    errors: list[str] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        if "=" not in raw:
            errors.append(f"role binding `{raw}` must use role=provider")
            continue
        role, target = raw.split("=", 1)
        role = role.strip()
        provider, session_id = _split_provider_session(target)
        if role not in known_roles:
            errors.append(f"role binding `{raw}` uses unknown role `{role}`")
            continue
        provider = normalize_provider_id(provider)
        if not is_valid_provider_id(provider):
            errors.append(f"role binding `{raw}` uses invalid provider `{provider}`")
            continue
        bindings.append(
            CollaborationRoleBinding(
                role=role,
                provider=provider,
                session_id=session_id
                or _session_for_role(
                    review_state,
                    provider=provider,
                    role=role,
                    session_posture=session_posture,
                ),
            )
        )
    return tuple(bindings), tuple(errors)


def _providers(
    *,
    requested: Sequence[object],
    role_bindings: tuple[CollaborationRoleBinding, ...],
    agent_mind_providers: Sequence[object],
    remote_provider: object,
) -> tuple[str, ...]:
    providers: list[str] = []
    for value in requested:
        _append_provider(providers, value)
    for binding in role_bindings:
        _append_provider(providers, binding.provider)
    for value in agent_mind_providers:
        _append_provider(providers, value)
    _append_provider(providers, remote_provider)
    if not providers:
        providers.extend(DEFAULT_PROFILE_PROVIDERS)
    return tuple(providers)


def _agent_mind_providers(
    *,
    requested: Sequence[object],
    providers: tuple[str, ...],
) -> tuple[str, ...]:
    values: list[str] = []
    for value in requested:
        _append_provider(values, value)
    if not values:
        values.extend(provider for provider in providers if provider in DEFAULT_PROFILE_PROVIDERS)
    return tuple(values)


def _provider_errors(
    providers: tuple[str, ...],
    *,
    label: str = "provider",
) -> tuple[str, ...]:
    return tuple(
        f"{label} `{provider}` is not a valid provider id"
        for provider in providers
        if not is_valid_provider_id(provider)
    )


def _validation_warnings(
    *,
    selected_mode_id: str,
    selected_role_preset_id: str,
    role_bindings: tuple[CollaborationRoleBinding, ...],
    agent_mind_providers: tuple[str, ...],
) -> tuple[str, ...]:
    warnings: list[str] = []
    if not role_bindings and selected_mode_id != "solo":
        warnings.append("multi-actor mode requested without explicit role bindings")
    if "implementer" in {item.role for item in role_bindings} and "reviewer" in {
        item.role for item in role_bindings
    }:
        implementers = {item.provider for item in role_bindings if item.role == "implementer"}
        reviewers = {item.provider for item in role_bindings if item.role == "reviewer"}
        if implementers & reviewers:
            warnings.append("implementer and reviewer share a provider; self-review is still blocked by authority gates")
    if selected_role_preset_id not in {item.role for item in role_bindings} and role_bindings:
        warnings.append("selected role preset is not explicitly bound in the profile")
    if not agent_mind_providers:
        warnings.append("no agent-mind providers selected; peer polling commands will be omitted")
    return tuple(warnings)


def _role_count_requests(
    values: Sequence[object],
    *,
    architecture_agent_count: int,
    review_agent_count: int,
    max_workers: int,
    selected_mode: DevelopCollaborationModeSpec | None,
    selected_mode_id: str,
    known_roles: set[str],
) -> tuple[tuple[CollaborationRoleCountRequest, ...], tuple[str, ...]]:
    requests: list[CollaborationRoleCountRequest] = []
    errors: list[str] = []
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        if "=" not in raw:
            errors.append(f"role count `{raw}` must use role=n")
            continue
        role, count_text = raw.split("=", 1)
        role = role.strip()
        if role not in known_roles:
            errors.append(f"role count `{raw}` uses unknown role `{role}`")
            continue
        count = _parse_count(count_text)
        if count is None:
            errors.append(f"role count `{raw}` must use a non-negative integer")
            continue
        requests.append(
            CollaborationRoleCountRequest(
                role=role,
                requested_count=count,
                source="request",
            )
        )
    if architecture_agent_count > 0:
        requests.append(
            CollaborationRoleCountRequest(
                role="architect",
                requested_count=architecture_agent_count,
                source="architecture_agents",
            )
        )
    if review_agent_count > 0:
        requests.append(
            CollaborationRoleCountRequest(
                role="reviewer",
                requested_count=review_agent_count,
                source="review_agents",
            )
        )
    if (
        max_workers > 0
        and selected_mode is not None
        and selected_mode.audit_role
        and selected_mode_id == "agent_sync"
    ):
        requests.append(
            CollaborationRoleCountRequest(
                role=selected_mode.audit_role,
                requested_count=max_workers,
                source="max_workers",
            )
        )
    return _merge_role_count_requests(tuple(requests)), tuple(errors)


def _merge_role_count_requests(
    requests: tuple[CollaborationRoleCountRequest, ...],
) -> tuple[CollaborationRoleCountRequest, ...]:
    merged: dict[str, CollaborationRoleCountRequest] = {}
    for request in requests:
        previous = merged.get(request.role)
        if previous is None or request.requested_count >= previous.requested_count:
            source = request.source
            if previous is not None and previous.source != request.source:
                source = f"{previous.source}+{request.source}"
            merged[request.role] = CollaborationRoleCountRequest(
                role=request.role,
                requested_count=request.requested_count,
                source=source,
            )
    return tuple(merged.values())


def _resolved_role_budgets(
    *,
    requests: tuple[CollaborationRoleCountRequest, ...],
    selected_mode: DevelopCollaborationModeSpec | None,
    live_capacity_by_role: Mapping[str, int],
) -> tuple[CollaborationResolvedRoleBudget, ...]:
    budget_by_role = _budget_by_role(selected_mode)
    rows: list[CollaborationResolvedRoleBudget] = []
    for request in requests:
        budget = budget_by_role.get(request.role, _fallback_budget(request.role))
        status = "ok"
        reasons: list[str] = []
        resolved_count = request.requested_count
        if request.requested_count > budget.max_count:
            status = "capped"
            reasons.append("requested count exceeds selected mode policy")
            resolved_count = budget.max_count
        live_capacity = int(live_capacity_by_role.get(request.role, -1))
        if live_capacity >= 0 and request.requested_count > live_capacity:
            status = "capacity_limited"
            reasons.append("requested count exceeds live topology capacity")
            resolved_count = min(resolved_count, live_capacity)
        rows.append(
            CollaborationResolvedRoleBudget(
                role=request.role,
                requested_count=request.requested_count,
                resolved_count=resolved_count,
                max_count=budget.max_count,
                live_capacity=live_capacity,
                capacity_source=(
                    "resolve_role_topology" if live_capacity >= 0 else ""
                ),
                mutable_lane_limit=budget.mutable_lane_limit,
                budget_kind=budget.budget_kind,
                status=status,
                reasons=tuple(reasons),
            )
        )
    return tuple(rows)


def _live_capacity_by_role(review_state: Mapping[str, object]) -> dict[str, int]:
    """Return live capacity exposed by the shared role-topology reducer."""
    live_topology = resolve_role_topology(
        _mapping(review_state.get("bridge_liveness")),
        include_runtime_presence=True,
    )
    capacity: dict[str, int] = {}
    if live_topology.live_reviewer_providers:
        capacity["reviewer"] = len(live_topology.live_reviewer_providers)
    if live_topology.live_implementer_providers:
        capacity["implementer"] = len(live_topology.live_implementer_providers)
    if live_topology.live_operator_providers:
        capacity["operator"] = len(live_topology.live_operator_providers)
    return capacity


def _budget_by_role(
    selected_mode: DevelopCollaborationModeSpec | None,
) -> dict[str, RoleCountBudget]:
    if selected_mode is None:
        return {}
    return {budget.role: budget for budget in selected_mode.role_count_budgets}


def _fallback_budget(role: str) -> RoleCountBudget:
    return RoleCountBudget(role=role, max_count=1, budget_kind="read_only")


def _resolved_count_for(
    budgets: tuple[CollaborationResolvedRoleBudget, ...],
    role: str,
) -> int:
    for budget in budgets:
        if budget.role == role:
            return budget.resolved_count
    return 0


def _parse_count(value: object) -> int | None:
    text = str(value or "").strip()
    if not text.isdigit():
        return None
    return int(text)


def _command_plan(
    *,
    role_bindings: tuple[CollaborationRoleBinding, ...],
    agent_mind_providers: tuple[str, ...],
    source_packet_id: str,
    target_packet_id: str,
    stop_anchor_request: CollaborationStopAnchorRequest | None,
    source_ref: str,
    target_ref: str,
    advisory_wake_evidence: tuple[CollaborationProfileWakeEvidence, ...] = (),
) -> tuple[str, ...]:
    commands: list[str] = []
    wake_by_binding = {
        _wake_binding_key(row.role, row.provider, row.session_id): row
        for row in advisory_wake_evidence
    }
    for provider in agent_mind_providers:
        commands.append(
            "python3 dev/scripts/devctl.py agent-mind "
            f"--agent {provider} --since-cursor --project --format md --limit 20"
        )
    for packet_id in (source_packet_id, target_packet_id):
        if packet_id:
            commands.append(
                "python3 dev/scripts/devctl.py review-channel --action show "
                f"--packet-id {packet_id} --terminal none --format md"
            )
    if stop_anchor_request is not None:
        if stop_anchor_request.stop_at_packet_id:
            commands.append(
                "python3 dev/scripts/devctl.py review-channel --action show "
                f"--packet-id {stop_anchor_request.stop_at_packet_id} "
                "--terminal none --format md"
            )
        if stop_anchor_request.stop_at_mp_row_id:
            commands.append(
                "python3 dev/scripts/devctl.py develop show "
                f"--slice-id {stop_anchor_request.stop_at_mp_row_id} --format md"
            )
        if stop_anchor_request.status == "stop_anchor_due":
            commands.extend(_stop_anchor_post_commands(stop_anchor_request, role_bindings))
    for binding in role_bindings:
        wake = wake_by_binding.get(
            _wake_binding_key(binding.role, binding.provider, binding.session_id)
        )
        if wake is not None and _wake_attention_required(wake):
            commands.append(_actor_inbox_command(binding.provider))
        wake_packet_id = _wake_command_packet_id(wake)
        if wake_packet_id:
            commands.append(_packet_show_command(wake_packet_id))
        command = (
            "python3 dev/scripts/devctl.py agent-loop --format json "
            f"--actor {binding.provider} --role {binding.role}"
        )
        if binding.session_id:
            command = f"{command} --session-id {binding.session_id}"
        if wake_packet_id:
            command = f"{command} --packet {wake_packet_id}"
        commands.append(command)
    target = target_ref or source_ref
    if target:
        commands.append(
            "python3 dev/scripts/devctl.py develop design-preflight "
            f"--topic {target!r} --format md"
        )
    return tuple(dict.fromkeys(commands))


def _wake_binding_key(role: str, provider: str, session_id: str) -> tuple[str, str, str]:
    return (role, provider, session_id)


def _wake_attention_required(wake: CollaborationProfileWakeEvidence) -> bool:
    return (
        wake.arrival_kind != "none"
        or wake.attention_status not in {"", "none"}
        or bool(wake.wake_reason)
        or bool(wake.required_command)
        or bool(wake.pending_packet_ids)
    )


def _wake_command_packet_id(wake: CollaborationProfileWakeEvidence | None) -> str:
    if wake is None:
        return ""
    if wake.latest_relevant_packet_id:
        return wake.latest_relevant_packet_id
    return wake.pending_packet_ids[0] if wake.pending_packet_ids else ""


def _actor_inbox_command(provider: str) -> str:
    return (
        "python3 dev/scripts/devctl.py review-channel --action inbox "
        f"--target {provider} --actor {provider} --status pending "
        "--terminal none --format md"
    )


def _packet_show_command(packet_id: str) -> str:
    return (
        "python3 dev/scripts/devctl.py review-channel --action show "
        f"--packet-id {packet_id} --terminal none --format md"
    )


def _stop_anchor_post_commands(
    stop_anchor_request: CollaborationStopAnchorRequest,
    role_bindings: tuple[CollaborationRoleBinding, ...],
) -> tuple[str, ...]:
    bindings = role_bindings or (
        CollaborationRoleBinding(role="reviewer", provider="codex"),
        CollaborationRoleBinding(role="implementer", provider="claude"),
    )
    commands: list[str] = []
    summary = "agent_sync stop condition reached"
    body = (
        "agent_sync stop condition reached; end the bounded collaboration "
        "through SessionTerminationPolicy and scoped stop_anchor packets."
    )
    for binding in bindings:
        command = (
            "python3 dev/scripts/devctl.py review-channel --action post "
            f"--from-agent operator --to-agent {binding.provider} "
            f"--kind {stop_anchor_request.stop_packet_kind} "
            f"--summary {summary!r} --body {body!r} "
            f"--target-role {binding.role} --target-role-scoped"
        )
        if binding.session_id:
            command = f"{command} --target-session-id {binding.session_id}"
        commands.append(command)
    return tuple(commands)


def _stop_anchor_target_ref(
    request: CollaborationStopAnchorRequest,
) -> str:
    if request.stop_at_packet_id:
        return f"agent_sync:stop_at_packet:{request.stop_at_packet_id}"
    if request.stop_at_mp_row_id:
        return f"agent_sync:stop_at_mp_row:{request.stop_at_mp_row_id}"
    return "agent_sync:stop"


def _stop_anchor_request(
    *,
    stop_at_packet_id: object,
    stop_at_mp_row_id: object,
    selected_mode: DevelopCollaborationModeSpec | None,
    review_state: Mapping[str, object],
    plan_rows: Sequence[object],
) -> CollaborationStopAnchorRequest | None:
    packet_id = str(stop_at_packet_id or "").strip()
    row_id = str(stop_at_mp_row_id or "").strip()
    if not packet_id and not row_id:
        return None
    policy = (
        selected_mode.stop_anchor_policy
        if selected_mode is not None and selected_mode.stop_anchor_policy
        else STOP_ANCHOR_POLICY
    )
    reasons: list[str] = []
    validation_errors = list(
        _stop_anchor_target_validation_errors(
            packet_id=packet_id,
            row_id=row_id,
            selected_mode=selected_mode,
        )
    )
    if validation_errors:
        return CollaborationStopAnchorRequest(
            stop_at_packet_id=packet_id,
            stop_at_mp_row_id=row_id,
            status="invalid_stop_anchor_target",
            reasons=tuple(validation_errors),
            validation_errors=tuple(validation_errors),
            authority_policy=policy,
        )
    due = False
    missing = False
    if packet_id:
        packet = _packet_by_id(review_state, packet_id)
        if packet is None:
            missing = True
            reasons.append(f"stop_at_packet `{packet_id}` is not in review_state packets")
        elif _packet_is_resolved(packet):
            due = True
            reasons.append(f"stop_at_packet `{packet_id}` is acked_or_applied")
        else:
            reasons.append(f"stop_at_packet `{packet_id}` is still active")
    if row_id:
        plan_row = _plan_row_by_id(plan_rows, row_id)
        if plan_row is None:
            missing = True
            reasons.append(f"stop_at_mp_row `{row_id}` is not in plan rows")
        elif _plan_row_is_completed(plan_row):
            due = True
            reasons.append(f"stop_at_mp_row `{row_id}` is completed")
        else:
            reasons.append(
                f"stop_at_mp_row `{row_id}` status is {_plan_row_field(plan_row, 'status') or 'unknown'}"
            )
    status = "stop_anchor_due" if due else "waiting_for_stop_condition"
    if missing and not due:
        status = (
            "waiting_packet_not_found"
            if packet_id and not row_id
            else "waiting_plan_row_not_found"
            if row_id and not packet_id
            else "waiting_stop_target_not_found"
        )
    return CollaborationStopAnchorRequest(
        stop_at_packet_id=packet_id,
        stop_at_mp_row_id=row_id,
        status=status,
        reasons=tuple(reasons),
        authority_policy=policy,
    )


def _stop_anchor_target_validation_errors(
    *,
    packet_id: str,
    row_id: str,
    selected_mode: DevelopCollaborationModeSpec | None,
) -> tuple[str, ...]:
    allowed_targets = (
        set(selected_mode.stop_anchor_targets or ())
        if selected_mode is not None
        else set()
    )
    allowed_text = ", ".join(sorted(allowed_targets)) or "(none)"
    mode_id = selected_mode.mode_id if selected_mode is not None else "(unknown)"
    errors: list[str] = []
    if packet_id and "packet_ack_or_apply" not in allowed_targets:
        errors.append(
            "stop_at_packet requires selected mode "
            f"`{mode_id}` to allow stop_anchor target `packet_ack_or_apply`; "
            f"allowed targets: {allowed_text}"
        )
    if row_id and "plan_row_completed" not in allowed_targets:
        errors.append(
            "stop_at_mp_row requires selected mode "
            f"`{mode_id}` to allow stop_anchor target `plan_row_completed`; "
            f"allowed targets: {allowed_text}"
        )
    return tuple(errors)


def _packet_by_id(
    review_state: Mapping[str, object],
    packet_id: str,
) -> Mapping[str, object] | None:
    for packet in _rows(review_state.get("packets")):
        if str(packet.get("packet_id") or "").strip() == packet_id:
            return packet
    return None


def _packet_is_resolved(packet: Mapping[str, object]) -> bool:
    status = str(packet.get("status") or "").strip()
    lifecycle = str(packet.get("lifecycle_current_state") or "").strip()
    return status in {"acked", "applied"} or lifecycle in {"acknowledged", "applied"}


def _plan_row_by_id(
    plan_rows: Sequence[object],
    row_id: str,
) -> object | None:
    for row in plan_rows:
        if _plan_row_field(row, "row_id") == row_id:
            return row
    return None


def _plan_row_is_completed(row: object) -> bool:
    return _plan_row_field(row, "status") in {
        "applied",
        "closed",
        "complete",
        "completed",
        "done",
    }


def _plan_row_field(row: object, field_name: str) -> str:
    if isinstance(row, Mapping):
        return str(row.get(field_name) or "").strip()
    return str(getattr(row, field_name, "") or "").strip()


def _max_architecture_agents(mode: DevelopCollaborationModeSpec | None) -> int:
    if mode and mode.max_audit_agent_count > 0:
        return mode.max_audit_agent_count
    return 3


def _session_for_role(
    review_state: Mapping[str, object],
    *,
    provider: str,
    role: str,
    session_posture: SessionPosture | None,
) -> str:
    if session_posture is not None:
        for actor in session_posture.actors:
            actor_provider = normalize_provider_id(actor.provider or actor.actor_id)
            if actor_provider == provider and actor.role == role:
                return actor.actor_id or actor.provider
    for row in _rows(_mapping(review_state.get("agent_work_board")).get("rows")):
        if (
            normalize_provider_id(row.get("provider") or row.get("actor_id")) == provider
            and str(row.get("role") or "").strip() == role
        ):
            return str(row.get("session_id") or "").strip()
    for row in _rows(review_state.get("agent_loop_decisions")):
        if (
            normalize_provider_id(row.get("actor_id")) == provider
            and str(row.get("actor_role") or "").strip() == role
        ):
            return str(row.get("session_id") or "").strip()
    return ""


def _known_roles(
    topology: object,
    review_state: Mapping[str, object],
    session_posture: SessionPosture | None,
) -> set[str]:
    roles = {item.preset_id for item in topology.role_presets}
    if session_posture is not None:
        roles.update(actor.role for actor in session_posture.actors if actor.role)
    live_topology = resolve_role_topology(
        _mapping(review_state.get("bridge_liveness")),
        include_runtime_presence=True,
    )
    if live_topology.reviewer_provider:
        roles.add("reviewer")
    if live_topology.implementer_providers:
        roles.add("implementer")
    if live_topology.live_operator_providers:
        roles.add("operator")
    return roles


def _session_posture_from_review_state(
    review_state: Mapping[str, object],
) -> SessionPosture | None:
    runtime = _mapping(review_state.get("reviewer_runtime"))
    posture = session_posture_from_mapping(
        runtime.get("session_posture") or review_state.get("session_posture")
    )
    return posture if _session_posture_has_evidence(posture) else None


def _session_posture_from_collaboration(
    state: CollaborationSessionState | None,
) -> SessionPosture | None:
    if state is None:
        return None
    posture = state.session_posture
    return posture if _session_posture_has_evidence(posture) else None


def _session_posture_has_evidence(posture: SessionPosture | None) -> bool:
    return posture is not None and (
        bool(posture.actors) or posture.interaction_mode != "unresolved"
    )


def _split_provider_session(value: str) -> tuple[str, str]:
    target = value.strip()
    if ":" not in target:
        return target, ""
    provider, session_id = target.split(":", 1)
    return provider.strip(), session_id.strip()


def _append_provider(providers: list[str], value: object) -> None:
    provider = normalize_provider_id(value)
    if provider and provider not in providers:
        providers.append(provider)


def _append_packet_id(packet_ids: list[str], value: object) -> None:
    packet_id = str(value or "").strip()
    if packet_id and packet_id not in packet_ids:
        packet_ids.append(packet_id)


def _rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "AUTHORITY_POLICY",
    "COORDINATION_SURFACES",
    "DEFAULT_PROFILE_ID",
    "PEER_POLLING_POLICY",
    "PROFILE_CONTRACT_ID",
    "PROFILE_SCHEMA_VERSION",
    "AgentCollaborationProfile",
    "CollaborationProfileActorAuthority",
    "CollaborationProfileArbitration",
    "CollaborationProfilePeerReview",
    "CollaborationProfileReadyGate",
    "CollaborationProfileSession",
    "CollaborationProfileWakeEvidence",
    "CollaborationRoleBinding",
    "CollaborationResolvedRoleBudget",
    "CollaborationRoleCountRequest",
    "CollaborationStopAnchorRequest",
    "build_agent_collaboration_profile",
    "profile_template",
]
