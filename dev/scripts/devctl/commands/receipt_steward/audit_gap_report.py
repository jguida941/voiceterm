"""`devctl receipt-steward audit-gap-report` action (A38.2 S2)."""

from __future__ import annotations

from typing import Any

from ...common import add_standard_output_arguments
from ...config import REPO_ROOT
from ...runtime.receipt_steward_audit import build_audit_gap_report


def add_audit_gap_report_parser(action_sub: Any) -> None:
    """Register the `audit-gap-report` sub-action."""
    parser = action_sub.add_parser(
        "audit-gap-report",
        help=(
            "Report applied/completed PlanRows without a paired "
            "FeatureProofReceipt under dev/reports/feature_proof_receipts/."
        ),
    )
    add_standard_output_arguments(
        parser,
        format_choices=("json", "md"),
        default_format="md",
    )


def audit_gap_report_action(args: Any) -> tuple[dict[str, object], int]:
    """Walk plan_index.jsonl and tag rows with no paired FPR."""
    payload = build_audit_gap_report(repo_root=REPO_ROOT)
    rc = 0 if payload.get("ok") else 1
    report = {
        "command": "receipt-steward",
        "action": "audit-gap-report",
        **payload,
    }
    return report, rc


def render_audit_gap_report_markdown(report: dict[str, object]) -> str:
    lines = ["# devctl receipt-steward audit-gap-report", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- plan_index_path: {report.get('plan_index_path', '')}")
    lines.append(f"- fpr_dir_path: {report.get('fpr_dir_path', '')}")
    lines.append(f"- coverage_pct: {report.get('coverage_pct', 0)}")
    rows_without = report.get("rows_without_receipts") or []
    rows_with = report.get("rows_with_receipts") or []
    lines.append(f"- rows_with_receipts: {len(rows_with) if isinstance(rows_with, list) else 0}")
    lines.append(
        f"- rows_without_receipts: {len(rows_without) if isinstance(rows_without, list) else 0}"
    )
    if isinstance(rows_without, list) and rows_without:
        lines.append("")
        lines.append("## Rows without paired FeatureProofReceipt")
        for row in rows_without[:50]:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {row.get('row_id', '')} (commit {row.get('commit_sha', '')[:12]}, status {row.get('status', '')})"
            )
    if report.get("error"):
        lines.append(f"- error: {report.get('error')}")
    return "\n".join(lines) + "\n"


__all__ = [
    "add_audit_gap_report_parser",
    "audit_gap_report_action",
    "render_audit_gap_report_markdown",
]
