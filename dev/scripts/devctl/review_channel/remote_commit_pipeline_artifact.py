"""Read-only helpers for the remote commit pipeline artifact surface."""

from __future__ import annotations

import json
from pathlib import Path

from ..runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
    remote_commit_pipeline_contract_from_mapping,
)


COMMIT_PIPELINE_FILENAME = "commit_pipeline.json"


def load_remote_commit_pipeline_contract(
    *,
    output_root: Path,
) -> RemoteCommitPipelineContract:
    """Load the canonical commit-pipeline artifact or fail closed to blocked."""
    artifact_path = output_root / COMMIT_PIPELINE_FILENAME
    if not artifact_path.exists():
        return RemoteCommitPipelineContract()

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return RemoteCommitPipelineContract(
            blocked_reason="commit_pipeline_artifact_unreadable"
        )

    if not isinstance(payload, dict):
        return RemoteCommitPipelineContract(
            blocked_reason="commit_pipeline_artifact_invalid"
        )
    return remote_commit_pipeline_contract_from_mapping(payload)
