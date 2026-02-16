#!/usr/bin/env python3
"""Validate hardening traceability between MASTER_PLAN and audit table."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MASTER_ITEM_RE = re.compile(
    r"^- \[(?P<done>[ xX])\]\s+(?P<mp>MP-\d+)\b.*\((?P<fx>FX-\d+)\)"
)


@dataclass(frozen=True)
class MasterItem:
    mp_id: str
    fx_id: str
    done: bool


@dataclass(frozen=True)
class AuditRow:
    fx_id: str
    test_ids: str
    mp_id: str
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Enforce traceability between dev/active/MASTER_PLAN.md and "
            "RUST_GUI_AUDIT_2026-02-15.md"
        )
    )
    parser.add_argument(
        "--master-plan",
        default="dev/active/MASTER_PLAN.md",
        help="Path to master plan markdown file",
    )
    parser.add_argument(
        "--audit",
        default="RUST_GUI_AUDIT_2026-02-15.md",
        help="Path to Rust GUI audit markdown file",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc


def parse_master_items(text: str) -> dict[str, MasterItem]:
    items: dict[str, MasterItem] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = MASTER_ITEM_RE.match(line)
        if not match:
            continue
        mp_id = match.group("mp")
        fx_id = match.group("fx")
        done = match.group("done").lower() == "x"
        if mp_id in items:
            raise SystemExit(f"Duplicate master plan item found: {mp_id}")
        items[mp_id] = MasterItem(mp_id=mp_id, fx_id=fx_id, done=done)
    return items


def parse_audit_rows(text: str) -> dict[str, AuditRow]:
    rows: dict[str, AuditRow] = {}
    in_table = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not in_table:
            if line.startswith("| finding_id |") and "master_plan_item" in line:
                in_table = True
            continue
        if not line.startswith("|"):
            break
        if set(line.replace("|", "").strip()) == {"-"}:
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) != 8:
            continue
        fx_id = cells[0]
        test_ids = cells[5]
        mp_id = cells[6]
        status = cells[7]
        if not mp_id.startswith("MP-") or not fx_id.startswith("FX-"):
            continue
        if mp_id in rows:
            raise SystemExit(f"Duplicate audit row found for master plan item: {mp_id}")
        rows[mp_id] = AuditRow(
            fx_id=fx_id,
            test_ids=test_ids,
            mp_id=mp_id,
            status=status,
        )
    return rows


def normalize_status(status: str) -> str:
    return " ".join(status.strip().lower().split())


def status_is_complete_like(status: str) -> bool:
    return normalize_status(status) in {"done", "complete", "completed"}


def status_is_in_progress_like(status: str) -> bool:
    return normalize_status(status) in {"in progress", "done", "complete", "completed"}


def status_is_planned_like(status: str) -> bool:
    return normalize_status(status) in {"planned", "not started", "todo", "tbd"}


def validate(master_items: dict[str, MasterItem], audit_rows: dict[str, AuditRow]) -> list[str]:
    errors: list[str] = []
    if not master_items:
        errors.append("No master-plan items with FX mappings were found.")
        return errors
    if not audit_rows:
        errors.append("No audit traceability rows were found.")
        return errors

    for mp_id, item in sorted(master_items.items()):
        row = audit_rows.get(mp_id)
        if row is None:
            errors.append(
                f"Missing audit row for {mp_id} ({item.fx_id}) in RUST_GUI_AUDIT traceability table."
            )
            continue
        if row.fx_id != item.fx_id:
            errors.append(
                f"FX mismatch for {mp_id}: master plan has {item.fx_id} but audit row has {row.fx_id}."
            )

        if item.done and status_is_planned_like(row.status):
            errors.append(
                f"{mp_id} is complete in master plan but still marked '{row.status}' in audit table."
            )

        if not item.done and status_is_complete_like(row.status):
            errors.append(
                f"{mp_id} is not complete in master plan but marked '{row.status}' in audit table."
            )

        if status_is_in_progress_like(row.status) and "tbd" in row.test_ids.lower():
            errors.append(
                f"{mp_id} has status '{row.status}' but test_ids are still TBD in audit table."
            )

    return errors


def main() -> int:
    args = parse_args()
    master_plan_path = Path(args.master_plan)
    audit_path = Path(args.audit)

    master_items = parse_master_items(read_text(master_plan_path))
    audit_rows = parse_audit_rows(read_text(audit_path))
    errors = validate(master_items, audit_rows)

    print(
        "Traceability summary: "
        f"master_items={len(master_items)} audit_rows={len(audit_rows)} errors={len(errors)}"
    )
    if errors:
        print("Traceability errors:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Traceability check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
