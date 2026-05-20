"""Plan-row coverage reducers for substrate commit checks."""

from __future__ import annotations

from typing import Any

from dev.scripts.devctl.runtime.commit_to_plan_row_reducer import (
    plan_row_closure_receipt_succeeded,
)
from dev.scripts.devctl.runtime.master_plan_parse import plan_row_from_mapping

APPLIED_STATUSES = ("applied", "completed", "closed_via_commit_anchor")


def covered_commit_shas(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    covered: list[str] = []
    for row_payload in rows:
        row = plan_row_from_mapping(row_payload)
        if row.status not in APPLIED_STATUSES:
            continue
        refs = (row.commit_anchor_ref, *row.anchor_refs)
        for ref in refs:
            commit_ref = commit_ref_value(ref)
            if commit_ref:
                covered.append(commit_ref)
    return tuple(dict.fromkeys(covered))


def successful_closure_commit_shas(
    receipts: tuple[dict[str, Any], ...],
) -> tuple[str, ...]:
    covered: list[str] = []
    for receipt in receipts:
        if not plan_row_closure_receipt_succeeded(receipt):
            continue
        commit_sha = str(receipt.get("commit_sha") or "").strip()
        if commit_sha:
            covered.append(commit_sha)
            continue
        commit_ref = commit_ref_value(receipt.get("commit_anchor_ref"))
        if commit_ref:
            covered.append(commit_ref)
    return tuple(dict.fromkeys(covered))


def commit_ref_value(value: object) -> str:
    text = str(value or "").strip()
    if text.startswith("commit:"):
        return text.removeprefix("commit:").strip()
    return ""
