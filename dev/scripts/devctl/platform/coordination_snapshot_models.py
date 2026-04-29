"""Typed contracts for the bounded coordination-posture reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..runtime.work_intake_models import PlanTargetRef
from ..runtime.surface_provenance import (
    attach_surface_provenance,
    surface_provenance_kwargs,
)

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
    occupied_lane: str = ""
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
    snapshot_id: str = ""
    zref: str = ""
    source_identity: dict[str, str] | None = None
    source_contract: str = ""
    source_command: str = ""
    observed_fields: tuple[str, ...] = ()
    inferred_fields: tuple[str, ...] = ()
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
        return attach_surface_provenance(payload)


def coordination_actor_from_mapping(value: object) -> CoordinationActorRecord | None:
    """Deserialize one bounded actor row from a JSON-like mapping."""
    if not isinstance(value, dict):
        return None
    actor_id = str(value.get("actor_id") or "").strip()
    provider = str(value.get("provider") or "").strip()
    role = str(value.get("role") or "").strip()
    presence = str(value.get("presence") or "").strip()
    if not actor_id or not provider or not role or not presence:
        return None
    return CoordinationActorRecord(
        actor_id=actor_id,
        provider=provider,
        role=role,
        presence=presence,
        session_name=str(value.get("session_name") or "").strip(),
        job_state=str(value.get("job_state") or "").strip(),
        waiting_on=str(value.get("waiting_on") or "").strip(),
        occupied_lane=str(
            value.get("occupied_lane") or value.get("lane") or ""
        ).strip(),
        lane=str(value.get("lane") or "").strip(),
        mp_scope=str(value.get("mp_scope") or "").strip(),
        worktree=str(value.get("worktree") or "").strip(),
        branch=str(value.get("branch") or "").strip(),
        summary=str(value.get("summary") or "").strip(),
    )


def coordination_snapshot_from_mapping(value: object) -> CoordinationSnapshot | None:
    """Deserialize one coordination snapshot from a JSON-like mapping."""
    if not isinstance(value, dict):
        return None
    contract_id = str(value.get("contract_id") or "").strip()
    if contract_id and contract_id != COORDINATION_SNAPSHOT_CONTRACT_ID:
        return None
    target_mapping = value.get("active_target")
    active_target = (
        PlanTargetRef(
            target_id=str(target_mapping.get("target_id") or "").strip(),
            plan_path=str(target_mapping.get("plan_path") or "").strip(),
            plan_title=str(target_mapping.get("plan_title") or "").strip(),
            plan_scope=str(target_mapping.get("plan_scope") or "").strip(),
            target_kind=str(target_mapping.get("target_kind") or "").strip(),
            anchor_ref=str(target_mapping.get("anchor_ref") or "").strip(),
            expected_revision=str(target_mapping.get("expected_revision") or "").strip(),
        )
        if isinstance(target_mapping, dict)
        else None
    )
    actors_raw = value.get("actors", ())
    actors: list[CoordinationActorRecord] = []
    if isinstance(actors_raw, (list, tuple)):
        for row in actors_raw:
            actor = coordination_actor_from_mapping(row)
            if actor is not None:
                actors.append(actor)
    return CoordinationSnapshot(
        schema_version=int(value.get("schema_version") or COORDINATION_SNAPSHOT_SCHEMA_VERSION),
        contract_id=contract_id or COORDINATION_SNAPSHOT_CONTRACT_ID,
        **surface_provenance_kwargs(value),
        generated_at_utc=str(value.get("generated_at_utc") or "").strip(),
        repo_name=str(value.get("repo_name") or "").strip(),
        repo_root=str(value.get("repo_root") or "").strip(),
        current_branch=str(value.get("current_branch") or "").strip(),
        head_commit_sha=str(value.get("head_commit_sha") or "").strip(),
        active_target=active_target,
        current_slice=str(value.get("current_slice") or "").strip(),
        scope_paths=tuple(
            str(item).strip()
            for item in value.get("scope_paths", ())
            if str(item).strip()
        ),
        ownership_status=str(value.get("ownership_status") or "").strip(),
        authority_mode=str(value.get("authority_mode") or "").strip(),
        work_ownership_mode=str(value.get("work_ownership_mode") or "").strip(),
        sync_cadence_mode=str(value.get("sync_cadence_mode") or "").strip(),
        declared_topology=str(value.get("declared_topology") or "single_agent").strip(),
        observed_topology=str(value.get("observed_topology") or "single_agent").strip(),
        recommended_topology=str(
            value.get("recommended_topology") or "single_agent"
        ).strip(),
        fanout_posture=str(value.get("fanout_posture") or "single_agent_only").strip(),
        safe_to_fanout=bool(value.get("safe_to_fanout", False)),
        worktree_strategy=str(
            value.get("worktree_strategy") or "shared_primary_worktree"
        ).strip(),
        resync_required=bool(value.get("resync_required", False)),
        resync_reasons=tuple(
            str(item).strip()
            for item in value.get("resync_reasons", ())
            if str(item).strip()
        ),
        observed_active_participant_count=int(
            value.get("observed_active_participant_count") or 0
        ),
        declared_participant_count=int(value.get("declared_participant_count") or 0),
        planned_delegated_worker_count=int(
            value.get("planned_delegated_worker_count") or 0
        ),
        live_delegated_worker_count=int(value.get("live_delegated_worker_count") or 0),
        active_participants=tuple(
            str(item).strip()
            for item in value.get("active_participants", ())
            if str(item).strip()
        ),
        duplicate_worktrees=tuple(
            str(item).strip()
            for item in value.get("duplicate_worktrees", ())
            if str(item).strip()
        ),
        conflict_summaries=tuple(
            str(item).strip()
            for item in value.get("conflict_summaries", ())
            if str(item).strip()
        ),
        actors=tuple(actors),
        summary=str(value.get("summary") or "").strip(),
    )
__all__ = [
    "COORDINATION_SNAPSHOT_CONTRACT_ID",
    "COORDINATION_SNAPSHOT_SCHEMA_VERSION",
    "CoordinationActorRecord",
    "CoordinationSnapshot",
    "coordination_actor_from_mapping",
    "coordination_snapshot_from_mapping",
]
