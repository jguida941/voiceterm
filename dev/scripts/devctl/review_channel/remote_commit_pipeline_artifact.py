"""Helpers for the remote commit pipeline artifact surface."""

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


def persist_remote_commit_pipeline_contract(
    contract: RemoteCommitPipelineContract,
    *,
    output_root: Path,
) -> Path:
    """Write the canonical commit-pipeline artifact and return its path.

    Per Codex rev_pkt_2406/2409/2413: same atomic-replace contract as
    ``projection_bundle._atomic_write_text`` — write to a unique tempfile
    in the same directory, fsync, then ``os.replace`` so concurrent
    readers (e.g. ``check_review_surface_consistency``) never observe a
    half-written commit_pipeline.json.
    """
    from .projection_bundle import _atomic_write_text

    artifact_path = output_root / COMMIT_PIPELINE_FILENAME
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(
        artifact_path,
        json.dumps(contract.to_dict(), indent=2) + "\n",
    )
    return artifact_path
