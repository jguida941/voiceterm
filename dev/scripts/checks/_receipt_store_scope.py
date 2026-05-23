"""Shared scope-dispatch helper for receipt-store path resolvers.

``store_paths_for_scope`` previously lived (byte-identically) in both
``receipt_store_consumer/paths.py`` and
``receipt_store_coverage_sweep/sweep_paths.py``. The dispatch shape is the
same; only the scope-specific ``all_*`` / ``changed_*`` helpers differ.

This module exposes a single higher-order ``resolve_store_paths_for_scope``
that accepts those scope-specific functions, removing the duplication.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path


def resolve_store_paths_for_scope(
    *,
    repo_root: Path,
    scope: str,
    changed_paths: Sequence[str | Path] | None,
    warnings: list[str],
    all_paths_fn: Callable[[Path], tuple[str, ...]],
    changed_paths_fn: Callable[..., tuple[str, ...]],
    git_changed_paths_fn: Callable[[Path, list[str]], tuple[Path, ...]],
) -> tuple[str, ...]:
    """Generic ``store_paths_for_scope`` dispatcher.

    ``all_paths_fn`` and ``changed_paths_fn`` are scope-specific path
    resolvers; ``git_changed_paths_fn`` discovers the changed worktree paths
    when the caller has not supplied a pre-computed list.
    """

    if scope == "all":
        return all_paths_fn(repo_root)
    if scope != "changed":
        warnings.append(f"unknown scope {scope!r}; defaulting to changed")
    paths = (
        tuple(Path(path) for path in changed_paths)
        if changed_paths is not None
        else git_changed_paths_fn(repo_root, warnings)
    )
    return changed_paths_fn(paths, repo_root=repo_root)
