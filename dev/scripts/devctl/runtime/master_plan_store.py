"""JSONL store helpers for typed master-plan authority."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from .master_plan_contract import PlanRow
from .plan_index_authority import (
    read_plan_index_rows,
    upsert_plan_index_row,
    write_plan_index_rows,
)


def read_plan_rows_jsonl(path: Path) -> tuple[PlanRow, ...]:
    """Read typed plan rows from a JSONL authority file."""
    return read_plan_index_rows(path)


def write_plan_rows_jsonl(path: Path, rows: tuple[PlanRow, ...]) -> None:
    """Write a complete JSONL plan-row snapshot sorted by row id."""
    write_plan_index_rows(path, rows)


def upsert_plan_row_jsonl(path: Path, row: PlanRow) -> tuple[str, PlanRow]:
    """Insert or replace one row by primary key.

    Returns `(status, stored_row)`, where status is `inserted`, `updated`, or
    `already_present`.
    """
    result = upsert_plan_index_row(path, row)
    return result.status, result.stored_row


def upsert_plan_rows_jsonl(
    path: Path,
    rows: tuple[PlanRow, ...],
) -> tuple[tuple[PlanRow, ...], tuple[str, ...]]:
    """Insert or replace multiple rows via one locked plan-index write."""
    current_rows = list(read_plan_rows_jsonl(path))
    current_by_id = {row.row_id: row for row in current_rows}
    current_index = {row.row_id: index for index, row in enumerate(current_rows)}
    stored_rows: list[PlanRow] = []
    statuses: list[str] = []
    for row in rows:
        with_revision = with_plan_revision(row, tuple(current_rows))
        existing = current_by_id.get(row.row_id)
        if existing is None:
            status = "inserted"
            stored = with_revision
            current_index[row.row_id] = len(current_rows)
            current_rows.append(stored)
        elif existing.to_dict() == with_revision.to_dict():
            status = "already_present"
            stored = existing
        else:
            status = "updated"
            stored = with_revision
            current_rows[current_index[row.row_id]] = stored
        current_by_id[row.row_id] = stored
        stored_rows.append(stored)
        statuses.append(status)
    write_plan_rows_jsonl(path, tuple(current_rows))
    return tuple(stored_rows), tuple(statuses)


def plan_revision_for_rows(rows: tuple[PlanRow, ...]) -> str:
    """Return a stable revision hash for a typed row collection."""
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: item.row_id):
        digest.update(
            json.dumps(row.to_dict(), sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        )
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def with_plan_revision(row: PlanRow, rows: tuple[PlanRow, ...]) -> PlanRow:
    """Return row with `plan_revision_at_write` bound to the current snapshot."""
    return replace(row, plan_revision_at_write=plan_revision_for_rows(rows))


__all__ = [
    "plan_revision_for_rows",
    "read_plan_rows_jsonl",
    "upsert_plan_row_jsonl",
    "upsert_plan_rows_jsonl",
    "with_plan_revision",
    "write_plan_rows_jsonl",
]
