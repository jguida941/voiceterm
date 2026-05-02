"""Typed `/develop` topology and routing contracts.

The development controller is not a fixed team roster. It compiles a developer
request to typed routing:

``request -> graph/system discovery -> plan/finding slice -> authority route
-> workstream assignment -> evidence -> learning feedback``.

Provider names are compatibility labels only. Codex, Claude, future agents,
and humans can occupy any workstream when typed runtime authority grants the
matching capabilities for the current session.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

DEVELOPMENT_MODE_CONTRACT_ID = "DevelopmentModeTopology"
DEVELOPMENT_MODE_SCHEMA_VERSION = 1
DEVELOPMENT_TEAM_CONTRACT_ID = DEVELOPMENT_MODE_CONTRACT_ID


@dataclass(frozen=True, slots=True)
class DevelopmentAuthorityRequirement:
    """Typed proof required before an actor may occupy a workstream."""

    capabilities: tuple[str, ...] = ()
    lease_kind: str = "none"
    exclusive: bool = False
    approval_packet_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["capabilities"] = list(self.capabilities)
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentEvidenceContract:
    """Typed read/write/packet contract for one workstream."""

    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    emits_packets: tuple[str, ...] = ()
    visible_in: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("reads", "writes", "emits_packets", "visible_in"):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentRoutingContract:
    """How `/develop` decides where work goes."""

    route_sources: tuple[str, ...]
    selection_signals: tuple[str, ...]
    graph_views: tuple[str, ...] = ()
    dispatch_contracts: tuple[str, ...] = ()
    fail_closed_when: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "route_sources",
            "selection_signals",
            "graph_views",
            "dispatch_contracts",
            "fail_closed_when",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentLearningContract:
    """How issues become future prevention instead of chat memory."""

    issue_sources: tuple[str, ...]
    pattern_outputs: tuple[str, ...]
    prevention_outputs: tuple[str, ...]
    prompt_inputs: tuple[str, ...]
    success_metrics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "issue_sources",
            "pattern_outputs",
            "prevention_outputs",
            "prompt_inputs",
            "success_metrics",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentExternalResearchContract:
    """Boundaries for web/vendor/library research in development mode."""

    route_grant_required: bool
    allowed_sources: tuple[str, ...]
    required_evidence: tuple[str, ...]
    synthesis_inputs: tuple[str, ...]
    blocked_uses: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "allowed_sources",
            "required_evidence",
            "synthesis_inputs",
            "blocked_uses",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentKnowledgeFlowContract:
    """How durable knowledge artifacts feed graph, plan, and guard systems."""

    artifact_inputs: tuple[str, ...]
    canonical_sinks: tuple[str, ...]
    generated_projections: tuple[str, ...]
    pointer_surfaces: tuple[str, ...]
    graph_consumers: tuple[str, ...]
    promotion_gates: tuple[str, ...]
    forbidden_uses: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "artifact_inputs",
            "canonical_sinks",
            "generated_projections",
            "pointer_surfaces",
            "graph_consumers",
            "promotion_gates",
            "forbidden_uses",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentScaleModeSpec:
    """One named pressure-response mode for development fanout."""

    mode_id: str
    display_name: str
    workstreams: tuple[str, ...]
    purpose: str
    pressure_signals: tuple[str, ...]
    capacity_effect: str
    required_gates: tuple[str, ...] = ()
    evidence_outputs: tuple[str, ...] = ()
    blocked_when: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "workstreams",
            "pressure_signals",
            "required_gates",
            "evidence_outputs",
            "blocked_when",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentScalingContract:
    """How typed work pressure becomes bounded extra agents."""

    pressure_inputs: tuple[str, ...]
    route_outputs: tuple[str, ...]
    scale_out_when: tuple[str, ...]
    communication_rules: tuple[str, ...]
    safety_gates: tuple[str, ...]
    scale_in_when: tuple[str, ...]
    success_metrics: tuple[str, ...]
    modes: tuple[DevelopmentScaleModeSpec, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "pressure_inputs",
            "route_outputs",
            "scale_out_when",
            "communication_rules",
            "safety_gates",
            "scale_in_when",
            "success_metrics",
        ):
            payload[key] = list(payload[key])
        payload["modes"] = [item.to_dict() for item in self.modes]
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentWorkstreamSpec:
    """One user-facing job mapped to typed runtime authority and routing."""

    workstream_id: str
    display_name: str
    aliases: tuple[str, ...]
    runtime_role: str
    plain_language: str
    phases: tuple[str, ...]
    mutation_policy: str
    authority: DevelopmentAuthorityRequirement
    evidence: DevelopmentEvidenceContract
    routing: DevelopmentRoutingContract
    allowed_actions: tuple[str, ...] = ()
    blocked_actions: tuple[str, ...] = ()
    assignment_rule: str = "any_actor_with_matching_authority"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["aliases"] = list(self.aliases)
        payload["phases"] = list(self.phases)
        payload["authority"] = self.authority.to_dict()
        payload["evidence"] = self.evidence.to_dict()
        payload["routing"] = self.routing.to_dict()
        payload["allowed_actions"] = list(self.allowed_actions)
        payload["blocked_actions"] = list(self.blocked_actions)
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentModeTopology:
    """Provider-neutral `/develop` topology."""

    topology_id: str
    workstreams: tuple[DevelopmentWorkstreamSpec, ...]
    global_routing: DevelopmentRoutingContract
    learning_loop: DevelopmentLearningContract
    external_research: DevelopmentExternalResearchContract
    knowledge_flow: DevelopmentKnowledgeFlowContract
    scaling: DevelopmentScalingContract
    assignment_policy: str
    provider_policy: str
    mutation_policy: str
    default_worker_fanout: int = 0
    schema_version: int = DEVELOPMENT_MODE_SCHEMA_VERSION
    contract_id: str = DEVELOPMENT_MODE_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["global_routing"] = self.global_routing.to_dict()
        payload["learning_loop"] = self.learning_loop.to_dict()
        payload["external_research"] = self.external_research.to_dict()
        payload["knowledge_flow"] = self.knowledge_flow.to_dict()
        payload["scaling"] = self.scaling.to_dict()
        payload["workstreams"] = [item.to_dict() for item in self.workstreams]
        return payload


def build_default_development_topology() -> DevelopmentModeTopology:
    """Return the default topology for typed development mode."""
    from .development_topology_defaults import (
        build_default_development_topology as build_default,
    )

    return build_default()


def build_default_development_team() -> DevelopmentModeTopology:
    """Compatibility alias for older callers."""
    return build_default_development_topology()


__all__ = [
    "DEVELOPMENT_MODE_CONTRACT_ID",
    "DEVELOPMENT_MODE_SCHEMA_VERSION",
    "DEVELOPMENT_TEAM_CONTRACT_ID",
    "DevelopmentAuthorityRequirement",
    "DevelopmentEvidenceContract",
    "DevelopmentExternalResearchContract",
    "DevelopmentKnowledgeFlowContract",
    "DevelopmentLearningContract",
    "DevelopmentModeTopology",
    "DevelopmentRoutingContract",
    "DevelopmentScaleModeSpec",
    "DevelopmentScalingContract",
    "DevelopmentWorkstreamSpec",
    "build_default_development_team",
    "build_default_development_topology",
]
