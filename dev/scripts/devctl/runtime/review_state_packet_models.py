"""Packet, inbox, candidate, and registry helpers for ReviewState."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AgentAttentionRecord:
    agent: str
    current_instruction_packet_id: str = ""
    latest_finding_packet_id: str = ""
    pending_actionable_packet_ids: tuple[str, ...] = ()
    expired_unresolved_packet_ids: tuple[str, ...] = ()
    attention_status: str = "none"
    wake_reason: str = ""
    required_command: str = ""
    attention_revision: str = ""
    delivery_state: str = "idle"


def agent_attention_record_from_mapping(value: object) -> AgentAttentionRecord | None:
    if not isinstance(value, Mapping):
        return None
    agent = str(value.get("agent") or "").strip()
    if not agent:
        return None
    return AgentAttentionRecord(
        agent=agent,
        current_instruction_packet_id=str(
            value.get("current_instruction_packet_id") or ""
        ).strip(),
        latest_finding_packet_id=str(
            value.get("latest_finding_packet_id") or ""
        ).strip(),
        pending_actionable_packet_ids=tuple(
            str(item).strip()
            for item in value.get("pending_actionable_packet_ids", ())
            if str(item).strip()
        ),
        expired_unresolved_packet_ids=tuple(
            str(item).strip()
            for item in value.get("expired_unresolved_packet_ids", ())
            if str(item).strip()
        ),
        attention_status=str(value.get("attention_status") or "none").strip() or "none",
        wake_reason=str(value.get("wake_reason") or "").strip(),
        required_command=str(value.get("required_command") or "").strip(),
        attention_revision=str(value.get("attention_revision") or "").strip(),
        delivery_state=str(value.get("delivery_state") or "idle").strip() or "idle",
    )


@dataclass(frozen=True, slots=True)
class PacketInboxState:
    attention_revision: str = ""
    agents: tuple[AgentAttentionRecord, ...] = ()

    def for_agent(self, agent: str) -> AgentAttentionRecord | None:
        normalized = str(agent or "").strip().lower()
        for record in self.agents:
            if record.agent == normalized:
                return record
        return None


def packet_inbox_from_mapping(value: object) -> PacketInboxState | None:
    if not isinstance(value, Mapping):
        return None
    records = tuple(
        record
        for record in (
            agent_attention_record_from_mapping(item)
            for item in value.get("agents", ())
        )
        if record is not None
    )
    if not records and not str(value.get("attention_revision") or "").strip():
        return None
    return PacketInboxState(
        attention_revision=str(value.get("attention_revision") or "").strip(),
        agents=records,
    )


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
    plan_id: str = ""
    evidence_refs: tuple[str, ...] = ()
    context_pack_refs: tuple[ContextPackRefState, ...] = ()
    trace_id: str = ""
    latest_event_id: str = ""
    confidence: float = 0.0
    guidance_refs: tuple[str, ...] = ()
    target_kind: str = ""
    target_ref: str = ""
    target_revision: str = ""
    target_role: str = ""
    target_session_id: str = ""
    requested_session_visibility: str = ""
    anchor_refs: tuple[str, ...] = ()
    intake_ref: str = ""
    mutation_op: str = ""
    pipeline_generation: str = ""
    staged_snapshot_hash: str = ""
    guard_results_summary: str = ""
    full_guard_bundle_evidence: str = ""
    acked_by: str = ""
    acked_at_utc: str = ""
    applied_at_utc: str = ""
    delivery_emitted_at_utc: str = ""
    delivery_observed_at_utc: str = ""
    delivery_observed_by: str = ""
    execution_started_at_utc: str = ""
    execution_started_by: str = ""
    execution_failed_at_utc: str = ""
    execution_failed_by: str = ""
    execution_failed_reason: str = ""
    apply_pending_after_execution_at_utc: str = ""
    apply_pending_after_execution_by: str = ""
    apply_pending_after_execution_reason: str = ""
    expires_at_utc: str = ""
    semantic_zref: str = ""
    source_identity: dict[str, str] = field(default_factory=dict)
    acknowledged_events: tuple[dict[str, object], ...] = ()
    acted_on_events: tuple[dict[str, object], ...] = ()
    lifecycle_current_state: str = ""
    resolution_anchor: str = ""
    disposition: dict[str, object] = field(default_factory=dict)
    lifecycle_history: dict[str, object] = field(default_factory=dict)

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
    snapshot_id: str = ""
    zref: str = ""
    source_identity: dict[str, str] = field(default_factory=dict)
    source_contract: str = ""
    source_command: str = ""
    observed_fields: tuple[str, ...] = ()
    inferred_fields: tuple[str, ...] = ()


def packet_requires_operator_approval(packet: object) -> bool:
    if isinstance(packet, ReviewPacketState):
        return packet.requires_operator_approval()
    if isinstance(packet, dict):
        return bool(packet.get("approval_required")) and packet.get("status") == "pending"
    return False
