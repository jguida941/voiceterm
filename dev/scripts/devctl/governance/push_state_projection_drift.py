"""Classify ignored worktree paths for push-state projection drift."""

from __future__ import annotations


def matching_excluded_paths(
    excluded_paths: tuple[str, ...],
    configured_paths: tuple[str, ...],
) -> tuple[str, ...]:
    """Return excluded paths that belong to the configured governance lane."""
    configured = set(configured_paths)
    if not configured:
        return ()
    return tuple(path for path in excluded_paths if path in configured)
