"""Managed receipt helpers for push-state projection."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..runtime.review_snapshot_refresh import (
    is_managed_receipt_commit,
    receipt_commit_ancestor_shas,
    receipt_artifact_relpaths,
)
from .push_policy import PushPolicy


@dataclass(frozen=True, slots=True)
class AheadCommitClassification:
    """Source-vs-receipt classification for unpublished local commits."""

    source_commits: int | None = None
    managed_receipt_commits: int = 0
    unclassified_commits: int | None = None


def dedupe_paths(*paths: str) -> tuple[str, ...]:
    """Return stable unique non-empty repo-relative paths."""
    return tuple(dict.fromkeys(path for path in paths if path))


def managed_projection_exclusion_paths(policy: PushPolicy) -> tuple[str, ...]:
    """Return receipt-managed projection paths that are not source edits."""
    return dedupe_paths(
        *receipt_artifact_relpaths(None),
        *policy.checkpoint.compatibility_projection_paths,
    )


def managed_receipt_ancestor_shas(
    *,
    repo_root: Path,
    current_head: str,
) -> tuple[str, ...]:
    try:
        return receipt_commit_ancestor_shas(
            repo_root=repo_root,
            current_head=current_head,
            governance=None,
        )
    except (AttributeError, TypeError, ValueError):
        return ()


def classify_ahead_commits(
    *,
    repo_root: Path,
    upstream_ref: str,
    ahead_of_upstream_commits: int | None,
    git_stdout: Callable[[Path, str, str, str], str],
) -> AheadCommitClassification:
    """Split unpublished commits into source edits and managed receipt commits."""
    if not upstream_ref or not isinstance(ahead_of_upstream_commits, int):
        return AheadCommitClassification()
    if ahead_of_upstream_commits <= 0:
        return AheadCommitClassification(
            source_commits=0,
            managed_receipt_commits=0,
            unclassified_commits=0,
        )
    try:
        revs = git_stdout(
            repo_root,
            "rev-list",
            "--reverse",
            f"{upstream_ref}..HEAD",
        )
    except Exception:  # broad-except: allow reason=git rev-list failure must not crash push-state classifier; fallback=treat all ahead-commits as unclassified
        return _unclassified(ahead_of_upstream_commits)
    shas = tuple(line.strip() for line in revs.splitlines() if line.strip())
    if not shas:
        return _unclassified(ahead_of_upstream_commits)

    managed_receipts = sum(
        1
        for sha in shas
        if is_managed_receipt_commit(repo_root=repo_root, current_head=sha)
    )
    return AheadCommitClassification(
        source_commits=len(shas) - managed_receipts,
        managed_receipt_commits=managed_receipts,
        unclassified_commits=0,
    )


def _unclassified(ahead_of_upstream_commits: int) -> AheadCommitClassification:
    return AheadCommitClassification(
        source_commits=None,
        managed_receipt_commits=0,
        unclassified_commits=ahead_of_upstream_commits,
    )
