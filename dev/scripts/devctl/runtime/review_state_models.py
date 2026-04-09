"""Typed review-state models shared by review-channel frontends."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from ..platform.coordination_snapshot_models import CoordinationSnapshot
from .reviewer_runtime_models import (
    ReviewerAcceptanceState,
    ReviewerLastPollState,
    ReviewerRolloverState,
    ReviewerRuntimeContract,
    ReviewerSessionOwnerState,
)
from .remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
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
class ReviewCandidateRecord:
    candidate_id: str
    instruction_revision: str
    artifact_kind: str
    base_sha: str
    head_sha: str
    worktree_hash: str
    changed_paths: tuple[str, ...] = ()
    tests_run: tuple[str, ...] = ()
    guards_run: tuple[str, ...] = ()
    implementer_status_written: bool = False
    ready_for_review: bool = False
    valid: bool = False
    invalidation_reason: str = ""
    implementer_state_hash: str = ""
    emitted_at_utc: str = ""
    scope_paths: tuple[str, ...] = ()
    missing_scope_paths: tuple[str, ...] = ()


def review_candidate_from_mapping(value: object) -> ReviewCandidateRecord | None:
    """Deserialize one ReviewCandidateRecord from a JSON-like mapping."""
    if not isinstance(value, Mapping):
        return None
    candidate_id = str(value.get("candidate_id") or "").strip()
    if not candidate_id:
        return None
    return ReviewCandidateRecord(
        candidate_id=candidate_id,
        instruction_revision=str(value.get("instruction_revision") or "").strip(),
        artifact_kind=str(value.get("artifact_kind") or "").strip(),
        base_sha=str(value.get("base_sha") or "").strip(),
        head_sha=str(value.get("head_sha") or "").strip(),
        worktree_hash=str(value.get("worktree_hash") or "").strip(),
        changed_paths=tuple(
            str(item).strip()
            for item in value.get("changed_paths", ())
            if str(item).strip()
        ),
        tests_run=tuple(
            str(item).strip()
            for item in value.get("tests_run", ())
            if str(item).strip()
        ),
        guards_run=tuple(
            str(item).strip()
            for item in value.get("guards_run", ())
            if str(item).strip()
        ),
        implementer_status_written=bool(
            value.get("implementer_status_written", False)
        ),
        ready_for_review=bool(value.get("ready_for_review", False)),
        valid=bool(value.get("valid", False)),
        invalidation_reason=str(value.get("invalidation_reason") or "").strip(),
        implementer_state_hash=str(value.get("implementer_state_hash") or "").strip(),
        emitted_at_utc=str(value.get("emitted_at_utc") or "").strip(),
        scope_paths=tuple(
            str(item).strip()
            for item in value.get("scope_paths", ())
            if str(item).strip()
        ),
        missing_scope_paths=tuple(
            str(item).strip()
            for item in value.get("missing_scope_paths", ())
            if str(item).strip()
        ),
    )


from .review_state_collaboration_models import (  # noqa: E402,F401
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


def _packet_requires_operator_approval(packet: object) -> bool:
    """Defensive check that matches `ReviewPacketState.requires_operator_approval`
    when ``packet`` is a typed model, and mirrors the same logic when a
    deserializer upstream left the packet as a raw dict. The typed path is the
    intended shape; the dict branch is a load-bearing safety net that keeps
    status/doctor/dashboard operator surfaces projecting even when packet
    hydration drops typing on the way through.
    """
    if isinstance(packet, ReviewPacketState):
        return packet.requires_operator_approval()
    if isinstance(packet, dict):
        return bool(packet.get("approval_required")) and packet.get("status") == "pending"
    return False


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
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    snapshot_id: str = ""

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
        return asdict(self)
