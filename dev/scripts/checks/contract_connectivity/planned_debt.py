"""Typed-plan coverage for contract-connectivity debt."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ACTIVE_PLAN_STATUSES = frozenset({"queued", "in_progress", "reviewing"})
CONNECTIVITY_TOKEN = "contract-connectivity"


@dataclass(frozen=True, slots=True)
class PlannedDebtCoverage:
    """Active plan rows that own known contract-connectivity debt."""

    row_ids: tuple[str, ...] = ()

    @property
    def active(self) -> bool:
        return bool(self.row_ids)


def load_planned_debt_coverage(repo_root: Path) -> PlannedDebtCoverage:
    """Return active plan rows that explicitly cover connectivity debt."""
    plan_path = repo_root / "dev/state/plan_index.jsonl"
    if not plan_path.exists():
        return PlannedDebtCoverage()

    row_ids: list[str] = []
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if _row_covers_connectivity_debt(row):
            row_id = str(row.get("row_id", "")).strip()
            if row_id and row_id not in row_ids:
                row_ids.append(row_id)
    return PlannedDebtCoverage(row_ids=tuple(row_ids))


def _row_covers_connectivity_debt(row: dict[str, Any]) -> bool:
    if str(row.get("status", "")).strip() not in ACTIVE_PLAN_STATUSES:
        return False

    evidence_refs = [
        *[str(ref) for ref in row.get("anchor_refs", [])],
        *[str(ref) for ref in row.get("work_evidence_ids", [])],
    ]
    return any(ref.startswith(f"evidence:{CONNECTIVITY_TOKEN}:") for ref in evidence_refs)


__all__ = ["PlannedDebtCoverage", "load_planned_debt_coverage"]
