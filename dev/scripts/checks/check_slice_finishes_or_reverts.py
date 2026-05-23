#!/usr/bin/env python3
"""Fail when an implementation slice is left dirty without closure evidence."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
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
    from slice_finishes_or_reverts_support import SliceGuardSupport as Support
except ModuleNotFoundError:
    from dev.scripts.checks.slice_finishes_or_reverts_support import (
        SliceGuardSupport as Support,
    )


COMMAND = "check_slice_finishes_or_reverts"
CONTRACT_ID = "SliceFinishesOrRevertsGuard"
DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
DEFAULT_PLAN_INDEX_PATH = REPO_ROOT / "dev/state/plan_index.jsonl"
DEFAULT_CLOSURE_RECEIPTS_PATH = REPO_ROOT / "dev/state/plan_row_closure_receipts.jsonl"
DEFAULT_ABORT_RECEIPTS_PATH = REPO_ROOT / "dev/state/slice_lifecycle_receipts.jsonl"
DEFAULT_FEATURE_PROOF_DIR = REPO_ROOT / "dev/reports/feature_proof_receipts"

HALF_BUILT_REASON = "slice_left_half_built_without_receipt"
COMPLETED_MISSING_COMMIT_REASON = "completed_slice_missing_commit_anchor"
COMPLETED_MISSING_CLOSURE_REASON = "completed_slice_missing_closure_receipt"
COMPLETED_MISSING_FPR_REASON = "completed_slice_missing_proven_feature_proof"
DISPLAY_TEXT = (
    "AI DUMBASS ALERT: incomplete slice. Finish, block, or revert. "
    "Half-built work is not closure evidence."
)


@dataclass(frozen=True, slots=True)
class GuardViolation:
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
    feature_proof_dir: Path = DEFAULT_FEATURE_PROOF_DIR,
    abort_receipts_path: Path = DEFAULT_ABORT_RECEIPTS_PATH,
    git_status_output: str | None = None,
) -> dict[str, object]:
    row_id = row_id.strip()
    violations: list[GuardViolation] = []
    warnings: list[str] = []

    if not row_id:
        violations.append(
            GuardViolation(
                reason="blank_plan_row_id",
                detail="slice guard cannot resolve an empty PlanRow id",
                remediation="Pass --row-id or fix the active-row typed source.",
            )
        )
        return _report(
            row_id=row_id,
            plan_row={},
            dirty_files=(),
            has_closure_receipt=False,
            has_proven_feature_proof=False,
            has_abort_receipt=False,
            violations=violations,
            warnings=warnings,
            plan_index_path=plan_index_path,
            closure_receipts_path=closure_receipts_path,
            feature_proof_dir=feature_proof_dir,
            abort_receipts_path=abort_receipts_path,
        )

    plan_row = Support.find_plan_row(plan_index_path, row_id)
    if not plan_row:
        violations.append(
            GuardViolation(
                reason="plan_row_missing",
                detail=f"PlanRow {row_id!r} was not found in {plan_index_path}",
                remediation="Use a typed ingest/update path so the active row resolves.",
            )
        )

    dirty_files = Support.parse_git_status(
        git_status_output if git_status_output is not None else Support.git_status_output(warnings)
    )
    has_closure = Support.has_closure_receipt(closure_receipts_path, row_id)
    has_proven_fpr = Support.has_proven_feature_proof(feature_proof_dir, row_id)
    has_abort = Support.has_abort_receipt(abort_receipts_path, row_id)

    if plan_row:
        violations.extend(
            _completed_slice_evidence_violations(
                plan_row=plan_row,
                has_closure_receipt=has_closure,
                has_proven_feature_proof=has_proven_fpr,
            )
        )

    if plan_row and _is_half_built_open_slice(
        plan_row=plan_row,
        dirty_files=dirty_files,
        has_closure_receipt=has_closure,
        has_proven_feature_proof=has_proven_fpr,
        has_abort_receipt=has_abort,
    ):
        violations.append(
            GuardViolation(
                reason=HALF_BUILT_REASON,
                detail=(
                    f"{row_id} has {len(dirty_files)} dirty files, status="
                    f"{plan_row.get('status')!r}, commit_anchor_ref="
                    f"{plan_row.get('commit_anchor_ref')!r}, applied_at_utc="
                    f"{plan_row.get('applied_at_utc')!r}, closure_receipt="
                    f"{has_closure}, feature_proof_receipt={has_proven_fpr}, "
                    f"abort_receipt={has_abort}"
                ),
                remediation=(
                    "Finish the slice with proof + closure receipt, emit a typed "
                    "slice_aborted/slice_blocked receipt, or revert/disposition the dirty work."
                ),
            )
        )

    return _report(
        row_id=row_id,
        plan_row=plan_row,
        dirty_files=dirty_files,
        has_closure_receipt=has_closure,
        has_proven_feature_proof=has_proven_fpr,
        has_abort_receipt=has_abort,
        violations=violations,
        warnings=warnings,
        plan_index_path=plan_index_path,
        closure_receipts_path=closure_receipts_path,
        feature_proof_dir=feature_proof_dir,
        abort_receipts_path=abort_receipts_path,
    )


def _report(
    *,
    row_id: str,
    plan_row: Mapping[str, object],
    dirty_files: Sequence[str],
    has_closure_receipt: bool,
    has_proven_feature_proof: bool,
    has_abort_receipt: bool,
    violations: Sequence[GuardViolation],
    warnings: Sequence[str],
    plan_index_path: Path,
    closure_receipts_path: Path,
    feature_proof_dir: Path,
    abort_receipts_path: Path,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "row_id": row_id,
        "plan_index_path": str(Support.repo_relative(plan_index_path)),
        "closure_receipts_path": str(Support.repo_relative(closure_receipts_path)),
        "feature_proof_dir": str(Support.repo_relative(feature_proof_dir)),
        "abort_receipts_path": str(Support.repo_relative(abort_receipts_path)),
        "plan_row_found": bool(plan_row),
        "plan_row_status": str(plan_row.get("status", "")) if plan_row else "",
        "commit_anchor_ref": str(plan_row.get("commit_anchor_ref", "")) if plan_row else "",
        "applied_at_utc": str(plan_row.get("applied_at_utc", "")) if plan_row else "",
        "work_evidence_count": len(Support.sequence(plan_row.get("work_evidence_ids"))),
        "dirty_file_count": len(dirty_files),
        "dirty_files": list(dirty_files),
        "has_closure_receipt": has_closure_receipt,
        "has_proven_feature_proof_receipt": has_proven_feature_proof,
        "has_slice_abort_or_block_receipt": has_abort_receipt,
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": list(warnings),
    }


def _is_half_built_open_slice(
    *,
    plan_row: Mapping[str, object],
    dirty_files: Sequence[str],
    has_closure_receipt: bool,
    has_proven_feature_proof: bool,
    has_abort_receipt: bool,
) -> bool:
    if not dirty_files:
        return False
    status = str(plan_row.get("status", "")).strip().lower()
    if status not in {"in_progress", "queued", "active", "spec", "testing"}:
        return False
    if str(plan_row.get("commit_anchor_ref", "")).strip():
        return False
    if str(plan_row.get("applied_at_utc", "")).strip():
        return False
    # A FeatureProofReceipt alone is not closure. The row must also have closure
    # state or an explicit abort/block receipt, otherwise dirty work can hide
    # behind a proof fragment while the PlanRow remains in_progress.
    if has_closure_receipt or has_abort_receipt:
        return False
    return True


def _completed_slice_evidence_violations(
    *,
    plan_row: Mapping[str, object],
    has_closure_receipt: bool,
    has_proven_feature_proof: bool,
) -> tuple[GuardViolation, ...]:
    status = str(plan_row.get("status", "")).strip().lower()
    if status not in {"applied", "completed", "closed"}:
        return ()
    row_id = str(plan_row.get("row_id", ""))
    violations: list[GuardViolation] = []
    if not str(plan_row.get("commit_anchor_ref", "")).strip():
        violations.append(
            GuardViolation(
                reason=COMPLETED_MISSING_COMMIT_REASON,
                detail=f"{row_id} has status={status!r} but commit_anchor_ref is empty",
                remediation="Reduce the proven commit into PlanRow.commit_anchor_ref before closure.",
            )
        )
    if not str(plan_row.get("applied_at_utc", "")).strip():
        violations.append(
            GuardViolation(
                reason=COMPLETED_MISSING_COMMIT_REASON,
                detail=f"{row_id} has status={status!r} but applied_at_utc is empty",
                remediation="Reduce the proven commit into PlanRow.applied_at_utc before closure.",
            )
        )
    if not has_closure_receipt:
        violations.append(
            GuardViolation(
                reason=COMPLETED_MISSING_CLOSURE_REASON,
                detail=f"{row_id} has status={status!r} without a successful PlanRowClosureReceipt",
                remediation="Emit or repair the existing PlanRowClosureReceipt for this row.",
            )
        )
    if not has_proven_feature_proof:
        violations.append(
            GuardViolation(
                reason=COMPLETED_MISSING_FPR_REASON,
                detail=f"{row_id} has status={status!r} without FeatureProofReceipt(proven_passed)",
                remediation="Emit a FeatureProofReceipt(proven_passed) referencing this row.",
            )
        )
    return tuple(violations)


def render_markdown(report: Mapping[str, object]) -> str:
    return Support.render_markdown(report, COMMAND)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-id", default=DEFAULT_ROW_ID)
    parser.add_argument("--plan-index-path", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    parser.add_argument(
        "--closure-receipts-path",
        type=Path,
        default=DEFAULT_CLOSURE_RECEIPTS_PATH,
    )
    parser.add_argument("--feature-proof-dir", type=Path, default=DEFAULT_FEATURE_PROOF_DIR)
    parser.add_argument("--abort-receipts-path", type=Path, default=DEFAULT_ABORT_RECEIPTS_PATH)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            row_id=args.row_id,
            plan_index_path=args.plan_index_path,
            closure_receipts_path=args.closure_receipts_path,
            feature_proof_dir=args.feature_proof_dir,
            abort_receipts_path=args.abort_receipts_path,
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
