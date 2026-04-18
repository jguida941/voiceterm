"""ReviewSnapshot staging helpers for governed stage execution."""

from __future__ import annotations

from pathlib import Path

from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.review_snapshot_refresh import (
    receipt_artifact_relpaths,
    refresh_and_stage_review_snapshot,
)
from .governed_executor_git import staged_paths


def refresh_snapshot_staging(
    *,
    repo_root: Path,
) -> tuple[list[str], list[str], list[str]]:
    """Return refresh warnings, current staged paths, and any lost user paths."""
    before = staged_paths(repo_root)
    warnings = refresh_and_stage_review_snapshot(repo_root=repo_root)
    after = staged_paths(repo_root)
    return warnings, after, _missing_preserved_staged_paths(
        repo_root=repo_root,
        before=before,
        after=after,
    )


def _missing_preserved_staged_paths(
    *,
    repo_root: Path,
    before: list[str],
    after: list[str],
) -> list[str]:
    """Return user-staged paths that disappeared during snapshot refresh."""
    try:
        governance = scan_repo_governance_safely(repo_root)
    except (OSError, ValueError):
        governance = None
    artifact_allowlist = set(receipt_artifact_relpaths(governance))
    preserved_before = {path for path in before if path not in artifact_allowlist}
    return sorted(preserved_before - set(after))
