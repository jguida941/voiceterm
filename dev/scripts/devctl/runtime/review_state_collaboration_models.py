"""Typed collaboration-session dataclasses for the review-state contract."""

from __future__ import annotations

from dataclasses import dataclass, field

from .work_intake_models import WorkIntakeOwnershipState


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
