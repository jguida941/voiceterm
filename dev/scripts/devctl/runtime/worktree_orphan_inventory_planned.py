"""Planned delegated-worker lane inventory sources."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple

from .value_coercion import coerce_mapping, coerce_mapping_items, coerce_string
from .worktree_orphan_inventory_git import branch_exists
from .worktree_orphan_snapshot import OrphanSource, OrphanSourceClassification


class PlannedLane(NamedTuple):
    actor: Mapping[str, object]
    actor_id: str
    worktree: str
    resolved_path: Path
    branch: str
    worktree_exists: bool
    branch_exists: bool
    realization_status: str


class PlannedLaneMetadata(NamedTuple):
    actor_id: str
    lane: str
    mp_scope: str
    presence: str
    status: str
    declared_worktree_path: str
    declared_branch: str
    worktree_exists: bool
    branch_exists: bool
    realization_status: str


def scan_planned_lanes(
    repo_root: Path,
    *,
    state: Mapping[str, object],
) -> tuple[OrphanSource, ...]:
    sources: list[OrphanSource] = []
    seen: set[str] = set()

    for actor in planned_actor_rows(state):
        lane = planned_lane_from_actor(repo_root, actor)
        if lane is None or planned_lane_seen(lane, seen):
            continue

        if lane.worktree_exists and lane.branch_exists:
            continue

        sources.append(planned_lane_source(lane))

    return tuple(sources)


def planned_actor_rows(state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    coordination = coerce_mapping(state.get("coordination"))
    collaboration = coerce_mapping(state.get("collaboration"))

    rows.extend(
        item
        for item in coerce_mapping_items(coordination.get("actors"))
        if coerce_string(item.get("presence")) == "planned"
    )
    rows.extend(
        item
        for item in coerce_mapping_items(collaboration.get("delegated_work"))
        if coerce_string(item.get("status")) == "planned"
    )
    rows.extend(
        item
        for item in coerce_mapping_items(state.get("delegated_work"))
        if coerce_string(item.get("status")) == "planned"
    )

    return tuple(rows)


def planned_lane_from_actor(
    repo_root: Path,
    actor: Mapping[str, object],
) -> PlannedLane | None:
    actor_id = coerce_string(actor.get("actor_id") or actor.get("agent_id"))
    worktree = coerce_string(actor.get("worktree"))
    if not actor_id or not worktree:
        return None

    resolved = resolve_declared_path(repo_root, worktree)
    branch = coerce_string(actor.get("branch"))
    worktree_exists = resolved.exists()
    branch_realized = branch_exists(repo_root, branch)

    return PlannedLane(
        actor=actor,
        actor_id=actor_id,
        worktree=worktree,
        resolved_path=resolved,
        branch=branch,
        worktree_exists=worktree_exists,
        branch_exists=branch_realized,
        realization_status=planned_lane_realization_status(
            worktree_exists=worktree_exists,
            branch_exists=branch_realized,
        ),
    )


def planned_lane_seen(lane: PlannedLane, seen: set[str]) -> bool:
    key = f"{lane.actor_id}:{lane.worktree}"
    if key in seen:
        return True

    seen.add(key)
    return False


def planned_lane_source(lane: PlannedLane) -> OrphanSource:
    return OrphanSource(
        source_id=f"source-planned-lane-{lane.actor_id}",
        source_kind="planned_delegated_worker_worktree",
        source_ref=f"planned-lane:{lane.actor_id}",
        path=str(lane.resolved_path),
        branch=lane.branch,
        status="unresolved",
        classification=planned_lane_classification(),
        evidence_refs=("review_state.coordination.actors",),
        metadata=planned_lane_metadata(lane)._asdict(),
    )


def planned_lane_classification() -> OrphanSourceClassification:
    return OrphanSourceClassification(
        state="planned_lane_orphan",
        load_bearing=False,
        governance_owner="coordination.actors",
        risk="phantom_worker_lane",
        notes=("planned actor has no realized checkout",),
    )


def planned_lane_metadata(lane: PlannedLane) -> PlannedLaneMetadata:
    return PlannedLaneMetadata(
        actor_id=lane.actor_id,
        lane=coerce_string(lane.actor.get("lane")),
        mp_scope=coerce_string(lane.actor.get("mp_scope")),
        presence=coerce_string(lane.actor.get("presence")),
        status=coerce_string(lane.actor.get("status")),
        declared_worktree_path=lane.worktree,
        declared_branch=lane.branch,
        worktree_exists=lane.worktree_exists,
        branch_exists=lane.branch_exists,
        realization_status=lane.realization_status,
    )


def resolve_declared_path(repo_root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve(strict=False)


def planned_lane_realization_status(
    *,
    worktree_exists: bool,
    branch_exists: bool,
) -> str:
    if not worktree_exists:
        return "worktree_missing"
    if not branch_exists:
        return "branch_missing"
    return "realized"


__all__ = ["scan_planned_lanes"]
