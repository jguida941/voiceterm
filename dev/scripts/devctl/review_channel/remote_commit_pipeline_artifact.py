"""Helpers for the remote commit pipeline artifact surface."""

from __future__ import annotations

import json
from pathlib import Path

from ..repo_packs import active_path_config
from ..runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
    remote_commit_pipeline_contract_from_mapping,
)
from ..runtime.pipeline_local_delivery_receipts import (
    apply_local_delivery_receipt,
)


COMMIT_PIPELINE_FILENAME = "commit_pipeline.json"


def load_canonical_remote_commit_pipeline_contract(
    *,
    repo_root: Path,
) -> RemoteCommitPipelineContract:
    """Load the canonical event-backed pipeline, with legacy status fallback."""
    for output_root in _canonical_pipeline_roots(repo_root):
        artifact_path = output_root / COMMIT_PIPELINE_FILENAME
        if not artifact_path.exists():
            continue
        return load_remote_commit_pipeline_contract(output_root=output_root)
    return RemoteCommitPipelineContract()


def load_remote_commit_pipeline_contract(
    *,
    output_root: Path,
    receipts_root: Path | None = None,
) -> RemoteCommitPipelineContract:
    """Load the canonical commit-pipeline artifact or fail closed to blocked."""
    resolved_output_root = output_root.resolve()
    artifact_path = resolved_output_root / COMMIT_PIPELINE_FILENAME
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
    receipt_root = (
        receipts_root.resolve()
        if receipts_root is not None
        else _default_receipts_root(resolved_output_root)
    )
    payload = apply_local_delivery_receipt(
        payload,
        receipts_root=receipt_root,
        pipeline_path=artifact_path,
    )
    return remote_commit_pipeline_contract_from_mapping(payload)


def persist_remote_commit_pipeline_contract(
    contract: RemoteCommitPipelineContract,
    *,
    output_root: Path,
) -> Path:
    """Write the canonical commit-pipeline artifact and return its path.

    Per Codex rev_pkt_2406/2409/2413: same atomic-replace contract as
    the projection bundle writer — write to a unique tempfile
    in the same directory, fsync, then ``os.replace`` so concurrent
    readers (e.g. ``check_review_surface_consistency``) never observe a
    half-written commit_pipeline.json.
    """
    from .projection_bundle_io import atomic_write_text

    artifact_path = output_root / COMMIT_PIPELINE_FILENAME
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        artifact_path,
        json.dumps(contract.to_dict(), indent=2) + "\n",
    )
    return artifact_path


def _canonical_pipeline_roots(repo_root: Path) -> tuple[Path, ...]:
    """Return preferred then legacy roots that may own commit_pipeline.json."""
    from .event_store import resolve_artifact_paths

    roots: list[Path] = []
    try:
        roots.append(Path(resolve_artifact_paths(repo_root=repo_root).projections_root))
    except (OSError, ValueError):
        pass
    config = active_path_config()
    roots.append(repo_root / config.review_projections_dir_rel)
    roots.append(repo_root / config.review_status_dir_rel)
    deduped: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(root)
    return tuple(deduped)


def _default_receipts_root(output_root: Path) -> Path:
    """Resolve the sibling review-channel/latest receipt directory."""
    try:
        review_channel_root = output_root.parent.parent
    except IndexError:
        return output_root
    return review_channel_root / "latest"
