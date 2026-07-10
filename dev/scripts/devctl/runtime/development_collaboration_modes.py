"""Read-only collaboration modes and role presets for ``/develop``."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .action_contracts import RUN_RECORD_CONTRACT_ID
from .evidence_receipts import (
    DOGFOOD_SELF_CHECK_RECEIPT_CONTRACT_ID,
    REVIEWER_AUDIT_RECEIPT_CONTRACT_ID,
)

COLLABORATION_MODE_CONTRACT_ID = "CollaborationModeTopology"
COLLABORATION_MODE_SCHEMA_VERSION = 1
MODE_CHAIN_CONTRACT_ID = "ModeChainComposition"
MODE_CHAIN_SCHEMA_VERSION = 1
DEFAULT_COMPOSITE_RECEIPT_CHILD_KINDS = (
    RUN_RECORD_CONTRACT_ID,
    DOGFOOD_SELF_CHECK_RECEIPT_CONTRACT_ID,
    REVIEWER_AUDIT_RECEIPT_CONTRACT_ID,
)


@dataclass(frozen=True, slots=True)
class PacketAttentionPressurePolicy:
    """Repo-pack configurable defaults for packet-aware attention."""

    soft_attention_budget: int = 12
    hard_attention_budget: int = 15
    near_ttl_minutes: int = 10
    budget_behavior: str = (
        "crossing a packet budget triggers classification and receipt coverage, "
        "never blind autodrain"
    )
    durable_intent_policy: str = (
        "classify durable intent as soon as detected and route to typed owner "
        "or terminal receipt"
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DevelopRolePresetSpec:
    preset_id: str
    display_name: str
    workstreams: tuple[str, ...]
    mutation_policy: str
    authority_requirements: tuple[str, ...]
    durable_outputs: tuple[str, ...]
    blocked_authority: tuple[str, ...]
    attention_subscription: str = "AgentAttentionLoop"
    timing_policy: str = "typed_event_driven_no_independent_poll"
    attention_events: tuple[str, ...] = ("packet_arrival", "peer_state_change", "subprocess_exit", "plan_row_change", "watchdog_signal", "role_flip")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "workstreams",
            "authority_requirements",
            "durable_outputs",
            "blocked_authority",
            "attention_events",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class RoleCountBudget:
    """Per-role fanout budget for one collaboration mode."""

    role: str
    default_count: int = 0
    max_count: int = 1
    mutable_lane_limit: int = 0
    budget_kind: str = "read_only"
    required_gates: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_gates"] = list(payload["required_gates"])
        return payload


@dataclass(frozen=True, slots=True)
class PhaseSequenceContract:
    """Ordering rules for chaining collaboration modes."""

    default_ordering: str = "sequential"
    primary_phase_policy: str = "selected role preset is phase 1"
    child_phase_policy: str = "child phases run after parent output exists"
    interleaving_policy: str = "explicit_phase_only"
    phase_boundary_receipts: tuple[str, ...] = ("RunRecord", "SessionActivityEntry")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["phase_boundary_receipts"] = list(self.phase_boundary_receipts)
        return payload


@dataclass(frozen=True, slots=True)
class ConflictingModeRule:
    """One fail-closed conflict rule for mode-chain requests."""

    rule_id: str
    selectors: tuple[str, ...]
    validation_stage: str
    reason: str
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selectors"] = list(self.selectors)
        return payload


@dataclass(frozen=True, slots=True)
class ScopeInheritanceContract:
    """Scope propagation rules between parent and child phases."""

    default_policy: str = "same_or_narrower"
    allowed_policies: tuple[str, ...] = ("inherits_parent_scope", "narrows_parent_scope")
    blocked_when: tuple[str, ...] = (
        "child widens parent scope without operator approval",
        "child omits scope when parent has an explicit scope",
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_policies"] = list(self.allowed_policies)
        payload["blocked_when"] = list(self.blocked_when)
        return payload


@dataclass(frozen=True, slots=True)
class LaneCardinalityEnforcer:
    """Control-plane lane limits for chained-mode requests."""

    max_chain_phases: int = 4
    max_live_tree_writers: int = 1
    max_independent_next_derivers: int = 1
    role_count_budget_source: str = "DevelopCollaborationModeSpec.role_count_budgets"
    enforcement_stage: str = "request_normalization_and_dispatch"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CompositeReceiptContainer:
    """Receipt-chain policy for completed mode chains."""

    emit_stage: str = "chain_completion"
    phase_boundary_policy: str = "child phases emit their native receipts"
    session_activity_log_policy: str = (
        "SessionActivityLog references child receipts and the composite receipt"
    )
    required_child_receipt_kinds: tuple[str, ...] = (
        DEFAULT_COMPOSITE_RECEIPT_CHILD_KINDS
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_child_receipt_kinds"] = list(
            self.required_child_receipt_kinds
        )
        return payload


@dataclass(frozen=True, slots=True)
class ModeChainPolicy:
    """Typed policy bundle for composable slash-command modes."""

    phase_sequence: PhaseSequenceContract
    conflict_rules: tuple[ConflictingModeRule, ...]
    scope_inheritance: ScopeInheritanceContract
    lane_cardinality: LaneCardinalityEnforcer
    composite_receipt: CompositeReceiptContainer
    authority_policy: str = (
        "mode chains compile request metadata only; AuthoritySnapshot, "
        "AgentDispatchRouter, OrphanSnapshot, and leases still grant work"
    )
    schema_version: int = MODE_CHAIN_SCHEMA_VERSION
    contract_id: str = MODE_CHAIN_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["phase_sequence"] = self.phase_sequence.to_dict()
        payload["conflict_rules"] = [item.to_dict() for item in self.conflict_rules]
        payload["scope_inheritance"] = self.scope_inheritance.to_dict()
        payload["lane_cardinality"] = self.lane_cardinality.to_dict()
        payload["composite_receipt"] = self.composite_receipt.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class ModeChainPhase:
    """One requested phase in a composable mode chain."""

    phase_id: str
    order: int
    role_preset: str
    collaboration_mode: str
    phase_kind: str
    scope_ref: str = ""
    scope_inherited_from: str = ""
    scope_policy: str = "same_or_narrower"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ChainReceiptRef:
    """Typed child receipt reference carried by a mode-chain composition."""

    receipt_ref: str
    expected_contract_id: str = ""
    phase_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModeChainComposition:
    """Canonical composition object behind the mode-chain report projection."""

    chain_id: str
    phases: tuple[ModeChainPhase, ...]
    receipt_refs: tuple[ChainReceiptRef, ...]
    policy: ModeChainPolicy
    effective_reviewer_mode: str = ""
    schema_version: int = MODE_CHAIN_SCHEMA_VERSION
    contract_id: str = MODE_CHAIN_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["phases"] = [item.to_dict() for item in self.phases]
        payload["receipt_refs"] = [item.to_dict() for item in self.receipt_refs]
        payload["policy"] = self.policy.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class ModeChainCompositionReport:
    """Resolved mode-chain request embedded in `/develop` output."""

    chain_id: str
    requested_chain_phases: tuple[str, ...]
    phases: tuple[ModeChainPhase, ...]
    receipt_refs: tuple[str, ...]
    validation_errors: tuple[str, ...]
    validation_warnings: tuple[str, ...]
    ok: bool
    policy: ModeChainPolicy
    composition: ModeChainComposition
    effective_reviewer_mode: str = ""
    schema_version: int = MODE_CHAIN_SCHEMA_VERSION
    contract_id: str = MODE_CHAIN_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["requested_chain_phases"] = list(self.requested_chain_phases)
        payload["phases"] = [item.to_dict() for item in self.phases]
        payload["receipt_refs"] = list(self.receipt_refs)
        payload["validation_errors"] = list(self.validation_errors)
        payload["validation_warnings"] = list(self.validation_warnings)
        payload["policy"] = self.policy.to_dict()
        payload["composition"] = self.composition.to_dict()
        payload["receipt_ref_rows"] = [
            item.to_dict() for item in self.composition.receipt_refs
        ]
        return payload


@dataclass(frozen=True, slots=True)
class DevelopCollaborationModeSpec:
    mode_id: str
    display_name: str
    purpose: str
    participant_roles: tuple[str, ...]
    mutable_fanout_allowed: bool = False
    default_worker_fanout: int = 0
    required_gates: tuple[str, ...] = ()
    durable_outputs: tuple[str, ...] = ()
    blocked_when: tuple[str, ...] = ()
    coordination_surfaces: tuple[str, ...] = ()
    peer_polling_policy: str = ""
    role_count_policy: str = ""
    role_count_budgets: tuple[RoleCountBudget, ...] = ()
    audit_role: str = ""
    default_audit_agent_count: int = 0
    max_audit_agent_count: int = 0
    stop_anchor_policy: str = ""
    stop_anchor_targets: tuple[str, ...] = ()
    stop_anchor_packet_kinds: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "participant_roles",
            "required_gates",
            "durable_outputs",
            "blocked_when",
            "coordination_surfaces",
            "stop_anchor_targets",
            "stop_anchor_packet_kinds",
        ):
            payload[key] = list(payload[key])
        payload["role_count_budgets"] = [
            item.to_dict() for item in self.role_count_budgets
        ]
        return payload


@dataclass(frozen=True, slots=True)
class CollaborationModeTopology:
    topology_id: str
    modes: tuple[DevelopCollaborationModeSpec, ...]
    role_presets: tuple[DevelopRolePresetSpec, ...]
    packet_pressure_policy: PacketAttentionPressurePolicy
    mode_chain_policy: ModeChainPolicy
    authority_policy: str
    slash_adapter_policy: str
    default_mode_id: str = "solo"
    default_role_preset_id: str = "dashboard"
    default_worker_fanout: int = 0
    schema_version: int = COLLABORATION_MODE_SCHEMA_VERSION
    contract_id: str = COLLABORATION_MODE_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["modes"] = [item.to_dict() for item in self.modes]
        payload["role_presets"] = [item.to_dict() for item in self.role_presets]
        payload["packet_pressure_policy"] = self.packet_pressure_policy.to_dict()
        payload["mode_chain_policy"] = self.mode_chain_policy.to_dict()
        return payload


ROLE_PRESETS = (
    DevelopRolePresetSpec(
        preset_id="dashboard",
        display_name="Dashboard",
        workstreams=("coordinator", "runtime_watcher"),
        mutation_policy="read_only",
        authority_requirements=("runtime_read", "packet_read"),
        durable_outputs=("DevelopmentLoopReport", "stale_state_report"),
        blocked_authority=("repo.stage", "repo.commit", "approval.commit"),
    ),
    DevelopRolePresetSpec(
        preset_id="implementer",
        display_name="Implementer",
        workstreams=("builder",),
        mutation_policy="requires_mutation_lease",
        authority_requirements=("MutationLease", "repo.stage", "repo.commit"),
        durable_outputs=("source_diff", "RunRecord", "completion_packet"),
        blocked_authority=("self_accept_review",),
    ),
    DevelopRolePresetSpec(
        preset_id="reviewer",
        display_name="Reviewer",
        workstreams=("reviewer",),
        mutation_policy="read_only",
        authority_requirements=("review_packet_read", "artifact_read"),
        durable_outputs=("FindingReview", "PacketDisposition"),
        blocked_authority=("repo.stage", "repo.commit"),
    ),
    DevelopRolePresetSpec(
        preset_id="architect",
        display_name="Architect",
        workstreams=("architect",),
        mutation_policy="typed_plan_proposals_only",
        authority_requirements=("plan_read", "contract_read"),
        durable_outputs=("PlanProposal", "PlanRow", "PatternObservation"),
        blocked_authority=("repo.stage", "repo.commit"),
    ),
    DevelopRolePresetSpec(
        preset_id="researcher",
        display_name="Researcher",
        workstreams=("researcher",),
        mutation_policy="read_only_or_isolated_draft",
        authority_requirements=("ResearchRouteGrant", "source_provenance"),
        durable_outputs=("ResearchEvidenceBundle", "ExternalSourceEvidence"),
        blocked_authority=("uncited_claim_as_authority", "live_tree_mutation"),
    ),
    DevelopRolePresetSpec(
        preset_id="intake",
        display_name="Intake",
        workstreams=("plan_intake_steward",),
        mutation_policy="typed_state_writes_only",
        authority_requirements=("packet_read", "master_plan_store_write"),
        durable_outputs=(
            "PlanRow", "PlanIntentIngestionReceipt", "PacketDurableIngestionReceipt",
        ),
        blocked_authority=("repo.stage", "repo.commit"),
    ),
    DevelopRolePresetSpec(
        preset_id="tester",
        display_name="Tester",
        workstreams=("quality_engineer", "dogfood_tester"),
        mutation_policy="evidence_only",
        authority_requirements=("guard_run", "dogfood_route"),
        durable_outputs=("RunRecord", "DogfoodRun", "GuardSmartnessReport"),
        blocked_authority=("approval.override",),
    ),
    DevelopRolePresetSpec(
        preset_id="watcher",
        display_name="Watcher",
        workstreams=("runtime_watcher",),
        mutation_policy="read_only",
        authority_requirements=("runtime_read", "packet_read"),
        durable_outputs=("stale_state_report", "attention_recommendation"),
        blocked_authority=("repo.stage", "repo.commit"),
    ),
    DevelopRolePresetSpec(
        preset_id="operator",
        display_name="Operator",
        workstreams=("operator",),
        mutation_policy="approval_receipts_only",
        authority_requirements=("approval_authority",),
        durable_outputs=("approval_receipt", "override_receipt"),
        blocked_authority=("repo.stage", "repo.commit"),
    ),
)

COLLABORATION_MODES = (
    DevelopCollaborationModeSpec(
        mode_id="solo",
        display_name="Solo",
        purpose="one actor works through typed authority with no implicit self-review",
        participant_roles=("requested_role",),
        blocked_when=("review evidence would be self-accepted",),
    ),
    DevelopCollaborationModeSpec(
        mode_id="pair_review",
        display_name="Pair Review",
        purpose="implementer plus reviewer coordinate through packet-mediated review",
        participant_roles=("implementer", "reviewer"),
        durable_outputs=("FindingReview", "PacketDisposition", "RunRecord"),
    ),
    DevelopCollaborationModeSpec(
        mode_id="dashboard_led",
        display_name="Dashboard Led",
        purpose="dashboard/operator observes, routes, and approves while mutation happens elsewhere",
        participant_roles=("dashboard", "operator", "implementer"),
        durable_outputs=("DevelopmentLoopReport", "approval_receipt"),
    ),
    DevelopCollaborationModeSpec(
        mode_id="intake_fanout",
        display_name="Intake Fanout",
        purpose="intake agents classify packet pressure into durable typed state",
        participant_roles=("intake",),
        durable_outputs=("PlanIntentIngestionReceipt", "PacketDurableIngestionReceipt"),
    ),
    DevelopCollaborationModeSpec(
        mode_id="research_fanout",
        display_name="Research Fanout",
        purpose="researchers and architects gather evidence and propose typed rows",
        participant_roles=("researcher", "architect"),
        durable_outputs=("ResearchEvidenceBundle", "PlanProposal"),
    ),
    DevelopCollaborationModeSpec(
        mode_id="review_fanout",
        display_name="Review Fanout",
        purpose="reviewers and testers inspect disjoint evidence without mutation",
        participant_roles=("reviewer", "tester"),
        durable_outputs=("FindingReview", "RunRecord"),
    ),
    DevelopCollaborationModeSpec(
        mode_id="watcher_fanout",
        display_name="Watcher Fanout",
        purpose="watchers track stale packets, attention gaps, process drift, and runtime drift",
        participant_roles=("watcher",),
        durable_outputs=("stale_state_report", "attention_recommendation"),
    ),
    DevelopCollaborationModeSpec(
        mode_id="agent_sync",
        display_name="Agent Sync",
        purpose=(
            "any supported development role can be bound to a provider, "
            "counted, watched through agent-mind, and routed through typed packets"
        ),
        participant_roles=(
            "dashboard",
            "implementer",
            "reviewer",
            "architect",
            "researcher",
            "intake",
            "tester",
            "watcher",
            "operator",
        ),
        required_gates=(
            "AgentMindSlice fresh for watched providers",
            "PacketInboxState fresh",
            "role counts within repo-pack policy",
            "mutable lanes require safe_to_fanout, registered worktrees, and leases",
        ),
        durable_outputs=(
            "PlanRow",
            "FindingReview",
            "PacketDisposition",
            "ResearchEvidenceBundle",
            "PlanProposal",
            "RunRecord",
            "GuardSmartnessReport",
            "stale_state_report",
            "approval_receipt",
        ),
        blocked_when=(
            "agent_mind_claim_used_as_authority",
            "self_accepted_review",
            "unbounded_role_fanout",
            "provider_label_grants_mutation",
        ),
        coordination_surfaces=(
            "AgentMindSlice",
            "PacketInboxState",
            "ReviewPacketState",
            "AgentWorkBoardProjection",
            "AgentLoopDecision",
            "CollaborationSessionState",
        ),
        peer_polling_policy=(
            "agent-mind polling is advisory attention context only; packets, "
            "session posture, authority snapshots, and leases remain authority"
        ),
        role_count_policy=(
            "role counts are request metadata; repo-pack policy and runtime "
            "authority decide whether each lane can run, mutate, or remain read-only"
        ),
        stop_anchor_policy=(
            "stop-at flags are typed stop-anchor readiness metadata; session "
            "termination only happens through continuation_anchor / stop_anchor "
            "packets and SessionTerminationPolicy, never chat prose"
        ),
        stop_anchor_targets=("packet_ack_or_apply", "plan_row_completed"),
        stop_anchor_packet_kinds=("continuation_anchor", "stop_anchor"),
        role_count_budgets=(
            RoleCountBudget(role="dashboard", max_count=1, budget_kind="read_only"),
            RoleCountBudget(
                role="implementer",
                max_count=3,
                budget_kind="mutable_requires_lease",
                required_gates=(
                    "AgentDispatchRouter.safe_to_fanout=true for fanout",
                    "registered worktree for isolated mutation",
                    "session-bound MutationLease before live-tree mutation",
                ),
            ),
            RoleCountBudget(role="reviewer", max_count=5, budget_kind="read_only"),
            RoleCountBudget(
                role="architect",
                max_count=3,
                budget_kind="typed_plan_proposals_only",
            ),
            RoleCountBudget(
                role="researcher",
                max_count=3,
                budget_kind="evidence_only",
                required_gates=("ResearchRouteGrant for web/vendor/library work",),
            ),
            RoleCountBudget(
                role="intake",
                max_count=3,
                budget_kind="typed_state_only",
            ),
            RoleCountBudget(role="tester", max_count=4, budget_kind="evidence_only"),
            RoleCountBudget(role="watcher", max_count=4, budget_kind="read_only"),
            RoleCountBudget(role="operator", max_count=1, budget_kind="approval_only"),
        ),
        audit_role="architect",
        default_audit_agent_count=0,
        max_audit_agent_count=3,
    ),
    DevelopCollaborationModeSpec(
        mode_id="isolated_builder_fanout",
        display_name="Isolated Builder Fanout",
        purpose="builders draft in registered isolated worktrees",
        participant_roles=("implementer",),
        mutable_fanout_allowed=True,
        required_gates=(
            "safe_to_fanout=true", "disjoint scopes", "registered worktrees",
            "OrphanSnapshot clearance", "MutationLease",
        ),
        durable_outputs=("draft_patch", "RunRecord"),
        blocked_when=("unregistered worktree", "overlapping path scope"),
    ),
    DevelopCollaborationModeSpec(
        mode_id="dogfood_campaign",
        display_name="Dogfood Campaign",
        purpose=(
            "scripted multi-agent proof over /develop, packet, dashboard, "
            "guard, Claude dogfood packet surfaces, and dashboard subscriber parity"
        ),
        participant_roles=("dashboard", "implementer", "reviewer", "tester"),
        durable_outputs=("DogfoodRun", "RunRecord", "PacketDisposition"),
    ),
)


def build_default_mode_chain_policy() -> ModeChainPolicy:
    """Return the default typed policy for composable slash modes."""
    return ModeChainPolicy(
        phase_sequence=PhaseSequenceContract(),
        conflict_rules=(
            ConflictingModeRule(
                rule_id="single_primary_role_per_phase",
                selectors=("role_preset", "chain_phase"),
                validation_stage="request_normalization",
                reason=(
                    "each phase must compile to one role preset; adapters cannot "
                    "smuggle /reviewer and /implementer into one phase"
                ),
            ),
            ConflictingModeRule(
                rule_id="self_review_blocked_across_phases",
                selectors=("implementer", "reviewer"),
                validation_stage="dispatch_authority_gate",
                reason=(
                    "implementer output and reviewer acceptance must remain "
                    "distinct evidence paths"
                ),
            ),
            ConflictingModeRule(
                rule_id="strict_governance_disables_full_auto",
                selectors=("strict_governance", "full_auto"),
                validation_stage="request_normalization",
                reason=(
                    "strict governance mode cannot be combined with autonomous "
                    "terminal completion shortcuts"
                ),
            ),
        ),
        scope_inheritance=ScopeInheritanceContract(),
        lane_cardinality=LaneCardinalityEnforcer(),
        composite_receipt=CompositeReceiptContainer(),
    )


def build_default_collaboration_mode_topology() -> CollaborationModeTopology:
    """Return the default read-only collaboration topology for `/develop`."""
    return CollaborationModeTopology(
        topology_id="develop-collaboration-default",
        modes=COLLABORATION_MODES,
        role_presets=ROLE_PRESETS,
        packet_pressure_policy=PacketAttentionPressurePolicy(),
        mode_chain_policy=build_default_mode_chain_policy(),
        authority_policy=(
            "CollaborationModeTopology explains requested topology only; "
            "AuthoritySnapshot, SessionPosture, AgentDispatchRouter, "
            "OrphanSnapshot, and leases grant or block work."
        ),
        slash_adapter_policy=(
            "slash adapters may pass typed role and mode request fields to "
            "/develop or agent-loop, but contain no policy, provider defaults, "
            "permissions, or repo-local path authority"
        ),
    )


def collaboration_mode_report(
    *,
    requested_mode: object = "",
    requested_role_preset: object = "",
    max_workers: int = 0,
    chain_phases: tuple[object, ...] = (),
    dogfood: bool = False,
    generic_agent_count: int = 0,
    chain_scope: object = "",
    receipt_refs: tuple[object, ...] = (),
    role_counts: tuple[object, ...] = (),
    effective_reviewer_mode: object = "",
) -> dict[str, Any]:
    """Return the compact report payload embedded in DevelopmentLoopReport."""
    topology = build_default_collaboration_mode_topology()
    modes = {item.mode_id: item for item in topology.modes}
    roles = {item.preset_id: item for item in topology.role_presets}
    selected_mode_id = _selected_key(
        requested_mode,
        allowed=modes,
        default=topology.default_mode_id,
    )
    selected_role_id = _selected_key(
        requested_role_preset,
        allowed=roles,
        default=topology.default_role_preset_id,
    )
    selected_mode = modes[selected_mode_id]
    selected_role = roles[selected_role_id]
    payload = topology.to_dict()
    payload["requested_mode"] = str(requested_mode or "").strip()
    payload["requested_role_preset"] = str(requested_role_preset or "").strip()
    payload["selected_mode_id"] = selected_mode_id
    payload["selected_role_preset_id"] = selected_role_id
    payload["selected_mode"] = selected_mode.to_dict()
    payload["selected_role_preset"] = selected_role.to_dict()
    payload["mutable_fanout_status"] = _mutable_fanout_status(
        max_workers=max_workers,
        mode=selected_mode,
    )
    payload["mode_chain"] = mode_chain_report(
        selected_mode_id=selected_mode_id,
        selected_role_preset_id=selected_role_id,
        chain_phases=chain_phases,
        dogfood=dogfood,
        generic_agent_count=generic_agent_count,
        chain_scope=chain_scope,
        receipt_refs=receipt_refs,
        role_counts=role_counts,
        effective_reviewer_mode=effective_reviewer_mode,
        topology=topology,
    )
    return payload


def mode_chain_report(
    *,
    selected_mode_id: str,
    selected_role_preset_id: str,
    chain_phases: tuple[object, ...] = (),
    dogfood: bool = False,
    generic_agent_count: int = 0,
    chain_scope: object = "",
    receipt_refs: tuple[object, ...] = (),
    role_counts: tuple[object, ...] = (),
    effective_reviewer_mode: object = "",
    topology: CollaborationModeTopology | None = None,
) -> dict[str, Any]:
    """Resolve a composable mode-chain request against typed policy."""
    topology = topology or build_default_collaboration_mode_topology()
    policy = topology.mode_chain_policy
    roles = {item.preset_id for item in topology.role_presets}
    modes = {item.mode_id for item in topology.modes}
    scope_ref = str(chain_scope or "").strip()
    effective_mode = str(effective_reviewer_mode or "").strip()
    errors: list[str] = []
    warnings: list[str] = []
    phases: list[ModeChainPhase] = [
        ModeChainPhase(
            phase_id="phase-1-primary",
            order=1,
            role_preset=selected_role_preset_id,
            collaboration_mode=selected_mode_id,
            phase_kind="primary",
            scope_ref=scope_ref,
        )
    ]

    for raw in chain_phases:
        phase = _parse_chain_phase(
            raw,
            roles=roles,
            modes=modes,
            order=len(phases) + 1,
            parent_phase_id=phases[0].phase_id,
            scope_ref=scope_ref,
        )
        if isinstance(phase, str):
            errors.append(phase)
            continue
        phases.append(phase)

    if dogfood:
        phases.append(
            ModeChainPhase(
                phase_id=f"phase-{len(phases) + 1}-dogfood",
                order=len(phases) + 1,
                role_preset="tester",
                collaboration_mode="dogfood_campaign",
                phase_kind="dogfood",
                scope_ref=scope_ref,
                scope_inherited_from=phases[0].phase_id,
                scope_policy=policy.scope_inheritance.default_policy,
            )
        )

    _reviewer_mode_semantic_findings(
        effective_reviewer_mode=effective_mode,
        phases=tuple(phases),
        errors=errors,
        warnings=warnings,
    )
    if len(phases) > policy.lane_cardinality.max_chain_phases:
        errors.append(
            "mode chain declares "
            f"{len(phases)} phases; max is "
            f"{policy.lane_cardinality.max_chain_phases} so the chain cannot "
            "bypass D-DevelopNext cardinality"
        )
    if generic_agent_count < 0:
        errors.append("--agents must be non-negative")
    if generic_agent_count > 0 and selected_role_preset_id not in roles:
        errors.append(
            f"--agents cannot resolve unknown role `{selected_role_preset_id}`"
        )
    _role_count_warnings(
        role_counts=role_counts,
        phase_roles={phase.role_preset for phase in phases},
        warnings=warnings,
    )
    receipt_ref_rows = _chain_receipt_refs(receipt_refs)
    clean_receipt_refs = tuple(item.receipt_ref for item in receipt_ref_rows)
    if len(phases) > 1 and not receipt_ref_rows:
        warnings.append(
            "composite receipt container is pending child receipt refs until "
            "the chained phases run"
        )
    chain_id = "+".join(
        f"{phase.role_preset}:{phase.collaboration_mode}" for phase in phases
    )
    composition = ModeChainComposition(
        chain_id=chain_id,
        phases=tuple(phases),
        receipt_refs=receipt_ref_rows,
        policy=policy,
        effective_reviewer_mode=effective_mode,
    )
    return ModeChainCompositionReport(
        chain_id=chain_id,
        requested_chain_phases=tuple(
            str(item or "").strip() for item in chain_phases if str(item or "").strip()
        ),
        phases=tuple(phases),
        receipt_refs=clean_receipt_refs,
        validation_errors=tuple(errors),
        validation_warnings=tuple(warnings),
        ok=not errors,
        policy=policy,
        composition=composition,
        effective_reviewer_mode=effective_mode,
    ).to_dict()


def _parse_chain_phase(
    raw: object,
    *,
    roles: set[str],
    modes: set[str],
    order: int,
    parent_phase_id: str,
    scope_ref: str,
) -> ModeChainPhase | str:
    text = str(raw or "").strip()
    if not text:
        return "chain phase cannot be empty"
    if "+" in text or "," in text:
        return (
            f"chain phase `{text}` must declare one role; use repeated "
            "--chain-phase flags for multiple phases"
        )
    role, separator, mode = text.partition(":")
    role = role.strip()
    mode = mode.strip() if separator else _default_mode_for_role(role)
    if role not in roles:
        return f"chain phase `{text}` uses unknown role `{role}`"
    if mode not in modes:
        return f"chain phase `{text}` uses unknown collaboration mode `{mode}`"
    return ModeChainPhase(
        phase_id=f"phase-{order}-{role}",
        order=order,
        role_preset=role,
        collaboration_mode=mode,
        phase_kind="explicit",
        scope_ref=scope_ref,
        scope_inherited_from=parent_phase_id,
    )


def _default_mode_for_role(role: str) -> str:
    if role in {"architect", "researcher"}:
        return "research_fanout"
    if role in {"reviewer", "tester"}:
        return "review_fanout"
    if role == "intake":
        return "intake_fanout"
    if role == "watcher":
        return "watcher_fanout"
    if role in {"dashboard", "operator"}:
        return "dashboard_led"
    if role == "implementer":
        return "pair_review"
    return "solo"


def _chain_receipt_refs(receipt_refs: tuple[object, ...]) -> tuple[ChainReceiptRef, ...]:
    rows: list[ChainReceiptRef] = []
    for raw in receipt_refs:
        ref = str(raw or "").strip()
        if not ref:
            continue
        rows.append(
            ChainReceiptRef(
                receipt_ref=ref,
                expected_contract_id=_expected_receipt_contract_id(ref),
            )
        )
    return tuple(rows)


def _expected_receipt_contract_id(receipt_ref: str) -> str:
    prefix = receipt_ref.split(":", 1)[0].strip().lower()
    if prefix == "run":
        return RUN_RECORD_CONTRACT_ID
    if prefix == "dogfood":
        return DOGFOOD_SELF_CHECK_RECEIPT_CONTRACT_ID
    if prefix in {"audit", "review", "reviewer_audit"}:
        return REVIEWER_AUDIT_RECEIPT_CONTRACT_ID
    return ""


def _reviewer_mode_semantic_findings(
    *,
    effective_reviewer_mode: str,
    phases: tuple[ModeChainPhase, ...],
    errors: list[str],
    warnings: list[str],
) -> None:
    if not effective_reviewer_mode:
        return
    review_phase = any(
        phase.role_preset in {"reviewer", "tester"}
        or phase.collaboration_mode in {"review_fanout", "dogfood_campaign"}
        for phase in phases
    )
    if not review_phase:
        return
    if effective_reviewer_mode in {"paused", "offline"}:
        errors.append(
            "effective_reviewer_mode "
            f"`{effective_reviewer_mode}` cannot satisfy review/dogfood "
            "mode-chain phases"
        )
        return
    if effective_reviewer_mode in {"single_agent", "tools_only"}:
        warnings.append(
            "effective_reviewer_mode "
            f"`{effective_reviewer_mode}` limits review/dogfood phases to that "
            "runtime posture; live dual-agent proof still needs a compatible "
            "CollaborationSession"
        )


def _role_count_warnings(
    *,
    role_counts: tuple[object, ...],
    phase_roles: set[str],
    warnings: list[str],
) -> None:
    for raw in role_counts:
        text = str(raw or "").strip()
        if not text or "=" not in text:
            continue
        role = text.split("=", 1)[0].strip()
        if role and role not in phase_roles:
            warnings.append(
                f"role count `{text}` applies outside the explicit mode chain"
            )


def _selected_key(
    value: object,
    *,
    allowed: dict[str, object],
    default: str,
) -> str:
    text = str(value or "").strip()
    if text in allowed:
        return text
    return default


def _mutable_fanout_status(
    *,
    max_workers: int,
    mode: DevelopCollaborationModeSpec,
) -> str:
    if max_workers <= 0:
        return "not_requested"
    if mode.mutable_fanout_allowed:
        return "requires_safe_to_fanout_worktrees_orphan_snapshot_and_leases"
    return "blocked_by_read_model_mode"


__all__ = [
    "COLLABORATION_MODE_CONTRACT_ID",
    "COLLABORATION_MODE_SCHEMA_VERSION",
    "ChainReceiptRef",
    "CollaborationModeTopology",
    "CompositeReceiptContainer",
    "ConflictingModeRule",
    "DevelopCollaborationModeSpec",
    "DevelopRolePresetSpec",
    "LaneCardinalityEnforcer",
    "MODE_CHAIN_CONTRACT_ID",
    "MODE_CHAIN_SCHEMA_VERSION",
    "ModeChainComposition",
    "ModeChainCompositionReport",
    "ModeChainPhase",
    "ModeChainPolicy",
    "PacketAttentionPressurePolicy",
    "PhaseSequenceContract",
    "RoleCountBudget",
    "ScopeInheritanceContract",
    "build_default_collaboration_mode_topology",
    "build_default_mode_chain_policy",
    "collaboration_mode_report",
    "mode_chain_report",
]
