"""Commit-pipeline helpers for review-state projection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from collections.abc import Mapping
from pathlib import Path

from ..runtime.surface_snapshot import build_surface_snapshot_id, build_surface_zref
from .remote_commit_pipeline_artifact import load_remote_commit_pipeline_contract
from .reviewer_runtime_contract import build_reviewer_doctor_surface


@dataclass(frozen=True)
class CommitProjectionInputs:
    """Grouped inputs for commit-pipeline surface projection."""

    output_root: Path
    reviewer_runtime: object
    collaboration: object
    recovery_assessment: object
    attention: Mapping[str, object]
    push_decision: Mapping[str, object] | None
    bridge_liveness: Mapping[str, object]
    reduced_runtime: dict[str, object] | None = None


@dataclass(frozen=True)
class CommitProjectionBundle:
    """Derived commit-pipeline surfaces used by review-state projection."""

    commit_pipeline: object
    snapshot_id: str
    zref: str
    doctor: dict[str, object]


def build_commit_projection_bundle(
    inputs: CommitProjectionInputs,
) -> CommitProjectionBundle:
    commit_pipeline = load_remote_commit_pipeline_contract(output_root=inputs.output_root)
    snapshot_id = build_surface_snapshot_id(
        reviewer_runtime=inputs.reviewer_runtime,
        commit_pipeline=commit_pipeline,
        push_decision=inputs.push_decision,
    )
    head_sha = str(
        (inputs.bridge_liveness.get("push_enforcement") or {}).get("current_head_commit")
        or commit_pipeline.commit_sha
        or ""
    ).strip()
    zref = build_surface_zref(snapshot_id=snapshot_id, head_sha=head_sha)
    commit_pipeline = replace(commit_pipeline, snapshot_id=snapshot_id, zref=zref)
    runtime_daemons = (
        inputs.reduced_runtime.get("daemons", {})
        if isinstance(inputs.reduced_runtime, dict)
        else {}
    )
    doctor = build_reviewer_doctor_surface(
        contract=inputs.reviewer_runtime,
        collaboration=asdict(inputs.collaboration),
        recovery_assessment=inputs.recovery_assessment,
        attention=inputs.attention,
        commit_pipeline=commit_pipeline,
        push_authorization=commit_pipeline.push_authorization,
        push_enforcement=inputs.bridge_liveness.get("push_enforcement"),
        runtime_state=runtime_daemons,
        snapshot_id=snapshot_id,
    )
    return CommitProjectionBundle(
        commit_pipeline=commit_pipeline,
        snapshot_id=snapshot_id,
        zref=zref,
        doctor=doctor,
    )
