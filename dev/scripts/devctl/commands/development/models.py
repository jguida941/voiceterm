"""Typed contracts for the read-only ``devctl develop`` controller."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DevelopmentLearningSnapshot:
    """Guard/probe learning evidence visible to the controller."""

    open_findings: int = 0
    promotion_candidates: int = 0
    queued_promotion_candidates: int = 0
    smartness_inputs: tuple[str, ...] = ()
    learning_state: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["smartness_inputs"] = list(self.smartness_inputs)
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentDiscoverySnapshot:
    """Static system-discovery counts used as coverage targets."""

    commands: int = 0
    guards: int = 0
    probes: int = 0
    surfaces: int = 0
    coverage_targets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["coverage_targets"] = list(self.coverage_targets)
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentLoopReport:
    """Read-only controller report for `/develop` and `devctl develop`."""

    action: str
    status: str
    ok: bool
    controller_state: str
    summary: str
    topology: dict[str, Any]
    next_slice: DevelopmentNextSlice
    learning: DevelopmentLearningSnapshot
    discovery: DevelopmentDiscoverySnapshot
    required_checks: tuple[str, ...]
    next_commands: tuple[str, ...]
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    contract_id: str = DEVELOPMENT_LOOP_CONTRACT_ID
    schema_version: int = DEVELOPMENT_LOOP_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "command": "develop",
            "action": self.action,
            "status": self.status,
            "ok": self.ok,
            "controller_state": self.controller_state,
            "summary": self.summary,
            "topology": dict(self.topology),
            "next_slice": self.next_slice.to_dict(),
            "learning": self.learning.to_dict(),
            "discovery": self.discovery.to_dict(),
            "required_checks": list(self.required_checks),
            "next_commands": list(self.next_commands),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "inputs": dict(self.inputs),
        }
