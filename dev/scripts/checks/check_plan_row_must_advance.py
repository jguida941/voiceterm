#!/usr/bin/env python3
"""Fail when an in-progress PlanRow accumulates work evidence without advancement."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

try:
    from ingestion_churn_advancement.jsonl import iter_jsonl as _iter_jsonl
except ModuleNotFoundError:
    from dev.scripts.checks.ingestion_churn_advancement.jsonl import (
        iter_jsonl as _iter_jsonl,
    )


COMMAND = "check_plan_row_must_advance"
CONTRACT_ID = "PlanRowMustAdvanceGuard"
DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
DEFAULT_EVIDENCE_THRESHOLD = 3
DEFAULT_PLAN_INDEX_PATH = REPO_ROOT / "dev/state/plan_index.jsonl"
DEFAULT_CLOSURE_RECEIPTS_PATH = REPO_ROOT / "dev/state/plan_row_closure_receipts.jsonl"
DEFAULT_LIFECYCLE_RECEIPTS_PATH = REPO_ROOT / "dev/state/slice_lifecycle_receipts.jsonl"

EVIDENCE_CHURN_REASON = "plan_row_evidence_churn_without_advancement"
DISPLAY_TEXT = (
    "AI DUMBASS ALERT: PlanRow is accumulating work evidence without advancement. "
    "Close it, block it, abort it, or stop adding evidence."
)


@dataclass(frozen=True, slots=True)
class PlanRowAdvancementViolation:
    row_id: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    row_id: str = DEFAULT_ROW_ID,
    plan_index_path: Path = DEFAULT_PLAN_INDEX_PATH,
    closure_receipts_path: Path = DEFAULT_CLOSURE_RECEIPTS_PATH,
    lifecycle_receipts_path: Path = DEFAULT_LIFECYCLE_RECEIPTS_PATH,
    evidence_threshold: int = DEFAULT_EVIDENCE_THRESHOLD,
) -> dict[str, object]:
    row_id = row_id.strip()
    violations: list[PlanRowAdvancementViolation] = []
    warnings: list[str] = []

    if not row_id:
        violations.append(
            PlanRowAdvancementViolation(
                row_id=row_id,
                reason="blank_plan_row_id",
                detail="plan-row advancement guard cannot resolve an empty PlanRow id",
                remediation="Pass --row-id or fix the active-row typed source.",
            )
        )
        return _report(
            row_id=row_id,
            plan_row={},
            evidence_threshold=evidence_threshold,
            has_closure_receipt=False,
            has_typed_blocker_or_abort=False,
            violations=violations,
            warnings=warnings,
            plan_index_path=plan_index_path,
            closure_receipts_path=closure_receipts_path,
            lifecycle_receipts_path=lifecycle_receipts_path,
        )

    plan_row = _find_plan_row(plan_index_path, row_id)
    if not plan_row:
        violations.append(
            PlanRowAdvancementViolation(
                row_id=row_id,
                reason="plan_row_missing",
                detail=f"PlanRow {row_id!r} was not found in {plan_index_path}",
                remediation="Use a typed ingest/update path so the active row resolves.",
            )
        )

    has_closure = _has_closure_receipt(closure_receipts_path, row_id)
    has_blocker_or_abort = _has_blocker_or_abort(lifecycle_receipts_path, row_id)

    if plan_row and _has_evidence_churn_without_advancement(
        plan_row=plan_row,
        evidence_threshold=evidence_threshold,
        has_closure_receipt=has_closure,
        has_typed_blocker_or_abort=has_blocker_or_abort,
    ):
        evidence_count = len(_sequence(plan_row.get("work_evidence_ids")))
        violations.append(
            PlanRowAdvancementViolation(
                row_id=row_id,
                reason=EVIDENCE_CHURN_REASON,
                detail=(
                    f"{row_id} has status={plan_row.get('status')!r}, "
                    f"work_evidence_count={evidence_count}, commit_anchor_ref="
                    f"{plan_row.get('commit_anchor_ref')!r}, applied_at_utc="
                    f"{plan_row.get('applied_at_utc')!r}, closure_receipt="
                    f"{has_closure}, typed_blocker_or_abort={has_blocker_or_abort}"
                ),
                remediation=(
                    "Advance the row with a commit anchor and closure receipt, emit a typed "
                    "blocker/abort receipt, or stop appending work evidence to an unadvanced row."
                ),
            )
        )

    return _report(
        row_id=row_id,
        plan_row=plan_row,
        evidence_threshold=evidence_threshold,
        has_closure_receipt=has_closure,
        has_typed_blocker_or_abort=has_blocker_or_abort,
        violations=violations,
        warnings=warnings,
        plan_index_path=plan_index_path,
        closure_receipts_path=closure_receipts_path,
        lifecycle_receipts_path=lifecycle_receipts_path,
    )


def _report(
    *,
    row_id: str,
    plan_row: Mapping[str, object],
    evidence_threshold: int,
    has_closure_receipt: bool,
    has_typed_blocker_or_abort: bool,
    violations: Sequence[PlanRowAdvancementViolation],
    warnings: Sequence[str],
    plan_index_path: Path,
    closure_receipts_path: Path,
    lifecycle_receipts_path: Path,
) -> dict[str, object]:
    commit_anchor_ref = str(plan_row.get("commit_anchor_ref", "")) if plan_row else ""
    applied_at_utc = str(plan_row.get("applied_at_utc", "")) if plan_row else ""
    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "row_id": row_id,
        "plan_index_path": str(_repo_relative(plan_index_path)),
        "closure_receipts_path": str(_repo_relative(closure_receipts_path)),
        "lifecycle_receipts_path": str(_repo_relative(lifecycle_receipts_path)),
        "plan_row_found": bool(plan_row),
        "plan_row_status": str(plan_row.get("status", "")) if plan_row else "",
        "evidence_threshold": evidence_threshold,
        "work_evidence_count": len(_sequence(plan_row.get("work_evidence_ids"))),
        "commit_anchor_ref": commit_anchor_ref,
        "applied_at_utc": applied_at_utc,
        "has_commit_anchor": bool(commit_anchor_ref.strip()),
        "has_applied_timestamp": bool(applied_at_utc.strip()),
        "has_closure_receipt": has_closure_receipt,
        "has_typed_blocker_or_abort": has_typed_blocker_or_abort,
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": list(warnings),
    }


def _has_evidence_churn_without_advancement(
    *,
    plan_row: Mapping[str, object],
    evidence_threshold: int,
    has_closure_receipt: bool,
    has_typed_blocker_or_abort: bool,
) -> bool:
    status = str(plan_row.get("status", "")).strip().lower()
    if status not in {"in_progress", "active", "testing"}:
        return False
    evidence_count = len(_sequence(plan_row.get("work_evidence_ids")))
    if evidence_count < evidence_threshold:
        return False
    if str(plan_row.get("commit_anchor_ref", "")).strip():
        return False
    if str(plan_row.get("applied_at_utc", "")).strip():
        return False
    if has_closure_receipt or has_typed_blocker_or_abort:
        return False
    return True


def _find_plan_row(path: Path, row_id: str) -> dict[str, object]:
    for row in _iter_jsonl(path):
        if row.get("contract_id") == "PlanRow" and row.get("row_id") == row_id:
            return dict(row)
    return {}


def _has_closure_receipt(path: Path, row_id: str) -> bool:
    for receipt in _iter_jsonl(path):
        if receipt.get("contract_id") != "PlanRowClosureReceipt":
            continue
        if receipt.get("plan_row_id") == row_id and bool(receipt.get("closure_succeeded")):
            return True
    return False


def _has_blocker_or_abort(path: Path, row_id: str) -> bool:
    for receipt in _iter_jsonl(path):
        if str(receipt.get("plan_row_id") or receipt.get("row_id")) != row_id:
            continue
        contract_id = str(receipt.get("contract_id", ""))
        status = str(receipt.get("status") or receipt.get("outcome") or "").lower()
        if contract_id in {"SliceAbortReceipt", "SliceBlockedReceipt"}:
            return True
        if status in {"slice_aborted", "blocked", "aborted"}:
            return True
    return False


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return ()


def _repo_relative(path: Path) -> Path:
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except (OSError, ValueError):
        return path


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- row_id: `{report.get('row_id')}`")
    lines.append(f"- plan_row_status: {report.get('plan_row_status')}")
    lines.append(f"- work_evidence_count: {report.get('work_evidence_count')}")
    lines.append(f"- evidence_threshold: {report.get('evidence_threshold')}")
    lines.append(f"- commit_anchor_ref: `{report.get('commit_anchor_ref')}`")
    lines.append(f"- applied_at_utc: `{report.get('applied_at_utc')}`")
    lines.append(f"- has_closure_receipt: {report.get('has_closure_receipt')}")
    lines.append(f"- has_typed_blocker_or_abort: {report.get('has_typed_blocker_or_abort')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if isinstance(violation, Mapping):
                lines.append(
                    f"- {violation.get('reason')}: {violation.get('detail')} "
                    f"Remediation: {violation.get('remediation')}"
                )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-id", default=DEFAULT_ROW_ID)
    parser.add_argument("--plan-index-path", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    parser.add_argument(
        "--closure-receipts-path",
        type=Path,
        default=DEFAULT_CLOSURE_RECEIPTS_PATH,
    )
    parser.add_argument(
        "--lifecycle-receipts-path",
        type=Path,
        default=DEFAULT_LIFECYCLE_RECEIPTS_PATH,
    )
    parser.add_argument(
        "--evidence-threshold",
        type=int,
        default=DEFAULT_EVIDENCE_THRESHOLD,
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            row_id=args.row_id,
            plan_index_path=args.plan_index_path,
            closure_receipts_path=args.closure_receipts_path,
            lifecycle_receipts_path=args.lifecycle_receipts_path,
            evidence_threshold=args.evidence_threshold,
        )
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
