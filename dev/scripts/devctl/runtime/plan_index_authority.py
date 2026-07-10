"""Canonical locked writer for ``dev/state/plan_index.jsonl``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .master_plan_contract import PlanRow
from .master_plan_parse import plan_row_from_mapping
from .state_store_authority import (
    json_line,
    read_json_mappings_strict,
    replace_json_mappings,
    transform_json_mappings,
)


@dataclass(frozen=True, slots=True)
class PlanIndexAuthorityResult:
    """Bounded result for one plan-index authority write."""

    status: str
    stored_row: PlanRow
    row_count: int
    authority_path: str


def read_plan_index_rows(path: Path) -> tuple[PlanRow, ...]:
    """Read plan rows through the canonical plan-index authority seam."""
    return tuple(
        plan_row_from_mapping(payload) for payload in read_json_mappings_strict(path)
    )


def write_plan_index_rows(path: Path, rows: tuple[PlanRow, ...]) -> None:
    """Replace the plan-index snapshot through the canonical authority seam."""
    ordered = sorted(rows, key=lambda row: row.row_id)
    replace_json_mappings(
        path,
        tuple(row.to_dict() for row in ordered),
        store_id="plan_index",
        serializer=_plan_row_json_line,
    )


def upsert_plan_index_row(path: Path, row: PlanRow) -> PlanIndexAuthorityResult:
    """Insert or replace one PlanRow via a locked read-modify-write."""
    outcome: dict[str, object] = {
        "status": "inserted",
        "stored": row.to_dict(),
        "row_count": 0,
    }

    def _transform(current_payloads: tuple[dict[str, object], ...]):
        rows = [plan_row_from_mapping(payload) for payload in current_payloads]
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
        ordered = sorted(next_rows, key=lambda item: item.row_id)
        outcome["status"] = status
        outcome["stored"] = stored.to_dict()
        outcome["row_count"] = len(ordered)
        return tuple(item.to_dict() for item in ordered)

    transform_json_mappings(
        path,
        transform=_transform,
        store_id="plan_index",
        serializer=_plan_row_json_line,
    )
    stored_row = plan_row_from_mapping(dict(outcome["stored"]))
    return PlanIndexAuthorityResult(
        status=str(outcome["status"]),
        stored_row=stored_row,
        row_count=int(outcome["row_count"]),
        authority_path=str(path),
    )


def _plan_row_json_line(payload: dict[str, object]) -> str:
    return json_line(payload, compact=True)


__all__ = [
    "PlanIndexAuthorityResult",
    "read_plan_index_rows",
    "upsert_plan_index_row",
    "write_plan_index_rows",
]
