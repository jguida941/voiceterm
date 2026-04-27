"""Helpers for distinguishing push-blocking worktree dirt from staged-only intent."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .push_projection_receipt import managed_projection_receipt_paths


def change_blocks_push_dirty_tree(change: Mapping[str, object]) -> bool:
    """Return True when one collected git-status row should block push cleanliness.

    Staged-only rows are intentionally allowed: they represent "next commit"
    intent and must not block publication of the already-approved commit.
    Older callers may still provide only ``status``/``path``; keep those
    fail-closed until they upgrade to the richer worktree fields.
    """

    status = str(change.get("status", "") or "").strip()
    raw_status = str(change.get("raw_status", "") or "")
    index_status = str(change.get("index_status", "") or "")[:1]
    worktree_status = str(change.get("worktree_status", "") or "")[:1]

    if status == "??" or raw_status == "??":
        return True
    if worktree_status and worktree_status not in {" ", "?"}:
        return True
    if any((raw_status, index_status, worktree_status)):
        return False
    return bool(status or change.get("path"))


def blocking_dirty_paths(
    changes: Sequence[Mapping[str, object]],
    *,
    exclude_paths: tuple[str, ...] = (),
) -> list[str]:
    """Return only unstaged/untracked dirty paths that block push execution."""

    exclude_set = set(exclude_paths)
    paths: list[str] = []
    for change in changes:
        path = str(change.get("path", "") or "").strip()
        if not path or path in exclude_set:
            continue
        if change_blocks_push_dirty_tree(change):
            paths.append(path)
    return paths


def push_exclusion_paths(policy, *, repo_root) -> tuple[str, ...]:
    """Return worktree paths that managed push phases own separately."""
    return (
        *managed_projection_receipt_paths(policy, repo_root=repo_root),
        *policy.checkpoint.advisory_context_paths,
    )
