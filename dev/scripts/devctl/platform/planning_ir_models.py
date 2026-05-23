"""Typed planning-reducer contracts for scheduler-facing platform state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..runtime.work_intake_models import PlanTargetRef

PLANNING_IR_SCHEMA_VERSION = 1
PLANNING_IR_CONTRACT_ID = "PlanningIRSnapshot"


@dataclass(frozen=True, slots=True)
class PlanDependency:
    """One typed dependency edge between plan phases or tasks."""

    dependency_id: str
    dependency_kind: str = "task"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PlanTask:
    """One typed checklist task parsed from an execution-plan phase."""

    task_id: str
    summary: str
    owner_doc: str = ""
    status: str = "pending"
    phase_id: str = ""
    phase_title: str = ""
    dependencies: tuple[PlanDependency, ...] = ()
    anchor_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["dependencies"] = [
            dependency.to_dict() for dependency in self.dependencies
        ]
        return payload


@dataclass(frozen=True, slots=True)
class PlanPhase:
    """One typed execution-plan phase plus its bounded checklist tasks."""

    phase_id: str
    title: str
    owner_doc: str = ""
    status: str = "pending"
    dependencies: tuple[PlanDependency, ...] = ()
    tasks: tuple[PlanTask, ...] = ()
    summary: str = ""
    anchor_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["dependencies"] = [
            dependency.to_dict() for dependency in self.dependencies
        ]
        payload["tasks"] = [task.to_dict() for task in self.tasks]
        return payload


@dataclass(frozen=True, slots=True)
class NextBestSliceRecord:
    """One bounded plan/file cluster recommendation for the next edit slice."""

    slice_id: str
    plan_path: str
    plan_title: str
    plan_scope: str
    file_paths: tuple[str, ...] = ()
    target_id: str = ""
    hot_path_count: int = 0
    live_finding_count: int = 0
    prioritized_finding_rank: int = 0
    finding_severity_band: str = ""
    total_score: float = 0.0
    schedule_state: str = "ready"
    recommended_topology: str = "single_implementer_single_reviewer"
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["file_paths"] = list(self.file_paths)
        return payload


@dataclass(frozen=True, slots=True)
class ConcurrentWriterConflictRecord:
    """A typed blocking or cautionary concurrent-writer signal."""

    conflict_kind: str
    summary: str
    active_participants: tuple[str, ...] = ()
    conflicting_paths: tuple[str, ...] = ()
    duplicate_worktrees: tuple[str, ...] = ()
    recommended_topology: str = "single_implementer_single_reviewer"
    blocking: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["active_participants"] = list(self.active_participants)
        payload["conflicting_paths"] = list(self.conflicting_paths)
        payload["duplicate_worktrees"] = list(self.duplicate_worktrees)
        return payload


@dataclass(frozen=True, slots=True)
class UnownedHotPathRecord:
    """A hot file that lacks any typed plan ownership edge."""

    file_path: str
    temperature: float
    live_finding_count: int = 0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PlanFindingMismatchRecord:
    """A current finding whose ownership does not line up cleanly with plan state."""

    finding_id: str
    check_id: str
    file_path: str
    severity: str
    mismatch_kind: str
    owner_plan_paths: tuple[str, ...] = ()
    active_target_path: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["owner_plan_paths"] = list(self.owner_plan_paths)
        return payload


@dataclass(frozen=True, slots=True)
class PlanningIRSnapshot:
    """Canonical scheduler-facing planning reducer snapshot."""

    schema_version: int = PLANNING_IR_SCHEMA_VERSION
    contract_id: str = PLANNING_IR_CONTRACT_ID
    generated_at_utc: str = ""
    repo_name: str = ""
    repo_root: str = ""
    current_branch: str = ""
    head_commit_sha: str = ""
    graph_source: str = ""
    governance_report_path: str = ""
    active_target: PlanTargetRef | None = None
    ownership_status: str = ""
    collaboration_topology: str = ""
    authority_mode: str = ""
    work_ownership_mode: str = ""
    sync_cadence_mode: str = ""
    plan_count: int = 0
    scoped_edge_count: int = 0
    hot_path_count: int = 0
    live_finding_count: int = 0
    next_best_slices: tuple[NextBestSliceRecord, ...] = ()
    concurrent_writer_conflicts: tuple[ConcurrentWriterConflictRecord, ...] = ()
    unowned_hot_paths: tuple[UnownedHotPathRecord, ...] = ()
    plan_finding_mismatches: tuple[PlanFindingMismatchRecord, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.active_target is None:
            payload["active_target"] = None
        else:
            payload["active_target"] = self.active_target.to_dict()
        payload["next_best_slices"] = [
            item.to_dict() for item in self.next_best_slices
        ]
        payload["concurrent_writer_conflicts"] = [
            item.to_dict() for item in self.concurrent_writer_conflicts
        ]
        payload["unowned_hot_paths"] = [
            item.to_dict() for item in self.unowned_hot_paths
        ]
        payload["plan_finding_mismatches"] = [
            item.to_dict() for item in self.plan_finding_mismatches
        ]
        return payload


__all__ = [
    "ConcurrentWriterConflictRecord",
    "NextBestSliceRecord",
    "PLANNING_IR_CONTRACT_ID",
    "PLANNING_IR_SCHEMA_VERSION",
    "PlanDependency",
    "PlanFindingMismatchRecord",
    "PlanPhase",
    "PlanTask",
    "PlanningIRSnapshot",
    "UnownedHotPathRecord",
]
