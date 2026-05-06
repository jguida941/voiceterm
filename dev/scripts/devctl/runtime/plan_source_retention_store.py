"""JSONL store helpers for plan-source snapshots."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from .plan_source_retention_models import PlanSourceSnapshot


def append_plan_source_snapshot(
    path: Path,
    snapshot: PlanSourceSnapshot,
) -> PlanSourceSnapshot:
    """Append one source snapshot unless that snapshot id is already stored."""
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = replace(snapshot, snapshot_path=str(path))
    for existing in read_plan_source_snapshots(path):
        if existing.snapshot_id == stored.snapshot_id:
            return existing
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(stored.to_dict(), sort_keys=True) + "\n")
    return stored


def read_plan_source_snapshots(path: Path) -> tuple[PlanSourceSnapshot, ...]:
    """Read valid source snapshots from the JSONL store."""
    if not path.exists():
        return ()
    snapshots: list[PlanSourceSnapshot] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        snapshots.append(PlanSourceSnapshot.from_mapping(payload))
    return tuple(snapshots)


__all__ = ["append_plan_source_snapshot", "read_plan_source_snapshots"]
