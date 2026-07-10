"""Worktree-count parser for PushEnforcement runtime records."""

from __future__ import annotations

from collections.abc import Mapping

from ..governance.push_state_git import WorktreeChangeCounts
from .value_coercion import coerce_int, coerce_string_items


def worktree_change_counts_from_payload(
    payload: Mapping[str, object],
) -> WorktreeChangeCounts:
    """Parse worktree count fields through their owning typed contract."""
    return WorktreeChangeCounts(
        dirty_path_count=coerce_int(payload.get("dirty_path_count")),
        untracked_path_count=coerce_int(payload.get("untracked_path_count")),
        staged_path_count=coerce_int(payload.get("staged_path_count")),
        unstaged_path_count=coerce_int(payload.get("unstaged_path_count")),
        excluded_path_count=coerce_int(payload.get("excluded_path_count")),
        excluded_paths=coerce_string_items(payload.get("excluded_paths")),
    )
