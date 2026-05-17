"""Managed projection path resolution for governed push receipts."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.review_snapshot_refresh import receipt_artifact_relpaths


def managed_projection_receipt_paths(
    policy,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[str, ...]:
    """Return the managed projection paths owned by receipt commits."""
    try:
        governance = scan_repo_governance_safely(repo_root)
    except (OSError, ValueError):
        governance = None
    configured = tuple(getattr(policy.checkpoint, "compatibility_projection_paths", ()))
    return tuple(dict.fromkeys((*receipt_artifact_relpaths(governance), *configured)))


__all__ = ["managed_projection_receipt_paths"]
