"""JSONL store helpers for plan-source snapshots."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from .plan_source_retention_models import PlanSourceSnapshot
from .state_store_authority import replace_json_mappings, transform_json_mappings


def append_plan_source_snapshot(
    path: Path,
    snapshot: PlanSourceSnapshot,
) -> PlanSourceSnapshot:
    """Insert or refresh one source snapshot keyed by snapshot id."""
    return upsert_plan_source_snapshots(path, (snapshot,))[0]


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


def upsert_plan_source_snapshots(
    path: Path,
    snapshots: tuple[PlanSourceSnapshot, ...],
) -> tuple[PlanSourceSnapshot, ...]:
    """Insert or refresh multiple source snapshots in one locked write."""
    stored_inputs = tuple(replace(snapshot, snapshot_path=str(path)) for snapshot in snapshots)
    outcomes: dict[str, PlanSourceSnapshot] = {
        snapshot.snapshot_id: snapshot for snapshot in stored_inputs
    }

    def _transform(current_payloads: tuple[dict[str, object], ...]):
        current = [
            PlanSourceSnapshot.from_mapping(payload) for payload in current_payloads
        ]
        next_rows = list(current_payloads)
        current_index = {
            snapshot.snapshot_id: index for index, snapshot in enumerate(current)
        }
        for snapshot in stored_inputs:
            existing_index = current_index.get(snapshot.snapshot_id)
            if existing_index is None:
                next_rows.append(snapshot.to_dict())
                outcomes[snapshot.snapshot_id] = snapshot
                current_index[snapshot.snapshot_id] = len(next_rows) - 1
                continue
            existing = current[existing_index]
            if existing.to_dict() == snapshot.to_dict():
                outcomes[snapshot.snapshot_id] = existing
                continue
            next_rows[existing_index] = snapshot.to_dict()
            outcomes[snapshot.snapshot_id] = snapshot
        return tuple(next_rows)

    transform_json_mappings(
        path,
        transform=_transform,
        store_id="plan_source_snapshots",
    )
    return tuple(outcomes[snapshot.snapshot_id] for snapshot in stored_inputs)


def write_plan_source_snapshots_jsonl(
    path: Path,
    snapshots: tuple[PlanSourceSnapshot, ...],
) -> None:
    replace_json_mappings(
        path,
        tuple(snapshot.to_dict() for snapshot in snapshots),
        store_id="plan_source_snapshots",
    )


__all__ = [
    "append_plan_source_snapshot",
    "read_plan_source_snapshots",
    "upsert_plan_source_snapshots",
    "write_plan_source_snapshots_jsonl",
]
