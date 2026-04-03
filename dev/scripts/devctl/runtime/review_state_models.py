"""Typed review-state models shared by review-channel frontends."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .reviewer_runtime_models import (
    ReviewerAcceptanceState,
    ReviewerLastPollState,
    ReviewerRolloverState,
    ReviewerRuntimeContract,
    ReviewerSessionOwnerState,
)
from .remote_commit_pipeline_models import RemoteCommitPipelineContract


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
    prepared_at: str = ""
    metadata_path: str = ""
    log_path: str = ""
    launch_command: str = ""
    requested_worker_budget: int | None = None
    planned_lane_count: int = 0


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
    launch_truth: str = ""
    effective_reviewer_mode: str = ""
    implementer_state_hash: str = ""
    reviewed_hash_current: bool | None = None
    review_needed: bool | None = None
    review_accepted: bool = False
    """Compatibility projection over ``ReviewerRuntimeContract.review_acceptance``."""
    implementer_completion_stall: bool = False
    publisher_running: bool = False
    codex_conductor_active: bool = False
    claude_conductor_active: bool = False
    reviewer_capability: ConductorCapabilityState | None = None
    implementer_capability: ConductorCapabilityState | None = None


@dataclass(frozen=True, slots=True)
class ReviewAttentionState:
    status: str
    owner: str
    summary: str
    recommended_action: str
    recommended_command: str


@dataclass(frozen=True, slots=True)
class ContextPackRefState:
    pack_kind: str
    pack_ref: str
    adapter_profile: str = ""
    generated_at_utc: str = ""


@dataclass(frozen=True, slots=True)
class ReviewPacketState:
    packet_id: str
    kind: str
    from_agent: str
    to_agent: str
    summary: str
    body: str
    status: str
    policy_hint: str
    requested_action: str
    approval_required: bool
    posted_at: str
    evidence_refs: tuple[str, ...] = ()
    context_pack_refs: tuple[ContextPackRefState, ...] = ()
    trace_id: str = ""
    latest_event_id: str = ""
    confidence: float = 0.0
    guidance_refs: tuple[str, ...] = ()
    target_kind: str = ""
    target_ref: str = ""
    target_revision: str = ""
    anchor_refs: tuple[str, ...] = ()
    intake_ref: str = ""
    mutation_op: str = ""
    pipeline_generation: str = ""
    staged_snapshot_hash: str = ""
    guard_results_summary: str = ""
    acked_by: str = ""
    acked_at_utc: str = ""
    applied_at_utc: str = ""
    expires_at_utc: str = ""

    def requires_operator_approval(self) -> bool:
        return self.approval_required and self.status == "pending"


@dataclass(frozen=True, slots=True)
class AgentRegistryEntryState:
    agent_id: str
    provider: str
    display_name: str
    lane: str
    lane_title: str
    current_job: str
    job_state: str
    waiting_on: str
    last_packet_seen: str
    last_packet_applied: str
    script_profile: str
    mp_scope: str
    worktree: str
    branch: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class AgentRegistryState:
    timestamp: str
    agents: tuple[AgentRegistryEntryState, ...]


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
    reviewer_runtime: ReviewerRuntimeContract = field(
        default_factory=ReviewerRuntimeContract
    )
    commit_pipeline: RemoteCommitPipelineContract = field(
        default_factory=RemoteCommitPipelineContract
    )
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    snapshot_id: str = ""

    def pending_approvals(self) -> tuple[ReviewPacketState, ...]:
        return tuple(packet for packet in self.packets if packet.requires_operator_approval())

    def lane_agents(self, lane_name: str) -> tuple[AgentRegistryEntryState, ...]:
        return tuple(
            agent
            for agent in self.registry.agents
            if agent.lane == lane_name or agent.provider == lane_name
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
