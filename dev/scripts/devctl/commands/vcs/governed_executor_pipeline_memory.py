"""In-process pipeline handle helpers for governed VCS execution."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
)
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from .governed_executor_sync import persist_pipeline_contract_only


def load_pipeline_with_memory(
    *,
    output_root: Path,
    fallback: RemoteCommitPipelineContract | None,
) -> RemoteCommitPipelineContract:
    """Load the projected pipeline, falling back to the same-process handle."""
    pipeline = load_remote_commit_pipeline_contract(output_root=output_root)
    if pipeline.pipeline_id or fallback is None or not fallback.pipeline_id:
        return pipeline
    return fallback


def persist_pipeline_contract_only_for_executor(
    executor,
    pipeline: RemoteCommitPipelineContract,
) -> list[str]:
    """Persist the pipeline contract and keep the executor handle current."""
    persist_pipeline_contract_only(
        pipeline,
        projections_root=executor.projections_root,
        repo_root=executor.repo_root,
    )
    executor.last_persisted_pipeline = pipeline
    return []
