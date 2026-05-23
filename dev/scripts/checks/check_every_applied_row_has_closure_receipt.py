#!/usr/bin/env python3
"""Fail when terminal PlanRows lack closure and proof receipts."""

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


COMMAND = "check_every_applied_row_has_closure_receipt"
CONTRACT_ID = "EveryAppliedRowHasClosureReceiptGuard"
DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
DEFAULT_PLAN_INDEX_PATH = REPO_ROOT / "dev/state/plan_index.jsonl"
DEFAULT_CLOSURE_RECEIPTS_PATH = REPO_ROOT / "dev/state/plan_row_closure_receipts.jsonl"
DEFAULT_FEATURE_PROOF_DIR = REPO_ROOT / "dev/reports/feature_proof_receipts"

TERMINAL_STATUSES = frozenset({"applied", "completed", "closed", "archived"})

REASON_MISSING_CLOSURE = "terminal_plan_row_missing_closure_receipt"
REASON_MISSING_PROVEN_FPR = "terminal_plan_row_missing_proven_feature_proof"
DISPLAY_TEXT = (
    "AI DUMBASS ALERT: terminal PlanRow has no closure proof. Applied, "
    "completed, closed, and archived rows require PlanRowClosureReceipt plus "
    "FeatureProofReceipt(proven_passed)."
)


@dataclass(frozen=True, slots=True)
class TerminalPlanRowViolation:
    row_id: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    row_id: str = DEFAULT_ROW_ID,
    row_ids: Sequence[str] | None = None,
    scope: str = "current",
    plan_index_path: Path = DEFAULT_PLAN_INDEX_PATH,
    closure_receipts_path: Path = DEFAULT_CLOSURE_RECEIPTS_PATH,
    feature_proof_dir: Path = DEFAULT_FEATURE_PROOF_DIR,
) -> dict[str, object]:
    plan_rows = _plan_rows_for_scope(
        plan_index_path=plan_index_path,
        row_id=row_id,
        row_ids=row_ids,
        scope=scope,
    )
    terminal_rows = tuple(
        row for row in plan_rows if _is_terminal_status(row.get("status"))
    )
    closure_rows = _successful_closure_row_ids(closure_receipts_path)
    proven_fpr_rows = _proven_feature_proof_row_ids(feature_proof_dir)

    violations: list[TerminalPlanRowViolation] = []
    for row in terminal_rows:
        current_row_id = str(row.get("row_id") or "").strip()
        if not current_row_id:
            continue
        if current_row_id not in closure_rows:
            violations.append(
                TerminalPlanRowViolation(
                    row_id=current_row_id,
                    reason=REASON_MISSING_CLOSURE,
                    detail=(
                        f"{current_row_id} status={row.get('status')!r} has no "
                        "successful PlanRowClosureReceipt"
                    ),
                    remediation=(
                        "Reduce the proven commit through the existing "
                        "commit_to_plan_row reducer so a PlanRowClosureReceipt is written."
                    ),
                )
            )
        if current_row_id not in proven_fpr_rows:
            violations.append(
                TerminalPlanRowViolation(
                    row_id=current_row_id,
                    reason=REASON_MISSING_PROVEN_FPR,
                    detail=(
                        f"{current_row_id} status={row.get('status')!r} has no "
                        "FeatureProofReceipt(proven_passed) referencing the row"
                    ),
                    remediation=(
                        "Emit or repair a FeatureProofReceipt(proven_passed) whose "
                        "feature_id or evidence refs name this PlanRow."
                    ),
                )
            )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "scope": scope,
        "row_id": row_id,
        "plan_index_path": str(_repo_relative(plan_index_path)),
        "closure_receipts_path": str(_repo_relative(closure_receipts_path)),
        "feature_proof_dir": str(_repo_relative(feature_proof_dir)),
        "scanned_row_count": len(plan_rows),
        "terminal_row_count": len(terminal_rows),
        "closure_receipt_row_count": len(closure_rows),
        "proven_feature_proof_row_count": len(proven_fpr_rows),
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "terminal_row_ids": [
            str(row.get("row_id") or "").strip()
            for row in terminal_rows
            if str(row.get("row_id") or "").strip()
        ],
    }


def _plan_rows_for_scope(
    *,
    plan_index_path: Path,
    row_id: str,
    row_ids: Sequence[str] | None,
    scope: str,
) -> tuple[Mapping[str, object], ...]:
    rows = tuple(
        row for row in _iter_jsonl(plan_index_path) if row.get("contract_id") == "PlanRow"
    )
    requested_row_ids = tuple(
        item.strip() for item in (row_ids or ()) if item.strip()
    )
    if requested_row_ids:
        allowed = frozenset(requested_row_ids)
        return tuple(row for row in rows if str(row.get("row_id") or "") in allowed)
    if scope == "all":
        return rows
    current = row_id.strip()
    if not current:
        return ()
    return tuple(row for row in rows if str(row.get("row_id") or "") == current)


def _is_terminal_status(value: object) -> bool:
    return str(value or "").strip().lower() in TERMINAL_STATUSES


def _successful_closure_row_ids(path: Path) -> frozenset[str]:
    row_ids: set[str] = set()
    for receipt in _iter_jsonl(path):
        if receipt.get("contract_id") != "PlanRowClosureReceipt":
            continue
        if not bool(receipt.get("closure_succeeded")):
            continue
        row_id = str(receipt.get("plan_row_id") or "").strip()
        if row_id:
            row_ids.add(row_id)
    return frozenset(row_ids)


def _proven_feature_proof_row_ids(root: Path) -> frozenset[str]:
    row_ids: set[str] = set()
    if not root.exists():
        return frozenset()
    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        if payload.get("contract_id") != "FeatureProofReceipt":
            continue
        if payload.get("real_life_test_status") != "proven_passed":
            continue
        row_ids.update(_feature_proof_row_refs(payload))
    return frozenset(row_ids)


def _feature_proof_row_refs(payload: Mapping[str, object]) -> set[str]:
    refs: set[str] = set()
    feature_id = str(payload.get("feature_id") or "").strip()
    if feature_id:
        refs.add(feature_id)
    for value in _sequence(payload.get("evidence_artifacts")):
        refs.update(_row_refs_from_text(str(value)))
    dogfood_ref = str(payload.get("dogfood_invocation_evidence_ref") or "")
    refs.update(_row_refs_from_text(dogfood_ref))
    return refs


def _row_refs_from_text(text: str) -> set[str]:
    refs: set[str] = set()
    for raw_token in text.replace(",", " ").split():
        token = raw_token.strip().strip("[](){}.,;")
        if token.startswith("plan:"):
            token = token.removeprefix("plan:")
        if token.startswith("row:"):
            token = token.removeprefix("row:")
        if token.startswith("MP") or token.startswith("ROW-"):
            refs.add(token)
    return refs


def _iter_jsonl(path: Path) -> Iterable[Mapping[str, object]]:
    if not path.exists():
        return ()

    def _rows() -> Iterable[Mapping[str, object]]:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, Mapping):
                yield payload

    return _rows()


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return ()


def _repo_relative(path: Path) -> Path:
    try:
        return path.resolve().relative_to(REPO_ROOT)
    except (OSError, ValueError):
        return path


def _render_md(report: Mapping[str, object]) -> str:
    lines = [
        f"# {COMMAND}",
        "",
        f"- ok: {report['ok']}",
        f"- scope: {report['scope']}",
        f"- scanned_row_count: {report['scanned_row_count']}",
        f"- terminal_row_count: {report['terminal_row_count']}",
        f"- violation_count: {report['violation_count']}",
    ]
    violations = report.get("violations") or []
    if violations:
        lines.extend(["", "## Violations"])
        for violation in violations:
            if not isinstance(violation, Mapping):
                continue
            lines.append(
                f"- {violation.get('row_id')}: {violation.get('reason')} - "
                f"{violation.get('detail')}"
            )
    return "\n".join(lines) + "\n"


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    parser.add_argument("--scope", choices=("current", "all"), default="current")
    parser.add_argument("--row-id", action="append", default=[])
    parser.add_argument("--plan-index", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    parser.add_argument(
        "--closure-receipts",
        type=Path,
        default=DEFAULT_CLOSURE_RECEIPTS_PATH,
    )
    parser.add_argument(
        "--feature-proof-dir",
        type=Path,
        default=DEFAULT_FEATURE_PROOF_DIR,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(tuple(argv if argv is not None else sys.argv[1:]))
    try:
        report = build_report(
            row_id=args.row_id[-1] if args.row_id else DEFAULT_ROW_ID,
            row_ids=args.row_id,
            scope=args.scope,
            plan_index_path=args.plan_index,
            closure_receipts_path=args.closure_receipts,
            feature_proof_dir=args.feature_proof_dir,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI guardrail
        return emit_runtime_error(command=COMMAND, exc=exc, output_format=args.format)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        print(_render_md(report), end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
