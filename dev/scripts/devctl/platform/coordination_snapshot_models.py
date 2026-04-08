"""Typed contracts for the bounded coordination-posture reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..runtime.work_intake_models import PlanTargetRef

COORDINATION_SNAPSHOT_SCHEMA_VERSION = 1
COORDINATION_SNAPSHOT_CONTRACT_ID = "CoordinationSnapshot"


@dataclass(frozen=True, slots=True)
class CoordinationActorRecord:
    """One bounded actor or delegated-lane record in coordination posture."""

    actor_id: str
    provider: str
    role: str
    presence: str
    session_name: str = ""
    job_state: str = ""
    waiting_on: str = ""
    lane: str = ""
    mp_scope: str = ""
    worktree: str = ""
    branch: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CoordinationSnapshot:
    """Canonical bounded answer for live coordination/topology posture."""

    schema_version: int = COORDINATION_SNAPSHOT_SCHEMA_VERSION
    contract_id: str = COORDINATION_SNAPSHOT_CONTRACT_ID
    generated_at_utc: str = ""
    repo_name: str = ""
    repo_root: str = ""
    current_branch: str = ""
    head_commit_sha: str = ""
    active_target: PlanTargetRef | None = None
    current_slice: str = ""
    scope_paths: tuple[str, ...] = ()
    ownership_status: str = ""
    authority_mode: str = ""
    work_ownership_mode: str = ""
    sync_cadence_mode: str = ""
    declared_topology: str = "single_agent"
    observed_topology: str = "single_agent"
    recommended_topology: str = "single_agent"
    fanout_posture: str = "single_agent_only"
    safe_to_fanout: bool = False
    worktree_strategy: str = "shared_primary_worktree"
    resync_required: bool = False
    resync_reasons: tuple[str, ...] = ()
    observed_active_participant_count: int = 0
    declared_participant_count: int = 0
    planned_delegated_worker_count: int = 0
    live_delegated_worker_count: int = 0
    active_participants: tuple[str, ...] = ()
    duplicate_worktrees: tuple[str, ...] = ()
    conflict_summaries: tuple[str, ...] = ()
    actors: tuple[CoordinationActorRecord, ...] = ()
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["scope_paths"] = list(self.scope_paths)
        payload["resync_reasons"] = list(self.resync_reasons)
        payload["active_participants"] = list(self.active_participants)
        payload["duplicate_worktrees"] = list(self.duplicate_worktrees)
        payload["conflict_summaries"] = list(self.conflict_summaries)
        payload["actors"] = [item.to_dict() for item in self.actors]
        if self.active_target is None:
            payload["active_target"] = None
        else:
            payload["active_target"] = self.active_target.to_dict()
        return payload


__all__ = [
    "COORDINATION_SNAPSHOT_CONTRACT_ID",
    "COORDINATION_SNAPSHOT_SCHEMA_VERSION",
    "CoordinationActorRecord",
    "CoordinationSnapshot",
]
