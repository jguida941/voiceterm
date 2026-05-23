"""`devctl receipt-steward audit` action (A38.2 S2)."""

from __future__ import annotations

from typing import Any

from ...common import add_standard_output_arguments
from ...config import REPO_ROOT
from ...runtime.receipt_steward_audit import audit_slice
from ._claim_loader import load_active_claim_for_audit


def add_audit_parser(action_sub: Any) -> None:
    """Register the `audit` sub-action."""
    audit = action_sub.add_parser(
        "audit",
        help="Audit one slice for a paired FeatureProofReceipt.",
    )
    audit.add_argument(
        "--slice-id",
        required=True,
        help="Typed slice id under audit (feature_id or row scope id).",
    )
    audit.add_argument(
        "--plan-row-id",
        required=True,
        help="PlanRow row_id the slice is linked to in plan_index.jsonl.",
    )
    audit.add_argument(
        "--commit-sha",
        required=True,
        help="Commit SHA the slice was applied at; FPR lookup key.",
    )
    audit.add_argument(
        "--store-path",
        default="",
        help="Optional override for the scope-claim JSONL store path.",
    )
    audit.add_argument(
        "--actor-session-id",
        default="receipt-steward-cli",
        help="Actor session id whose claim must be active for this audit.",
    )
    audit.add_argument(
        "--allow-no-claim",
        action="store_true",
        help=(
            "Bypass the active-claim guard. For dogfood/test only — CLI "
            "fails closed in production paths without an active claim."
        ),
    )
    audit.add_argument(
        "--skip-pytest-collect",
        action="store_true",
        help="Skip the optional `pytest --collect-only` resolvability probe.",
    )
    add_standard_output_arguments(
        audit,
        format_choices=("json", "md"),
        default_format="json",
    )


def audit_action(args: Any) -> tuple[dict[str, object], int]:
    """Run one audit and return the typed receipt as a dict + rc."""
    allow_no_claim = bool(getattr(args, "allow_no_claim", False))
    claim, claim_error = load_active_claim_for_audit(args, required=not allow_no_claim)
    if claim_error is not None and not allow_no_claim:
        return (
            {
                "command": "receipt-steward",
                "action": "audit",
                "ok": False,
                "error": claim_error,
            },
            1,
        )

    try:
        receipt = audit_slice(
            slice_id=str(getattr(args, "slice_id", "") or ""),
            plan_row_id=str(getattr(args, "plan_row_id", "") or ""),
            commit_sha=str(getattr(args, "commit_sha", "") or ""),
            repo_root=REPO_ROOT,
            active_claim=claim,
            pytest_collect=not bool(getattr(args, "skip_pytest_collect", False)),
        )
    except ValueError as exc:
        return (
            {
                "command": "receipt-steward",
                "action": "audit",
                "ok": False,
                "error": str(exc),
            },
            1,
        )

    blocking = [
        item for item in receipt.missing_items if item not in {"pytest_node_unresolvable", "dirty_tree_at_audit"}
    ]
    ok = not blocking
    return (
        {
            "command": "receipt-steward",
            "action": "audit",
            "ok": ok,
            "audit_id": receipt.audit_id,
            "slice_id": receipt.slice_id,
            "plan_row_id": receipt.plan_row_id,
            "commit_sha": receipt.commit_sha,
            "audited_at_utc": receipt.audited_at_utc,
            "actor_role": receipt.actor_role,
            "missing_items": list(receipt.missing_items),
            "feature_proof_receipt_path": receipt.feature_proof_receipt_path,
            "targets": receipt.targets.to_dict(),
            "claim_used": claim.claim_id if claim else "",
        },
        0 if ok else 1,
    )


def render_audit_markdown(report: dict[str, object]) -> str:
    lines = ["# devctl receipt-steward audit", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- audit_id: {report.get('audit_id', '')}")
    lines.append(f"- slice_id: {report.get('slice_id', '')}")
    lines.append(f"- plan_row_id: {report.get('plan_row_id', '')}")
    lines.append(f"- commit_sha: {report.get('commit_sha', '')}")
    lines.append(f"- actor_role: {report.get('actor_role', '')}")
    missing = report.get("missing_items") or []
    if missing:
        lines.append("- missing_items:")
        for item in missing:
            lines.append(f"  - {item}")
    else:
        lines.append("- missing_items: (none)")
    targets = report.get("targets")
    if isinstance(targets, dict):
        lines.append("- targets:")
        for key in sorted(targets):
            lines.append(f"  - {key}: {targets[key]}")
    if report.get("error"):
        lines.append(f"- error: {report.get('error')}")
    return "\n".join(lines) + "\n"


__all__ = ["add_audit_parser", "audit_action", "render_audit_markdown"]
