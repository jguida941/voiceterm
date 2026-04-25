"""Managed projection refresh helpers for governed push preflight."""

from __future__ import annotations

from pathlib import Path

from ...config import REPO_ROOT
from ...runtime.review_snapshot_refresh import refresh_review_snapshot_file
from .push_projection_receipt import auto_commit_managed_projection_receipt


def refresh_managed_projections_before_preflight(
    state,
    policy,
    *,
    repo_root: Path = REPO_ROOT,
) -> None:
    """Refresh ReviewSnapshot and commit managed projection drift before preflight."""
    warnings = refresh_review_snapshot_file(repo_root=repo_root)
    state.warnings.extend(warning for warning in warnings if warning)
    auto_commit_managed_projection_receipt(
        state,
        policy,
        repo_root=repo_root,
    )


__all__ = ["refresh_managed_projections_before_preflight"]
