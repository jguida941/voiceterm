"""`devctl receipt-steward audit-recent` action (A38.2 S2)."""

from __future__ import annotations

from typing import Any

from ...common import add_standard_output_arguments
from ...config import REPO_ROOT
from ...runtime.receipt_steward_audit import audit_recent_commits
from ._claim_loader import load_active_claim_for_audit


def add_audit_recent_parser(action_sub: Any) -> None:
    """Register the `audit-recent` sub-action."""
    audit_recent = action_sub.add_parser(
        "audit-recent",
        help="Audit the most recent N commits walking back from HEAD.",
    )
    audit_recent.add_argument(
        "--since-commit",
        default="",
        help="Stop walking at this commit (exclusive). Empty walks `limit` from HEAD.",
    )
    audit_recent.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of commits to audit (default 5).",
    )
    audit_recent.add_argument(
        "--store-path",
        default="",
        help="Optional override for the scope-claim JSONL store path.",
    )
    audit_recent.add_argument(
        "--actor-session-id",
        default="receipt-steward-cli",
        help="Actor session id whose claim must be active for this audit.",
    )
    audit_recent.add_argument(
        "--allow-no-claim",
        action="store_true",
        help="Bypass the active-claim guard (dogfood/test only).",
    )
    add_standard_output_arguments(
        audit_recent,
        format_choices=("json", "md"),
        default_format="json",
    )


def audit_recent_action(args: Any) -> tuple[dict[str, object], int]:
    """Audit recent commits and emit one row per audit."""
    allow_no_claim = bool(getattr(args, "allow_no_claim", False))
    claim, claim_error = load_active_claim_for_audit(args, required=not allow_no_claim)
    if claim_error is not None and not allow_no_claim:
        return (
            {
                "command": "receipt-steward",
                "action": "audit-recent",
                "ok": False,
                "error": claim_error,
            },
            1,
        )
    receipts = audit_recent_commits(
        repo_root=REPO_ROOT,
        since_commit=str(getattr(args, "since_commit", "") or ""),
        limit=int(getattr(args, "limit", 5) or 5),
        pytest_collect=False,
    )
    rows: list[dict[str, object]] = []
    any_blocking = False
    for receipt in receipts:
        blocking = [
            item
            for item in receipt.missing_items
            if item not in {"pytest_node_unresolvable", "dirty_tree_at_audit"}
        ]
        if blocking:
            any_blocking = True
        rows.append(
            {
                "audit_id": receipt.audit_id,
                "slice_id": receipt.slice_id,
                "plan_row_id": receipt.plan_row_id,
                "commit_sha": receipt.commit_sha,
                "missing_items": list(receipt.missing_items),
                "feature_proof_receipt_path": receipt.feature_proof_receipt_path,
                "targets_status": receipt.targets.status,
            }
        )
    return (
        {
            "command": "receipt-steward",
            "action": "audit-recent",
            "ok": not any_blocking,
            "claim_used": claim.claim_id if claim else "",
            "since_commit": str(getattr(args, "since_commit", "") or ""),
            "limit": int(getattr(args, "limit", 5) or 5),
            "rows": rows,
        },
        0,
    )


def render_audit_recent_markdown(report: dict[str, object]) -> str:
    lines = ["# devctl receipt-steward audit-recent", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- since_commit: {report.get('since_commit', '')}")
    lines.append(f"- limit: {report.get('limit', 0)}")
    rows = report.get("rows") or []
    if isinstance(rows, list):
        for row in rows:
            commit = row.get("commit_sha", "")[:12] if isinstance(row, dict) else ""
            missing = (
                ",".join(row.get("missing_items") or [])
                if isinstance(row, dict)
                else ""
            ) or "(clean)"
            lines.append(
                f"- {commit}: missing=[{missing}] status={row.get('targets_status', '') if isinstance(row, dict) else ''}"
            )
    if report.get("error"):
        lines.append(f"- error: {report.get('error')}")
    return "\n".join(lines) + "\n"


__all__ = [
    "add_audit_recent_parser",
    "audit_recent_action",
    "render_audit_recent_markdown",
]
