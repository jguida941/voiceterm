"""Fast latest-snapshot resolution for Step 0 context-graph consumers."""

from __future__ import annotations

import json
from pathlib import Path

from .snapshot_payload import SnapshotResolutionError
from .snapshot_store import (
    _resolve_snapshot_dir,
    _snapshot_filename_timestamp,
    load_context_graph_snapshot,
)


def latest_context_graph_snapshot_path(
    *,
    repo_root: Path | None = None,
    snapshot_dir: Path | None = None,
) -> Path | None:
    """Return the newest valid snapshot path without parsing the full store."""
    effective_snapshot_dir = _resolve_snapshot_dir(
        repo_root=repo_root,
        snapshot_dir=snapshot_dir,
    )
    if not effective_snapshot_dir.exists():
        return None
    candidates = sorted(
        (path.resolve() for path in effective_snapshot_dir.glob("*.json")),
        key=_snapshot_filename_sort_key,
    )
    for path in reversed(candidates):
        try:
            load_context_graph_snapshot(path)
        except (OSError, json.JSONDecodeError, SnapshotResolutionError):
            continue
        return path
    return None
def _snapshot_filename_sort_key(path: Path) -> tuple[str, str]:
    return (_snapshot_filename_timestamp(path), path.name)
