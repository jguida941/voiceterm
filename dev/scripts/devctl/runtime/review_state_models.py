"""Typed review-state models shared by review-channel frontends."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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
    open_findings: str = ""
    last_reviewed_scope: str = ""


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
    reviewed_hash_current: bool | None = None
    review_needed: bool | None = None
    review_accepted: bool = False
    """Reviewer-owned acceptance gate: True only when verdict shows
    accepted/all-green/resolved AND findings are clear/none.  Populated by
    the projection layer using the same semantics as
    ``bridge_validation.bridge_review_accepted()``."""
    implementer_completion_stall: bool = False
    publisher_running: bool = False


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
    bridge: ReviewBridgeState
    attention: ReviewAttentionState | None
    packets: tuple[ReviewPacketState, ...]
    registry: AgentRegistryState
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

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
