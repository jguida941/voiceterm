"""Advisory orphan-snapshot hooks for governed VCS flows."""

from __future__ import annotations

from pathlib import Path

from ...runtime.worktree_orphan_snapshot import OrphanSnapshot
from ...runtime.worktree_orphan_snapshot_projection import (
    build_orphan_snapshot_projection,
)


def append_orphan_snapshot_advisory(
    warnings: list[str],
    *,
    repo_root: Path,
    scan_trigger: str,
) -> OrphanSnapshot | None:
    """Append a non-blocking orphan snapshot summary to VCS warnings."""
    try:
        snapshot = build_orphan_snapshot_projection(
            repo_root=repo_root,
            scan_trigger=scan_trigger,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        warnings.append(f"orphan_snapshot_advisory_unavailable: {exc}")
        return None

    warnings.append(_advisory_warning(snapshot))
    return snapshot


def _advisory_warning(snapshot: OrphanSnapshot) -> str:
    return (
        "orphan_snapshot_advisory "
        f"snapshot_hash={snapshot.snapshot_hash} "
        f"sources={snapshot.stats.total_sources} "
        f"unresolved={snapshot.stats.unresolved_sources} "
        f"load_bearing={snapshot.stats.load_bearing_sources} "
        f"trigger={snapshot.scan_trigger} "
        "gates_evaluated=false"
    )


__all__ = ["append_orphan_snapshot_advisory"]
