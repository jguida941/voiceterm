"""Typed contracts for the read-only ``devctl develop`` controller."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from ...runtime.development_collaboration_modes import (
    CollaborationModeTopology,
    DevelopRolePresetSpec,
)
from ...runtime.development_packet_pressure_models import (
    PacketAttentionIngestionDecision,
    PacketBacklogPressure,
    PacketIngestDecision,
    PacketIntentClassification,
)
from dev.scripts.devctl.runtime.development_team import DevelopmentScalingContract
from .collaboration_models import (
    DevelopmentPeerMindEvent,
    DevelopmentPeerMindSnapshot,
    DevelopmentRuntimeRow,
    DevelopmentRuntimeSnapshot,
    DevelopmentSessionDiscoveryRow,
)
from .orchestration_models import (
    DevelopmentAgentLoopInput,
    DevelopmentContinuationRequiredSignal,
    DevelopmentOrchestrationSignal,
    DevelopmentOrchestrationSnapshot,
    DevelopmentWatcherLease,
)

DEVELOPMENT_LOOP_CONTRACT_ID = "DevelopmentLoopReport"
DEVELOPMENT_LOOP_SCHEMA_VERSION = 1
CollaborationModePayload = CollaborationModeTopology | Mapping[str, object]
CollaborationRolePresetPayload = DevelopRolePresetSpec | Mapping[str, object]
PacketPressurePayload = PacketBacklogPressure | Mapping[str, object]
PacketClassificationPayload = PacketIntentClassification | Mapping[str, object]
PacketIngestionDecisionPayload = PacketAttentionIngestionDecision | Mapping[str, object]
PacketIngestDecisionPayload = PacketIngestDecision | Mapping[str, object]


@dataclass(frozen=True, slots=True)
class DevelopmentNextSlice:
    """One deterministic next development slice selected from typed inputs."""

    slice_id: str = ""
    source: str = ""
    title: str = ""
    target_ref: str = ""
    status: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class DevelopmentLearningSnapshot:
    """Guard/probe learning evidence visible to the controller."""

    open_findings: int = 0
    promotion_candidates: int = 0
    queued_promotion_candidates: int = 0
    smartness_inputs: tuple[str, ...] = ()
    learning_state: str = "unknown"


@dataclass(frozen=True, slots=True)
class DevelopmentDiscoverySnapshot:
    """Static system-discovery counts used as coverage targets."""

    commands: int = 0
    guards: int = 0
    probes: int = 0
    surfaces: int = 0
    coverage_targets: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DevelopmentGroundTruthProbe:
    """One probe result in a design-preflight pass."""

    probe_id: str
    status: str
    summary: str
    evidence_ref: str = ""
    observed_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DevelopmentDesignPreflight:
    """Ground-truth-first architecture/design preflight report."""

    topic: str
    routing_decision: str
    summary: str
    required_probe_ids: tuple[str, ...]
    observed_probe_ids: tuple[str, ...]
    trigger_paths: tuple[str, ...]
    trigger_paths_digest: str
    receipt_verdict: str
    receipt_path: str = ""
    runtime_truth: Mapping[str, object] | None = None
    probes: tuple[DevelopmentGroundTruthProbe, ...] = ()
    next_commands: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DevelopmentPacketAttention:
    """Packet-driven wake state that can preempt ordinary slice selection."""

    attention_required: bool = False
    agent: str = "codex"
    attention_status: str = "none"
    attention_reason: str = ""
    wake_reason: str = ""
    latest_attention_packet_id: str = ""
    latest_finding_packet_id: str = ""
    pending_delivery_packet_ids: tuple[str, ...] = ()
    pending_actionable_packet_ids: tuple[str, ...] = ()
    expired_unresolved_count: int = 0
    required_command: str = ""
    durable_plan_row_id: str = ""
    packet_kind: str = ""
    requested_action: str = ""
    authority_affecting: bool = False
    summary: str = (
        "no pending attention; proceed with current slice or /develop "
        "dispatch-agent for next work"
    )


@dataclass(frozen=True, slots=True)
class DevelopmentWorkstreamSummary:
    """Compact workstream row embedded in controller output."""

    workstream_id: str
    display_name: str
    mutation_policy: str
    runtime_role: str


@dataclass(frozen=True, slots=True)
class DevelopmentScalingSummary:
    """Compact scaling summary embedded in controller output."""

    pressure_inputs: tuple[str, ...]
    route_outputs: tuple[str, ...]
    mode_ids: tuple[str, ...]
    mode_names: tuple[str, ...]
    safety_gates: tuple[str, ...]
    success_metrics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DevelopmentTopologySummary:
    """Compact topology view embedded in controller output."""

    contract_id: str
    schema_version: int
    topology_id: str
    workstreams: tuple[DevelopmentWorkstreamSummary, ...]
    assignment_policy: str
    provider_policy: str
    mutation_policy: str
    default_worker_fanout: int
    scaling: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DevelopmentControllerInputs:
    """Controller input summary used for explain-back."""

    master_plan_store: str
    plan_rows: int
    actor: str
    fleet: str
    max_cycles: int
    max_workers: int
    dry_run: bool
    requested_actor: str = ""
    actor_source: str = ""
    drain_packets: bool = False


@dataclass(frozen=True, slots=True)
class DevelopmentLifecycleStep:
    """One preview step for a `/develop` lifecycle action."""

    step_id: str
    purpose: str
    state: str
    command: str = ""
    authority: str = ""


@dataclass(frozen=True, slots=True)
class DevelopmentLifecyclePlan:
    """Lifecycle preview for developing through `/develop` itself."""

    action: str
    actor: str
    slice_id: str
    packet_id: str
    state: str
    summary: str
    steps: tuple[DevelopmentLifecycleStep, ...] = ()


@dataclass(frozen=True, slots=True)
class DevelopmentCampaignRoleState:
    """One actor lane in the remote-control pair campaign."""

    actor_id: str
    role: str
    session_id: str
    status: str
    mutation_mode: str
    active_packet_id: str = ""
    may_mutate: bool = False
    required_action: str = ""
    user_action: str = ""
    continuation_goal: str = ""
    proof_state: str = ""
    blocker: str = ""
    next_command: str = ""


@dataclass(frozen=True, slots=True)
class DevelopmentCampaignReport:
    """Read-only remote-control campaign state for Codex/Claude dogfood."""

    plan_row_id: str
    mode_id: str
    status: str
    current_phase: str
    summary: str
    remote_control_provider: str = ""
    remote_control_status: str = ""
    remote_control_active: bool = False
    remote_control_identity_bound: bool = False
    remote_control_session_id: str = ""
    remote_control_age_seconds: int = -1
    physical_remote_control_confirmed: bool = False
    coordination_topology: str = ""
    legacy_reviewer_mode: str = ""
    effective_reviewer_mode: str = ""
    operator_interaction_mode: str = ""
    mode_drift: bool = False
    fail_closed: bool = True
    mutation_allowed: bool = False
    publication_allowed: bool = False
    folded_plan_row_ids: tuple[str, ...] = ()
    governed_exception_store_path: str = ""
    governed_exception_pending_count: int = 0
    governed_exception_error_count: int = 0
    governed_exception_status: str = "unknown"
    bypass_posture: str = "unknown"
    bypass_publication_transport_retired: bool = False
    latest_push_report_path: str = ""
    latest_push_report_status: str = ""
    latest_push_report_head_commit: str = ""
    latest_push_report_published_remote: bool = False
    latest_push_report_post_push_green: bool = False
    latest_push_report_matches_current_head: bool = False
    publication_proof_summary: str = ""
    pending_packet_id: str = ""
    pending_packet_required_command: str = ""
    codex_next_command: str = ""
    claude_next_command: str = ""
    roles: tuple[DevelopmentCampaignRoleState, ...] = ()
    proof_requirements: tuple[str, ...] = ()
    contract_id: str = "RemoteControlCollaborationCampaign"
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class DevelopmentLoopReport:
    """Read-only controller report for `/develop` and `devctl develop`."""

    action: str
    status: str
    ok: bool
    controller_state: str
    summary: str
    topology: DevelopmentTopologySummary
    next_slice: DevelopmentNextSlice
    packet_attention: DevelopmentPacketAttention
    runtime: DevelopmentRuntimeSnapshot
    peer_minds: tuple[DevelopmentPeerMindSnapshot, ...]
    orchestration: DevelopmentOrchestrationSnapshot
    collaboration_mode: CollaborationModePayload
    packet_pressure: PacketPressurePayload
    selected_packet_classifications: tuple[PacketClassificationPayload, ...]
    packet_ingestion_decision: PacketIngestionDecisionPayload
    packet_ingest_decisions: tuple[PacketIngestDecisionPayload, ...]
    watcher_lease: DevelopmentWatcherLease
    continuation: DevelopmentContinuationRequiredSignal
    final_response_gate: Any
    reviewer_response_shape: Any
    learning: DevelopmentLearningSnapshot
    discovery: DevelopmentDiscoverySnapshot
    required_checks: tuple[str, ...]
    next_commands: tuple[str, ...]
    next_step_command: str = ""
    lifecycle: DevelopmentLifecyclePlan | None = None
    campaign: DevelopmentCampaignReport | None = None
    design_preflight: DevelopmentDesignPreflight | None = None
    packet_debt_remediation: dict[str, Any] | None = None
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    inputs: DevelopmentControllerInputs | None = None
    contract_id: str = DEVELOPMENT_LOOP_CONTRACT_ID
    schema_version: int = DEVELOPMENT_LOOP_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        payload["command"] = "develop"
        return payload


def scaling_summary_from_contract(
    scaling: DevelopmentScalingContract,
) -> dict[str, Any]:
    """Return the compact scaling view embedded in develop reports."""
    summary = DevelopmentScalingSummary(
        pressure_inputs=scaling.pressure_inputs,
        route_outputs=scaling.route_outputs,
        mode_ids=tuple(item.mode_id for item in scaling.modes),
        mode_names=tuple(item.display_name for item in scaling.modes),
        safety_gates=scaling.safety_gates,
        success_metrics=scaling.success_metrics,
    )
    return _json_ready(asdict(summary))


def _json_ready(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value
