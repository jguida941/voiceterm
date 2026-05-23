"""Typed models for the coordination/topology reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

COORDINATION_TOPOLOGY_SCHEMA_VERSION = 1
COORDINATION_TOPOLOGY_CONTRACT_ID = "CoordinationTopologySnapshot"


@dataclass(frozen=True, slots=True)
class CoordinationParticipantRecord:
    """One bounded participant row in the live coordination answer."""

    agent_id: str
    provider: str
    role: str
    session_name: str = ""
    live: bool = False
    live_source: str = ""
    status: str = ""
    requested_worker_budget: int = 0
    planned_lane_count: int = 0
    session_state: str = ""
    session_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DelegatedWorktreeRecord:
    """One delegated worker/worktree row in the coordination answer."""

    receipt_id: str
    agent_id: str
    provider: str
    role: str
    owner_session: str
    lane: str = ""
    worktree: str = ""
    branch: str = ""
    live: bool = False
    status: str = ""
    duplicate_worktree: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CoordinationReadyGateRecord:
    """One bounded ready-gate row projected into the coordination answer."""

    gate_id: str
    status: str
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CoordinationTopologySnapshot:
    """One bounded answer for coordination, ownership, and fanout posture."""

    schema_version: int = COORDINATION_TOPOLOGY_SCHEMA_VERSION
    contract_id: str = COORDINATION_TOPOLOGY_CONTRACT_ID
    collaboration_topology: str = "typed_role_topology_unresolved"
    authority_mode: str = "self_directed"
    work_ownership_mode: str = "exclusive_slice"
    sync_cadence_mode: str = "continuous"
    interaction_mode: str = "unresolved"
    ownership_status: str = "clear"
    reviewer_mode: str = ""
    effective_reviewer_mode: str = ""
    reviewer_freshness: str = "unknown"
    attention_status: str = "inactive"
    active_participant_count: int = 0
    active_conductor_count: int = 0
    planned_lane_count: int = 0
    requested_worker_budget_total: int = 0
    live_delegated_worker_count: int = 0
    fanout_posture: str = "conductor_only"
    fanout_safe: bool = False
    recommended_topology: str = "typed_role_topology_unresolved"
    resync_posture: str = "idle"
    resync_required: bool = False
    resync_reason: str = ""
    resync_command: str = ""
    scope_paths: tuple[str, ...] = ()
    conflicting_paths: tuple[str, ...] = ()
    duplicate_delegated_worktrees: tuple[str, ...] = ()
    active_participants: tuple[CoordinationParticipantRecord, ...] = ()
    delegated_worktrees: tuple[DelegatedWorktreeRecord, ...] = ()
    ready_gates: tuple[CoordinationReadyGateRecord, ...] = ()
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["scope_paths"] = list(self.scope_paths)
        payload["conflicting_paths"] = list(self.conflicting_paths)
        payload["duplicate_delegated_worktrees"] = list(
            self.duplicate_delegated_worktrees
        )
        payload["active_participants"] = [
            row.to_dict() for row in self.active_participants
        ]
        payload["delegated_worktrees"] = [
            row.to_dict() for row in self.delegated_worktrees
        ]
        payload["ready_gates"] = [row.to_dict() for row in self.ready_gates]
        return payload
