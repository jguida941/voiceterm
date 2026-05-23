"""Snapshot grouping iterator for the ingestion-churn guard."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path

from .jsonl import iter_jsonl
from .models import SnapshotGroup
from .time_window import parse_timestamp, within_latest_window


def snapshot_groups(
    *,
    snapshots_path: Path,
    window_hours: int,
    warnings: list[str],
) -> Iterable[SnapshotGroup]:
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = defaultdict(list)
    for snapshot in iter_jsonl(snapshots_path):
        if snapshot.get("contract_id") != "PlanSourceSnapshot":
            continue
        source_ref = str(snapshot.get("source_doc_path") or snapshot.get("source_ref") or "")
        row_id = snapshot_row_id(snapshot)
        if not source_ref or not row_id:
            continue
        grouped[(source_ref, row_id)].append(snapshot)

    for (source_ref, row_id), snapshots in grouped.items():
        sorted_snapshots = tuple(
            sorted(
                snapshots,
                key=lambda snapshot: parse_timestamp(
                    str(snapshot.get("captured_at_utc", "")),
                    warnings,
                )
                or datetime.min.replace(tzinfo=timezone.utc),
            )
        )
        recent = within_latest_window(sorted_snapshots, window_hours, warnings)
        if recent:
            yield SnapshotGroup(source_ref=source_ref, row_id=row_id, snapshots=recent)


def snapshot_row_id(snapshot: Mapping[str, object]) -> str:
    row_id = str(snapshot.get("plan_row_id", "") or "")
    if row_id:
        return row_id
    refs = snapshot.get("existing_owner_row_refs")
    if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
        for ref in refs:
            text = str(ref).strip()
            if text:
                return text
    return ""
