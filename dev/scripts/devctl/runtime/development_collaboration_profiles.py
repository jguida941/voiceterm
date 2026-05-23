"""Provider-neutral collaboration profile contracts for ``/develop``."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from .development_collaboration_modes import (
    DevelopCollaborationModeSpec,
    build_default_collaboration_mode_topology,
)
from .development_collaboration_profile_bindings import (
    mapping as _mapping,
    role_bindings as read_role_bindings,
    rows as _rows,
)
from .development_collaboration_profile_counts import (
    live_capacity_by_role,
    resolved_count_for,
    resolved_role_budgets,
    role_count_requests as read_role_count_requests,
)
from .development_collaboration_profile_posture import (
    session_posture_from_collaboration,
    session_posture_from_review_state,
)
from .development_collaboration_profile_providers import (
    agent_mind_providers as read_agent_mind_providers,
    provider_errors,
    providers as read_providers,
    validation_warnings,
)
from .development_collaboration_profile_wake import (
    advisory_wake_evidence as read_advisory_wake_evidence,
)
from .provider_registry import is_valid_provider_id, normalize_provider_id
from .review_state_collaboration_models import CollaborationSessionState
from .review_state_parser import review_state_from_payload
from .role_topology import resolve_role_topology
from .session_termination_policy import (
    CONTINUATION_ANCHOR_PACKET_KIND,
    STOP_ANCHOR_PACKET_KIND,
)
from .session_posture import SessionPosture

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
        or session_posture_from_review_state(state)
        or session_posture_from_collaboration(collaboration_state)
    )
    roles = _known_roles(topology, state, posture)
    selected_mode = modes.get(selected_mode_id)
    role_count_requests, role_count_errors = read_role_count_requests(
        role_counts,
        architecture_agent_count=architecture_agent_count,
        review_agent_count=review_agent_count,
        max_workers=max_workers,
        selected_mode=selected_mode,
        selected_mode_id=selected_mode_id,
        known_roles=roles,
        request_type=CollaborationRoleCountRequest,
    )
    resolved_budgets = resolved_role_budgets(
        requests=role_count_requests,
        selected_mode=selected_mode,
        live_capacity_by_role=live_capacity_by_role(state),
        resolved_budget_type=CollaborationResolvedRoleBudget,
    )
    architecture_count = resolved_count_for(resolved_budgets, "architect")
    review_count = resolved_count_for(resolved_budgets, "reviewer")
    bindings, binding_errors = read_role_bindings(
        role_bindings,
        known_roles=roles,
        review_state=state,
        session_posture=posture,
        binding_type=CollaborationRoleBinding,
    )
    advisory_wake_evidence = read_advisory_wake_evidence(
        role_bindings=bindings,
        review_state=state,
        events=events,
        wake_evidence_type=CollaborationProfileWakeEvidence,
    )
    provider_ids = read_providers(
        requested=providers,
        role_bindings=bindings,
        agent_mind_providers=agent_mind_providers,
        remote_provider=remote_provider,
        default_profile_providers=DEFAULT_PROFILE_PROVIDERS,
    )
    mind_providers = read_agent_mind_providers(
        requested=agent_mind_providers,
        providers=provider_ids,
        default_profile_providers=DEFAULT_PROFILE_PROVIDERS,
    )
    remote = normalize_provider_id(remote_provider)
    max_architects = _max_architecture_agents(selected_mode)
    warnings = validation_warnings(
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
    errors = _profile_validation_errors(
        binding_errors=binding_errors,
        role_count_errors=role_count_errors,
        provider_ids=provider_ids,
        mind_providers=mind_providers,
        remote=remote,
        resolved_budgets=resolved_budgets,
        stop_anchor=stop_anchor,
    )
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


def _profile_validation_errors(
    *,
    binding_errors: tuple[str, ...],
    role_count_errors: tuple[str, ...],
    provider_ids: tuple[str, ...],
    mind_providers: tuple[str, ...],
    remote: str,
    resolved_budgets: tuple[CollaborationResolvedRoleBudget, ...],
    stop_anchor: CollaborationStopAnchorRequest | None,
) -> list[str]:
    errors = [
        *binding_errors,
        *role_count_errors,
        *provider_errors(provider_ids),
        *provider_errors(mind_providers, label="agent-mind provider"),
    ]
    if remote and not is_valid_provider_id(remote):
        errors.append(f"remote provider `{remote}` is not a valid provider id")
    for row in resolved_budgets:
        if row.status not in {"capped", "capacity_limited", "invalid"}:
            continue
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
    if stop_anchor is not None and stop_anchor.validation_errors:
        errors.extend(stop_anchor.validation_errors)
    return errors


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


class MissingTypedCollaborationSessionError(RuntimeError):
    """Raised when stop-anchor command generation cannot resolve typed role bindings.

    Production code must not fall back to hardcoded provider-role literals such
    as ``(role="reviewer", provider="codex")`` and ``(role="implementer",
    provider="claude")`` per the AntiDumbass amendment (``delete_after_ingest.md``
    lines 731-870): provider names are adapter identities, not role authority.

    Callers must supply ``role_bindings`` resolved from typed
    ``CollaborationSessionState`` (typically via ``read_role_bindings`` over
    ``session_records[*]`` and the bridge-liveness role assignments). If no
    typed session is active, the caller must surface this error instead of
    silently emitting a two-provider command plan.
    """


def _stop_anchor_post_commands(
    stop_anchor_request: CollaborationStopAnchorRequest,
    role_bindings: tuple[CollaborationRoleBinding, ...],
) -> tuple[str, ...]:
    if not role_bindings:
        raise MissingTypedCollaborationSessionError(
            "stop-anchor post command generation requires typed role_bindings "
            "resolved from an active CollaborationSessionState; refusing to "
            "fall back to hardcoded codex/claude provider pairs."
        )
    bindings = role_bindings
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
