"""Freshness helpers for repo-pack review-channel projection caches."""

from __future__ import annotations

from pathlib import Path


def projection_dependency_paths(
    *,
    bridge_path: Path,
    review_channel_path: Path,
    push_report_path: Path | None = None,
) -> tuple[Path, ...]:
    """Return the authoritative source paths for review projection caches."""
    paths: list[Path] = [bridge_path, review_channel_path]
    if push_report_path is not None:
        paths.append(push_report_path)
    return tuple(paths)


def cache_is_fresh(
    cache_path: Path | None,
    *,
    freshness_paths: tuple[Path, ...],
) -> bool:
    """Return whether *cache_path* is at least as fresh as every source path."""
    if cache_path is None:
        return False
    try:
        cache_mtime_ns = cache_path.stat().st_mtime_ns
    except OSError:
        return False
    for source_path in freshness_paths:
        try:
            if source_path.stat().st_mtime_ns > cache_mtime_ns:
                return False
        except OSError:
            continue
    return True
