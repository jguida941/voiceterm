#!/usr/bin/env python3
"""Validate governed PlanRows have commit and typed ingestion evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, emit_runtime_error

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dev.scripts.devctl.runtime.plan_intent_ingestion import (  # noqa: E402
    PLAN_INTENT_INGESTION_RECEIPT_STORE_REL,
    PLAN_INTENT_RECEIPT_REF_PREFIX,
    TYPED_ACTION_REF_PREFIX,
    read_plan_intent_ingestion_receipts,
)
from dev.scripts.devctl.runtime.repo_portability import (  # noqa: E402
    GuardMandate,
    resolve_guard_mandate,
)

COMMAND = "check_plan_index_commit_continuity"
DEFAULT_PLAN_INDEX_REL = "dev/state/plan_index.jsonl"
ENFORCED_MUTATION_OPS = (
    "guard_discovery_build_loop_charter",
    "task_started_packet_binding",
)
CONTINUITY_MUTATION_SUFFIXES = ("_applied",)
ENFORCED_PACKET_BINDING_SUFFIX = "_packet_binding"


class PlanIndexContinuityGap(NamedTuple):
    line_number: int
    row_id: str
    scope: str
    missing: tuple[str, ...]
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "line_number": self.line_number,
            "row_id": self.row_id,
            "scope": self.scope,
            "missing": list(self.missing),
            "detail": self.detail,
        }


def evaluate_plan_index_commit_continuity(
    *,
    repo_root: Path = REPO_ROOT,
    plan_index_path: Path | None = None,
    receipt_path: Path | None = None,
    strict_legacy: bool = False,
) -> dict[str, object]:
    """Return continuity evidence for governed plan rows.

    The repo-policy mandate window is forward-enforcing: configured row
    prefixes and rows observed after the mandate fail when they require
    lifecycle continuity without the full proof triple. Older applied rows are
    still surfaced as legacy gaps so the backlog is visible without blocking
    the guard landing commit.
    """
    resolved_path = plan_index_path or repo_root / DEFAULT_PLAN_INDEX_REL
    resolved_receipt_path = (
        receipt_path or repo_root / PLAN_INTENT_INGESTION_RECEIPT_STORE_REL
    )
    rows, load_errors = _read_rows(resolved_path)
    receipts = read_plan_intent_ingestion_receipts(resolved_receipt_path)
    mandate = resolve_guard_mandate(COMMAND, repo_root=repo_root)
    receipts_by_id = {
        _text(receipt.get("receipt_id")): receipt
        for receipt in receipts
        if _text(receipt.get("receipt_id"))
    }
    enforced_gaps: list[PlanIndexContinuityGap] = []
    legacy_gaps: list[PlanIndexContinuityGap] = []
    applied_count = 0
    enforced_applied_count = 0
    continuity_row_count = 0
    enforced_row_count = 0

    for line_number, row in rows:
        if not _row_requires_continuity(row):
            continue
        continuity_row_count += 1
        row_is_applied = _text(row.get("status")) == "applied"
        if row_is_applied:
            applied_count += 1
        enforced = _row_is_enforced(row, mandate=mandate)
        if enforced:
            enforced_row_count += 1
            if row_is_applied:
                enforced_applied_count += 1
        missing = _missing_proof_refs(row, receipts_by_id=receipts_by_id)
        if not missing:
            continue
        scope = "enforced" if enforced or strict_legacy else "legacy"
        gap = PlanIndexContinuityGap(
            line_number=line_number,
            row_id=_text(row.get("row_id")) or f"line:{line_number}",
            scope=scope,
            missing=missing,
            detail=(
                "Governed PlanRows must carry commit anchor_refs plus "
                "PlanIntentReceipt and TypedAction work evidence."
            ),
        )
        if scope == "enforced":
            enforced_gaps.append(gap)
        else:
            legacy_gaps.append(gap)

    violations = tuple(enforced_gaps)
    return {
        "command": COMMAND,
        "schema_version": 1,
        "ok": not load_errors and not violations,
        "plan_index_path": _display_path(resolved_path, repo_root=repo_root),
        "receipt_path": _display_path(resolved_receipt_path, repo_root=repo_root),
        "mandate_packet_id": mandate.mandate_packet_id,
        "mandate_observed_at_utc": mandate.observed_at_utc,
        "mandate_policy_path": mandate.policy_path,
        "mandate_policy_warnings": list(mandate.warnings),
        "enforced_row_prefixes": mandate.enforced_row_prefixes,
        "strict_legacy": strict_legacy,
        "row_count": len(rows),
        "receipt_count": len(receipts),
        "continuity_row_count": continuity_row_count,
        "enforced_row_count": enforced_row_count,
        "applied_row_count": applied_count,
        "enforced_applied_row_count": enforced_applied_count,
        "violation_count": len(violations),
        "legacy_gap_count": len(legacy_gaps),
        "violations": [gap.to_dict() for gap in violations],
        "legacy_gaps": [gap.to_dict() for gap in legacy_gaps],
        "errors": load_errors,
    }


def _read_rows(path: Path) -> tuple[list[tuple[int, dict[str, Any]]], list[str]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"plan_index_read_failed:{exc.__class__.__name__}:{path}"]
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid_jsonl:{line_number}:{exc.msg}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"non_object_row:{line_number}")
            continue
        rows.append((line_number, payload))
    return rows, errors


def _missing_proof_refs(
    row: dict[str, Any],
    *,
    receipts_by_id: dict[str, dict[str, object]],
) -> tuple[str, ...]:
    row_id = _text(row.get("row_id"))
    anchor_refs = _refs(row.get("anchor_refs"))
    work_evidence_ids = _refs(row.get("work_evidence_ids"))
    missing: list[str] = []
    if not _has_prefix(anchor_refs, "commit:"):
        missing.append("commit_anchor_ref")
    receipt_ids = _suffixes(work_evidence_ids, PLAN_INTENT_RECEIPT_REF_PREFIX)
    action_ids = _suffixes(work_evidence_ids, TYPED_ACTION_REF_PREFIX)
    if not receipt_ids:
        missing.append("plan_intent_receipt_ref")
    if not action_ids:
        missing.append("typed_action_ref")
    if receipt_ids and action_ids:
        receipt_status = _matching_receipt_status(
            row_id=row_id,
            receipt_ids=receipt_ids,
            action_ids=action_ids,
            receipts_by_id=receipts_by_id,
        )
        if receipt_status:
            missing.append(receipt_status)
    return tuple(missing)


def _suffixes(values: tuple[str, ...], prefix: str) -> tuple[str, ...]:
    return tuple(value[len(prefix) :] for value in values if value.startswith(prefix))


def _matching_receipt_status(
    *,
    row_id: str,
    receipt_ids: tuple[str, ...],
    action_ids: tuple[str, ...],
    receipts_by_id: dict[str, dict[str, object]],
) -> str:
    receipt_missing = False
    receipt_not_accepted = False
    row_mismatch = False
    action_mismatch = False
    for receipt_id in receipt_ids:
        receipt = receipts_by_id.get(receipt_id)
        if receipt is None:
            receipt_missing = True
            continue
        if _text(receipt.get("status")) != "accepted":
            receipt_not_accepted = True
            continue
        if _text(receipt.get("target_kind")) != "plan_row":
            row_mismatch = True
            continue
        if row_id not in _refs(receipt.get("row_ids")):
            row_mismatch = True
            continue
        if _text(receipt.get("action_id")) not in action_ids:
            action_mismatch = True
            continue
        return ""
    if receipt_missing:
        return "receipt_not_found"
    if receipt_not_accepted:
        return "receipt_not_accepted"
    if row_mismatch:
        return "receipt_row_mismatch"
    if action_mismatch:
        return "typed_action_mismatch"
    return "receipt_not_found"


def _row_is_enforced(row: dict[str, Any], *, mandate: GuardMandate) -> bool:
    row_id = _text(row.get("row_id"))
    if mandate.enforced_row_prefixes and row_id.startswith(
        mandate.enforced_row_prefixes
    ):
        return True
    mutation_op = _text(row.get("mutation_op"))
    if mutation_op in ENFORCED_MUTATION_OPS:
        return True
    if _packet_binding_op_requires_continuity(row):
        return True
    refs = (*_refs(row.get("anchor_refs")), *_refs(row.get("work_evidence_ids")))
    if mandate.mandate_packet_id and f"packet:{mandate.mandate_packet_id}" in refs:
        return True
    observed_at = _text(_mapping(row.get("provenance")).get("observed_at_utc"))
    return _timestamp_is_enforced(observed_at, mandate=mandate)


def _row_requires_continuity(row: dict[str, Any]) -> bool:
    if _text(row.get("status")) == "applied":
        return True
    mutation_op = _text(row.get("mutation_op"))
    return (
        mutation_op in ENFORCED_MUTATION_OPS
        or mutation_op.endswith(CONTINUITY_MUTATION_SUFFIXES)
        or _packet_binding_op_requires_continuity(row)
    )


def _packet_binding_op_requires_continuity(row: dict[str, Any]) -> bool:
    mutation_op = _text(row.get("mutation_op"))
    if not mutation_op.endswith(ENFORCED_PACKET_BINDING_SUFFIX):
        return False
    refs = (*_refs(row.get("sourced_from_packets")), *_refs(row.get("anchor_refs")))
    return any(ref.startswith("rev_pkt_") or ref.startswith("packet:rev_pkt_") for ref in refs)


def _refs(value: object) -> tuple[str, ...]:
    if isinstance(value, list | tuple):
        return tuple(_text(item) for item in value if _text(item))
    return ()


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _has_prefix(values: tuple[str, ...], prefix: str) -> bool:
    return any(value.startswith(prefix) for value in values)


def _normalize_timestamp(value: str) -> str:
    return value.replace("+00:00", "Z")


def _timestamp_is_enforced(value: str, *, mandate: GuardMandate) -> bool:
    if not value or not mandate.observed_at_utc:
        return False
    return _normalize_timestamp(value) >= _normalize_timestamp(mandate.observed_at_utc)


def _text(value: object) -> str:
    return str(value or "").strip()


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def render_markdown(report: dict[str, object]) -> str:
    lines = ["# check_plan_index_commit_continuity", ""]
    for key in (
        "ok",
        "plan_index_path",
        "receipt_path",
        "mandate_packet_id",
        "strict_legacy",
        "row_count",
        "receipt_count",
        "continuity_row_count",
        "enforced_row_count",
        "applied_row_count",
        "enforced_applied_row_count",
        "violation_count",
        "legacy_gap_count",
    ):
        lines.append(f"- {key}: {report[key]}")
    errors = report.get("errors") or []
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {error}" for error in errors)
    violations = report.get("violations") or []
    if violations:
        lines.extend(["", "## Violations"])
        for gap in violations:
            lines.append(
                f"- line {gap['line_number']} `{gap['row_id']}` missing "
                f"{', '.join(gap['missing'])}"
            )
    legacy_gaps = report.get("legacy_gaps") or []
    if legacy_gaps:
        lines.extend(["", "## Legacy Gaps"])
        for gap in legacy_gaps:
            lines.append(
                f"- line {gap['line_number']} `{gap['row_id']}` missing "
                f"{', '.join(gap['missing'])}"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-index", default=DEFAULT_PLAN_INDEX_REL)
    parser.add_argument(
        "--receipt-path",
        default=PLAN_INTENT_INGESTION_RECEIPT_STORE_REL,
    )
    parser.add_argument(
        "--strict-legacy",
        action="store_true",
        help="Fail historical applied rows that predate the configured mandate.",
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = evaluate_plan_index_commit_continuity(
            repo_root=REPO_ROOT,
            plan_index_path=REPO_ROOT / args.plan_index,
            receipt_path=REPO_ROOT / args.receipt_path,
            strict_legacy=args.strict_legacy,
        )
    # broad-except: allow reason=defensive-cli-boundary fallback=emit-runtime-error
    except Exception as exc:  # pragma: no cover - defensive CLI boundary.
        emit_runtime_error(COMMAND, exc)
        return 1
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report), end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
