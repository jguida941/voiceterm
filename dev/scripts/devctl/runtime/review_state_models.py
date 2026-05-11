"""Typed review-state models shared by review-channel frontends."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..platform.coordination_snapshot_models import CoordinationSnapshot
from .authority_snapshot import AuthoritySnapshot
from .remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)
from .review_state_packet_models import (
    AgentAttentionRecord,
    AgentRegistryEntryState,
    AgentRegistryState,
    ContextPackRefState,
    PacketInboxState,
    ReviewCandidateRecord,
    ReviewPacketState,
    agent_attention_record_from_mapping,
    packet_inbox_from_mapping,
    review_candidate_from_mapping,
)
from .review_state_round_proof import RoundProofState
from .review_state_packet_models import (
    packet_requires_operator_approval as _packet_requires_operator_approval,
)
from .reviewer_runtime_models import (
    ReviewerAcceptanceState,
    ReviewerLastPollState,
    ReviewerRolloverState,
    ReviewerRuntimeContract,
    ReviewerSessionOwnerState,
)


@dataclass(frozen=True, slots=True)
class ReviewSessionState:
    plan_id: str
    controller_run_id: str
    session_id: str
    surface_mode: str
    active_lane: str
    refresh_seq: int = 0
    bridge_path: str = ""
    review_channel_path: str = ""


@dataclass(frozen=True, slots=True)
class ReviewQueueState:
    pending_total: int
    pending_codex: int
    pending_claude: int
    pending_cursor: int
    pending_operator: int
    stale_packet_count: int
    derived_next_instruction: str
    derived_next_instruction_source: dict[str, object]
    instruction_priority_decision: dict[str, object] = field(default_factory=dict)
    last_failed_action_request: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReviewCurrentSessionState:
    current_instruction: str
    current_instruction_revision: str
    implementer_status: str
    implementer_ack: str
    implementer_ack_revision: str
    implementer_ack_state: str
    implementer_state_hash: str = ""
    implementer_session_state: str = ""
    implementer_session_hint: str = ""
    open_findings: str = ""
    last_reviewed_scope: str = ""


from .review_state_collaboration_models import (  # noqa: E402,F401
    ActorAuthorityState,
    AgentSessionOutcomeState,
    CapabilityGrantState,
    CollaborationArbitrationState,
    CollaborationParticipantState,
    CollaborationPeerReviewState,
    CollaborationReadyGateState,
    CollaborationRestartState,
    CollaborationRoleAssignmentState,
    CollaborationSessionState,
    DelegatedWorkReceiptState,
)


@dataclass(frozen=True, slots=True)
class ConductorCapabilityState:
    provider: str
    role: str
    startup_context_command: str
    may_edit_repo: bool
    requires_explicit_takeover: bool
    worker_unavailable_policy: str
    queue_policy: str
    takeover_command: str = ""
    status_summary: str = ""


@dataclass(frozen=True, slots=True)
class ReviewBridgeState:
    overall_state: str
    codex_poll_state: str
    reviewer_freshness: str
    reviewer_mode: str
    last_codex_poll_utc: str
    last_codex_poll_age_seconds: int
    last_worktree_hash: str
    current_instruction: str
    open_findings: str
    claude_status: str
    claude_ack: str
    claude_ack_current: bool
    current_instruction_revision: str
    claude_ack_revision: str
    last_reviewed_scope: str
    reviewer_poll_state: str = ""
    last_reviewer_poll_utc: str = ""
    last_reviewer_poll_age_seconds: int = 0
    implementer_status: str = ""
    implementer_ack: str = ""
    implementer_ack_current: bool = False
    implementer_ack_revision: str = ""
    launch_truth: str = ""
    effective_reviewer_mode: str = ""
    implementer_state_hash: str = ""
    reviewed_hash_current: bool | None = None
    review_needed: bool | None = None
    review_accepted: bool = False
    """Compatibility projection over ``ReviewerRuntimeContract.review_acceptance``."""
    head_at_push_time: str = ""
    """HEAD SHA recorded at the last reviewer checkpoint or push."""
    implementer_completion_stall: bool = False
    publisher_running: bool = False
    codex_conductor_active: bool = False
    claude_conductor_active: bool = False
    reviewer_capability: ConductorCapabilityState | None = None
    implementer_capability: ConductorCapabilityState | None = None
    session_liveness_signals: tuple[dict[str, object], ...] = ()
    pending_total: int = 0
    declared_reviewer_mode: str = ""


@dataclass(frozen=True, slots=True)
class ReviewAttentionState:
    status: str
    owner: str
    summary: str
    recommended_action: str
    recommended_command: str


@dataclass(frozen=True, slots=True)
class RecoveryEvidenceState:
    code: str
    surface: str
    field: str
    value: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class RecoveryDiagnosisState:
    status: str
    root_cause: str
    supporting_causes: tuple[str, ...] = ()
    evidence: tuple[RecoveryEvidenceState, ...] = ()
    affected_surfaces: tuple[str, ...] = ()
    expected_healthy_state: str = ""


@dataclass(frozen=True, slots=True)
class RecoveryDecisionState:
    action_id: str
    command: str = ""
    execution_owner: str = ""
    rationale: str = ""
    blocked_alternatives: tuple[str, ...] = ()
    can_auto_fix: bool = False
    requires_approval: bool = False
    next_expected_state: str = ""


@dataclass(frozen=True, slots=True)
class RecoveryAssessmentState:
    diagnosis: RecoveryDiagnosisState
    decision: RecoveryDecisionState


@dataclass(frozen=True, slots=True)
class ReviewState:
    schema_version: int
    contract_id: str
    command: str
    action: str
    timestamp: str
    ok: bool
    review: ReviewSessionState
    queue: ReviewQueueState
    current_session: ReviewCurrentSessionState
    collaboration: CollaborationSessionState
    bridge: ReviewBridgeState
    attention: ReviewAttentionState | None
    packets: tuple[ReviewPacketState, ...]
    registry: AgentRegistryState
    packet_inbox: PacketInboxState = field(default_factory=PacketInboxState)
    review_candidate: ReviewCandidateRecord | None = None
    push_authorization: PushAuthorizationRecord | None = None
    recovery_assessment: RecoveryAssessmentState | None = None
    reviewer_runtime: ReviewerRuntimeContract = field(
        default_factory=ReviewerRuntimeContract
    )
    commit_pipeline: RemoteCommitPipelineContract = field(
        default_factory=RemoteCommitPipelineContract
    )
    coordination: CoordinationSnapshot | None = None
    authority_snapshot: AuthoritySnapshot | None = None
    round_proofs: tuple[RoundProofState, ...] = ()
    # Per Codex rev_pkt_2271 #3 + rev_pkt_2279 audit Track A: typed
    # ReviewState must round-trip the agent_sync (v1) and agent_work_board
    # (v1.1) projections so consumers parsing review_state.json through
    # ``review_state_from_payload`` retain them. Empty mapping sentinel
    # mirrors the convention used for other typed addenda above.
    agent_sync: dict[str, object] = field(default_factory=dict)
    agent_work_board: dict[str, object] = field(default_factory=dict)
    agent_loop_decisions: list[dict[str, object]] = field(default_factory=list)
    attention_windows: dict[str, object] = field(default_factory=dict)
    agent_dispatch_router: dict[str, object] = field(default_factory=dict)
    # Per Codex rev_pkt_2273/2278/2281/2298: 4-field topology/authority split
    # ('coordination_topology', 'authority_mode', 'recovery_eligibility',
    # 'observed_runtime') so consumers stop treating ``single_agent`` as
    # observed runtime when typed evidence shows multi-agent activity.
    coordination_state: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    source_identity: dict[str, str] = field(default_factory=dict)
    source_contract: str = ""
    source_command: str = ""
    observed_fields: tuple[str, ...] = ()
    inferred_fields: tuple[str, ...] = ()
    snapshot_id: str = ""
    zref: str = ""

    def pending_approvals(self) -> tuple[ReviewPacketState, ...]:
        from ..review_channel.pending_packets import live_pending_packets

        return tuple(
            packet
            for packet in live_pending_packets(self.packets)
            if _packet_requires_operator_approval(packet)
        )

    def lane_agents(self, lane_name: str) -> tuple[AgentRegistryEntryState, ...]:
        return tuple(
            agent
            for agent in self.registry.agents
            if agent.lane == lane_name or agent.provider == lane_name
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.authority_snapshot is not None:
            payload["authority_snapshot"] = self.authority_snapshot.to_dict()
        return payload
