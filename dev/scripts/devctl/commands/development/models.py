"""Typed contracts for the read-only ``devctl develop`` controller."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

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
class DevelopmentPacketAttention:
    """Packet-driven wake state that can preempt ordinary slice selection."""

    attention_required: bool = False
    agent: str = "codex"
    attention_status: str = "none"
    wake_reason: str = ""
    latest_attention_packet_id: str = ""
    latest_finding_packet_id: str = ""
    pending_delivery_packet_ids: tuple[str, ...] = ()
    pending_actionable_packet_ids: tuple[str, ...] = ()
    expired_unresolved_count: int = 0
    required_command: str = ""
    durable_plan_row_id: str = ""
    summary: str = "No packet attention is blocking /develop."


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
    watcher_lease: DevelopmentWatcherLease
    continuation: DevelopmentContinuationRequiredSignal
    learning: DevelopmentLearningSnapshot
    discovery: DevelopmentDiscoverySnapshot
    required_checks: tuple[str, ...]
    next_commands: tuple[str, ...]
    next_step_command: str = ""
    lifecycle: DevelopmentLifecyclePlan | None = None
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
