"""JSONL store helpers for typed master-plan authority."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from .master_plan_contract import PlanRow
from .master_plan_parse import plan_row_from_mapping


def read_plan_rows_jsonl(path: Path) -> tuple[PlanRow, ...]:
    """Read typed plan rows from a JSONL authority file."""
    if not path.exists():
        return ()
    rows: list[PlanRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            rows.append(plan_row_from_mapping(payload))
    return tuple(rows)


def write_plan_rows_jsonl(path: Path, rows: tuple[PlanRow, ...]) -> None:
    """Write a complete JSONL plan-row snapshot sorted by row id."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda row: row.row_id)
    payload = "\n".join(
        json.dumps(row.to_dict(), sort_keys=True, separators=(",", ":"))
        for row in ordered
    )
    path.write_text(f"{payload}\n" if payload else "", encoding="utf-8")


def upsert_plan_row_jsonl(path: Path, row: PlanRow) -> tuple[str, PlanRow]:
    """Insert or replace one row by primary key.

    Returns `(status, stored_row)`, where status is `inserted`, `updated`, or
    `already_present`.
    """
    rows = list(read_plan_rows_jsonl(path))
    next_rows: list[PlanRow] = []
    status = "inserted"
    stored = row
    for existing in rows:
        if existing.row_id != row.row_id:
            next_rows.append(existing)
            continue
        if existing.to_dict() == row.to_dict():
            status = "already_present"
            stored = existing
        else:
            status = "updated"
            stored = row
        next_rows.append(stored)
    if status == "inserted":
        next_rows.append(row)
    write_plan_rows_jsonl(path, tuple(next_rows))
    return status, stored


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
    "with_plan_revision",
    "write_plan_rows_jsonl",
]
