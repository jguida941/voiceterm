"""Plan-row / closure / lifecycle state lookups for the ingestion-churn guard."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .jsonl import iter_jsonl


def plan_rows_by_id(path: Path) -> dict[str, Mapping[str, object]]:
    rows: dict[str, Mapping[str, object]] = {}
    for row in iter_jsonl(path):
        if row.get("contract_id") != "PlanRow":
            continue
        row_id = str(row.get("row_id", "") or "")
        if row_id:
            rows[row_id] = row
    return rows


def has_plan_row_commit_anchor(row: Mapping[str, object]) -> bool:
    return bool(str(row.get("commit_anchor_ref", "") or "").strip()) or bool(
        str(row.get("applied_at_utc", "") or "").strip()
    )


def closure_row_ids(path: Path) -> frozenset[str]:
    row_ids: set[str] = set()
    for receipt in iter_jsonl(path):
        if receipt.get("contract_id") != "PlanRowClosureReceipt":
            continue
        if not bool(receipt.get("closure_succeeded")):
            continue
        row_id = str(receipt.get("plan_row_id", "") or "")
        if row_id:
            row_ids.add(row_id)
    return frozenset(row_ids)


def blocked_or_aborted_row_ids(path: Path) -> frozenset[str]:
    row_ids: set[str] = set()
    for receipt in iter_jsonl(path):
        row_id = str(receipt.get("plan_row_id") or receipt.get("row_id") or "").strip()
        if not row_id:
            continue
        contract_id = str(receipt.get("contract_id", "") or "")
        status = str(receipt.get("status") or receipt.get("outcome") or "").lower()
        if contract_id in {"SliceAbortReceipt", "SliceBlockedReceipt"}:
            row_ids.add(row_id)
            continue
        if status in {"slice_aborted", "blocked", "aborted"}:
            row_ids.add(row_id)
    return frozenset(row_ids)
