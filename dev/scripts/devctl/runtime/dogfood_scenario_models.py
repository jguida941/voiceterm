"""Typed models for self-hosted dogfood scenarios."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

DOGFOOD_SCENARIO_REPORT_CONTRACT_ID = "DogfoodScenarioReport"
DOGFOOD_SCENARIO_REPORT_SCHEMA_VERSION = 1
PLAN41_TANDEM_SCENARIO_ID = "plan41-tandem"
DEVELOPMENT_LOOP_SCENARIO_ID = "development-loop"
VALID_DOGFOOD_SCENARIOS: tuple[str, ...] = (
    PLAN41_TANDEM_SCENARIO_ID,
    DEVELOPMENT_LOOP_SCENARIO_ID,
)
VALID_DOGFOOD_FIX_MODES: tuple[str, ...] = (
    "observe",
    "authorized",
    "isolated-worker",
    "conflict-drill",
)
DEFAULT_TESTER_CADENCE_SECONDS = 330


@dataclass(frozen=True, slots=True)
class DogfoodScenarioGate:
    """One typed gate for a dogfood scenario cycle."""

    gate_id: str
    status: str
    blocking: bool
    summary: str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class DogfoodScenarioLane:
    """One actor lane the scenario expects to keep active."""

    lane_id: str
    actor_id: str
    role: str
    provider: str
    mode: str
    cadence_seconds: int
    required_actions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_actions"] = list(self.required_actions)
        return payload


@dataclass(frozen=True, slots=True)
class DogfoodScenarioReport:
    """Read-only beta-loop readiness report over existing typed surfaces."""

    scenario_id: str
    generated_from: str
    fix_mode: str
    loop_requested: bool
    max_cycles: int
    cadence_seconds: int
    scenario_state: str
    dogfood_status: str
    summary: str
    gates: tuple[DogfoodScenarioGate, ...]
    lanes: tuple[DogfoodScenarioLane, ...]
    router: dict[str, Any]
    recommended_actions: tuple[str, ...]

    contract_id: str = DOGFOOD_SCENARIO_REPORT_CONTRACT_ID
    schema_version: int = DOGFOOD_SCENARIO_REPORT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "scenario_id": self.scenario_id,
            "generated_from": self.generated_from,
            "fix_mode": self.fix_mode,
            "loop_requested": self.loop_requested,
            "max_cycles": self.max_cycles,
            "cadence_seconds": self.cadence_seconds,
            "scenario_state": self.scenario_state,
            "dogfood_status": self.dogfood_status,
            "summary": self.summary,
            "gates": [gate.to_dict() for gate in self.gates],
            "lanes": [lane.to_dict() for lane in self.lanes],
            "router": dict(self.router),
            "recommended_actions": list(self.recommended_actions),
        }


__all__ = [
    "DEFAULT_TESTER_CADENCE_SECONDS",
    "DEVELOPMENT_LOOP_SCENARIO_ID",
    "DOGFOOD_SCENARIO_REPORT_CONTRACT_ID",
    "DOGFOOD_SCENARIO_REPORT_SCHEMA_VERSION",
    "PLAN41_TANDEM_SCENARIO_ID",
    "VALID_DOGFOOD_FIX_MODES",
    "VALID_DOGFOOD_SCENARIOS",
    "DogfoodScenarioGate",
    "DogfoodScenarioLane",
    "DogfoodScenarioReport",
]
