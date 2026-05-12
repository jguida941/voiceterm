"""Typed models for the startup-context runtime surface."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..platform.coordination_snapshot_models import CoordinationSnapshot
from .authority_snapshot import AuthoritySnapshot
from .finding_contracts import RejectedRuleTraceRecord, RuleMatchEvidenceRecord
from .lifetime_bypass_mode import BypassLifecycle
from .packet_intent_anchor import PacketIntentAnchor, PlanIterationSession
from .project_governance import ProjectGovernance
from .recovery_authority import RecoveryAuthorityState
from .review_state_models import (
    CollaborationSessionState,
    PacketInboxState,
    ReviewAttentionState,
    ReviewCurrentSessionState,
)
from .reviewer_runtime_models import (
    RemoteControlAttachmentState,
    ReviewerRuntimeContract,
)
from .runtime_truth_snapshot import RuntimeTruthSnapshot
from .session_posture import SessionPosture
from .startup_blocker_decision import BlockerSnapshot
from .startup_context_collaboration_output import (
    startup_authority_snapshot_dict,
    startup_collaboration_dict,
    startup_collaboration_summary_dict,
    startup_packet_intent_anchor_dict,
)
from .startup_context_compaction import (
    compact_connectivity_registry,
    compact_packet_carry_forward_debt,
    compact_packet_continuity_index,
    compact_product_thesis,
    startup_interaction_mode,
    startup_runtime_truth_dict,
)
from .startup_context_projections import (
    bounded_contract_ownership_map,
    startup_coordination_dict,
    startup_orphan_snapshot_dict,
)
from .startup_governance_projection import startup_governance_dict
from .startup_packet_inbox import startup_packet_inbox_dict
from .startup_push_decision import PushDecisionState
from .work_intake import WorkIntakePacket
from .worktree_orphan_snapshot import OrphanSnapshot


@dataclass(frozen=True, slots=True)
class ReviewerGateState:
    """Current reviewer/ready-gate inputs for safe checkpoint/push decisions."""

    bridge_active: bool = False
    reviewer_mode: str = "single_agent"
    effective_reviewer_mode: str = "single_agent"
    review_accepted: bool = False
    required_checks_status: str = "unknown"
    checkpoint_permitted: bool = True
    review_gate_allows_push: bool = False
    implementation_blocked: bool = False
    implementation_block_reason: str = ""
    recovery_diagnosis_status: str = ""
    recovery_action_id: str = ""
    recovery_command: str = ""
    operator_interaction_mode: str = "unresolved"


@dataclass(frozen=True, slots=True)
class StartupContext:
    """Typed packet for AI agent session startup."""

    schema_version: int = 1
    contract_id: str = "StartupContext"
    governance: ProjectGovernance | None = None
    reviewer_gate: ReviewerGateState = field(default_factory=ReviewerGateState)
    push_decision: PushDecisionState = field(default_factory=PushDecisionState)
    advisory_action: str = "continue_editing"
    advisory_reason: str = ""
    observed_control_topology: str = "no_live_agents"
    implementation_permission: str = "blocked"
    recovery_authority: RecoveryAuthorityState = field(
        default_factory=RecoveryAuthorityState
    )
    rule_summary: str = ""
    match_evidence: tuple[RuleMatchEvidenceRecord, ...] = ()
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...] = ()
    product_thesis: str = ""
    work_intake: WorkIntakePacket | None = None
    coordination: CoordinationSnapshot | None = None
    authority_snapshot: AuthoritySnapshot | None = None
    collaboration: CollaborationSessionState | None = None
    reviewer_runtime: ReviewerRuntimeContract | None = None
    session_posture: SessionPosture | None = None
    runtime_truth: RuntimeTruthSnapshot | None = None
    remote_control_attachment: RemoteControlAttachmentState | None = None
    attention: ReviewAttentionState | None = None
    current_session: ReviewCurrentSessionState | None = None
    packet_inbox: PacketInboxState | None = None
    packet_intent_anchors: tuple[PacketIntentAnchor, ...] = ()
    plan_iteration_session: PlanIterationSession = field(
        default_factory=PlanIterationSession
    )
    quality_signals: dict[str, object] = field(default_factory=dict)
    orphan_snapshot: OrphanSnapshot | None = None
    blocker: BlockerSnapshot = field(default_factory=BlockerSnapshot)
    contract_ownership_map: dict[str, dict[str, object]] = field(default_factory=dict)
    connectivity_registry: dict[str, object] = field(default_factory=dict)
    runtime_spine_closure: dict[str, object] = field(default_factory=dict)
    packet_continuity_index: dict[str, object] = field(default_factory=dict)
    packet_carry_forward_debt: tuple[dict[str, object], ...] = ()
    continuity_attention: dict[str, object] = field(default_factory=dict)
    bypass_lifecycles: tuple[BypassLifecycle, ...] = ()
    key_surfaces: tuple[str, ...] = ()
    snapshot_id: str = ""
    zref: str = ""
    # Per Codex rev_pkt_2313/2326/2337: typed CoordinationStateProjection
    # passed through from review_state.coordination_state. The builder
    # populates this so recovery / startup / push consumers see the typed
    # 4-field split (coordination_topology / authority_mode /
    # recovery_eligibility / observed_runtime) alongside the legacy
    # observed_control_topology field.
    coordination_state_projection: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        d["schema_version"] = self.schema_version
        d["contract_id"] = self.contract_id
        d["action"] = self.advisory_action
        d["reason"] = self.advisory_reason
        d["advisory_action"] = self.advisory_action
        d["advisory_reason"] = self.advisory_reason
        if self.authority_snapshot is not None:
            d["interaction_mode"] = self.authority_snapshot.interaction_mode
            d["reviewer_mode"] = self.authority_snapshot.reviewer_mode
        else:
            d["interaction_mode"] = startup_interaction_mode(
                runtime_truth=self.runtime_truth,
                session_posture=self.session_posture,
                reviewer_gate=self.reviewer_gate,
            )
            d["reviewer_mode"] = (
                self.session_posture.reviewer_mode
                if self.session_posture is not None
                else self.reviewer_gate.reviewer_mode
            )
        d["observed_control_topology"] = self.observed_control_topology
        d["implementation_permission"] = self.implementation_permission
        # Per Codex rev_pkt_2313/2326/2337/2352: surface typed
        # coordination_state fields and demote legacy observed_control_topology
        # / reviewer_mode by attaching authority markers. Operators reading
        # startup-context JSON get explicit "this is the typed answer" vs
        # "this is the legacy compat field" provenance.
        coord = getattr(self, "coordination_state_projection", None) or {}
        for key in (
            "coordination_topology",
            "authority_mode",
            "recovery_eligibility",
        ):
            value = (coord or {}).get(key) if isinstance(coord, dict) else None
            if value:
                d[key] = value
        # Per rev_pkt_2352 demotion: when typed coordination_topology is
        # populated, tag legacy observed_control_topology as the legacy
        # compat surface so consumers don't trust it as primary.
        if isinstance(coord, dict) and coord.get("coordination_topology"):
            d["observed_control_topology_authority"] = "legacy"
            d["coordination_topology_authority"] = "primary"
        d["recovery_action"] = self.recovery_authority.recovery_action
        d["recovery_basis"] = self.recovery_authority.recovery_basis
        d["recovery_scope"] = self.recovery_authority.recovery_scope
        d["recovery_authority"] = self.recovery_authority.to_dict()
        d["rule_summary"] = self.rule_summary
        d["match_evidence"] = [evidence.to_dict() for evidence in self.match_evidence]
        d["rejected_rule_traces"] = [
            trace.to_dict() for trace in self.rejected_rule_traces
        ]
        d["reviewer_gate"] = asdict(self.reviewer_gate)
        d["push_decision"] = self.push_decision.to_dict()
        d["quality_signals"] = dict(self.quality_signals)
        d["blocker"] = self.blocker.to_dict()
        d["contract_ownership_map"] = bounded_contract_ownership_map(
            self.contract_ownership_map
        )
        d["connectivity_registry"] = compact_connectivity_registry(
            self.connectivity_registry
        )
        d["runtime_spine_closure"] = dict(self.runtime_spine_closure)
        d["packet_continuity_index"] = compact_packet_continuity_index(
            self.packet_continuity_index
        )
        d["packet_carry_forward_debt"] = compact_packet_carry_forward_debt(
            self.packet_carry_forward_debt
        )
        d["continuity_attention"] = dict(self.continuity_attention)
        if self.bypass_lifecycles:
            d["bypass_lifecycles"] = [
                lifecycle.to_dict() for lifecycle in self.bypass_lifecycles
            ]
        d["key_surfaces"] = list(self.key_surfaces)
        d["snapshot_id"] = self.snapshot_id
        d["zref"] = self.zref
        if self.product_thesis:
            d["product_thesis"] = compact_product_thesis(self.product_thesis)
        if self.governance is not None:
            d["governance"] = startup_governance_dict(self.governance)
        if self.work_intake is not None:
            d["work_intake"] = self.work_intake.to_dict()
        if self.coordination is not None:
            d["coordination"] = startup_coordination_dict(self.coordination)
        if self.authority_snapshot is not None:
            d["authority_snapshot"] = startup_authority_snapshot_dict(
                self.authority_snapshot
            )
        if self.collaboration is not None:
            if self.authority_snapshot is None:
                d["collaboration"] = startup_collaboration_dict(self.collaboration)
            else:
                d["collaboration"] = startup_collaboration_summary_dict(
                    self.collaboration
                )
        if self.reviewer_runtime is not None:
            reviewer_runtime = asdict(self.reviewer_runtime)
            reviewer_runtime.pop("session_posture", None)
            d["reviewer_runtime"] = reviewer_runtime
        if self.session_posture is not None:
            d["session_posture"] = self.session_posture.to_dict()
        if self.runtime_truth is not None:
            d["runtime_truth"] = startup_runtime_truth_dict(self.runtime_truth)
        if self.remote_control_attachment is not None:
            d["remote_control_attachment"] = asdict(self.remote_control_attachment)
        if self.attention is not None:
            d["attention"] = asdict(self.attention)
        if self.current_session is not None:
            d["current_session"] = asdict(self.current_session)
        if self.packet_inbox is not None:
            d["packet_inbox"] = startup_packet_inbox_dict(self.packet_inbox)
        if self.packet_intent_anchors:
            d["packet_intent_anchors"] = [
                startup_packet_intent_anchor_dict(anchor)
                for anchor in self.packet_intent_anchors
            ]
            d["plan_iteration_session"] = self.plan_iteration_session.to_dict()
        if self.orphan_snapshot is not None:
            d["orphan_snapshot"] = startup_orphan_snapshot_dict(self.orphan_snapshot)
        return d


__all__ = [
    "ReviewerGateState",
    "StartupContext",
    "startup_packet_intent_anchor_dict",
]
