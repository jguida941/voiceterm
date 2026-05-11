"""Read-only collaboration modes and role presets for ``/develop``."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

COLLABORATION_MODE_CONTRACT_ID = "CollaborationModeTopology"
COLLABORATION_MODE_SCHEMA_VERSION = 1


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


def build_default_collaboration_mode_topology() -> CollaborationModeTopology:
    """Return the default read-only collaboration topology for `/develop`."""
    return CollaborationModeTopology(
        topology_id="develop-collaboration-default",
        modes=COLLABORATION_MODES,
        role_presets=ROLE_PRESETS,
        packet_pressure_policy=PacketAttentionPressurePolicy(),
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
    return payload


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
    "CollaborationModeTopology",
    "DevelopCollaborationModeSpec",
    "DevelopRolePresetSpec",
    "PacketAttentionPressurePolicy",
    "RoleCountBudget",
    "build_default_collaboration_mode_topology",
    "collaboration_mode_report",
]
