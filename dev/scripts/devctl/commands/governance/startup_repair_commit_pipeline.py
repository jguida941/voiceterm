"""Commit-pipeline readers for startup repair classification."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
)
from ...runtime.checkpoint_repair_authority import (
    CheckpointRepairAuthority,
    checkpoint_repair_authority_from_pipeline,
)
from ...runtime.review_state_models import ReviewState
from ...runtime.startup_repair_models import (
    StartupRepairActionRecord,
    StartupRepairRuntimeInputs,
)


def collect_checkpoint_repair_authority(
    *,
    repo_root: Path,
    ctx,
) -> CheckpointRepairAuthority | None:
    """Read persisted checkpoint repair promotion authority, if present."""
    return checkpoint_repair_authority_from_pipeline(
        _read_commit_pipeline(repo_root=repo_root, ctx=ctx)
    )


def collect_runtime_inputs(
    repo_root: Path,
    ctx,
    review_state: ReviewState | None,
    review_error: str | None,
    applied_actions: tuple[StartupRepairActionRecord, ...],
) -> StartupRepairRuntimeInputs:
    """Collect optional runtime facts for startup repair classification."""
    return StartupRepairRuntimeInputs(
        review_state=review_state,
        review_error=review_error,
        applied_actions=applied_actions,
        checkpoint_repair_authority=collect_checkpoint_repair_authority(
            repo_root=repo_root,
            ctx=ctx,
        ),
    )


def _read_commit_pipeline(*, repo_root: Path, ctx):
    governance = ctx.governance
    if governance is None:
        return load_remote_commit_pipeline_contract(output_root=repo_root)
    review_root = str(governance.artifact_roots.review_root or "").strip()
    if not review_root:
        return load_remote_commit_pipeline_contract(output_root=repo_root)
    review_root_path = (repo_root / review_root).resolve()
    candidates = []
    if review_root_path.name == "latest":
        candidates.append(review_root_path.parent / "projections" / "latest")
    candidates.append(review_root_path)
    for output_root in candidates:
        pipeline = load_remote_commit_pipeline_contract(output_root=output_root)
        if pipeline.pipeline_id:
            return pipeline
    return pipeline


__all__ = [
    "collect_checkpoint_repair_authority",
    "collect_runtime_inputs",
]
