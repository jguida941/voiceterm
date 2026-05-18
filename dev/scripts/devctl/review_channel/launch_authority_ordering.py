"""Typed launch authority ordering for review-channel bootstrap.

This module keeps BypassReceipt validation ahead of projection-only bridge
preconditions. A valid receipt here only bypasses launch preconditions; it is
not commit, push, or raw-git authority.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Mapping

from ..runtime.lifetime_bypass_mode import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    BypassLifecycleState,
    active_bypass_lifecycle_for_receipt_id,
    bypass_receipt_active,
    bypass_receipt_grants_scope,
    load_bypass_lifecycles_with_errors,
)

LAUNCH_BYPASS_SCOPE = "launch_precondition_only"
LAUNCH_AUTHORITY_REPORT_FIELDS = (
    "bypass_receipt_id",
    "bypass_receipt_validated",
    "bridge_gate_bypassed",
    "bypass_scope",
    "rejected_reason",
)


def default_launch_authority_report() -> dict[str, object]:
    """Return the stable structured fields every launch report must carry."""
    return {
        "bypass_receipt_id": "",
        "bypass_receipt_validated": False,
        "bridge_gate_bypassed": False,
        "bypass_scope": "",
        "rejected_reason": "",
    }


def launch_authority_report_from_args(args: object) -> dict[str, object]:
    """Return the report already attached to args, or a default shape."""
    payload = getattr(args, "launch_authority_report", None)
    if isinstance(payload, Mapping):
        report = default_launch_authority_report()
        report.update(
            {
                key: payload.get(key, report[key])
                for key in LAUNCH_AUTHORITY_REPORT_FIELDS
            }
        )
        return report
    report = default_launch_authority_report()
    receipt_id = str(getattr(args, "bypass_receipt_id", "") or "").strip()
    if receipt_id:
        report["bypass_receipt_id"] = receipt_id
    return report


def launch_authority_report_fields(args: object) -> dict[str, object]:
    """Project launch authority fields into success/error reports."""
    return {
        key: launch_authority_report_from_args(args).get(key)
        for key in LAUNCH_AUTHORITY_REPORT_FIELDS
    }


def evaluate_launch_bypass_authority(
    *,
    repo_root: Path | None,
    bypass_receipt_id: str,
    now_utc: datetime | None = None,
) -> dict[str, object]:
    """Validate a launch-precondition bypass receipt before bridge gates."""
    report = default_launch_authority_report()
    receipt_id = str(bypass_receipt_id or "").strip()
    report["bypass_receipt_id"] = receipt_id
    if not receipt_id:
        return report
    if repo_root is None:
        report["rejected_reason"] = "repo_root_unavailable"
        return report

    store_path = repo_root / DEFAULT_BYPASS_LIFECYCLE_STORE_REL
    lifecycle = active_bypass_lifecycle_for_receipt_id(
        receipt_id,
        store_path=store_path,
        required_scope=BypassAuthorityScope.EDIT_ONLY,
        now_utc=now_utc,
    )
    if lifecycle is not None:
        report["bypass_receipt_validated"] = True
        report["bridge_gate_bypassed"] = True
        report["bypass_scope"] = LAUNCH_BYPASS_SCOPE
        report["bypass_lifecycle_id"] = lifecycle.lifecycle_id
        return report

    report["rejected_reason"] = _rejected_reason_for_receipt(
        store_path=store_path,
        receipt_id=receipt_id,
        now_utc=now_utc,
    )
    return report


def require_valid_launch_bypass_if_requested(
    *,
    args: object,
    repo_root: Path | None,
    now_utc: datetime | None = None,
) -> dict[str, object]:
    """Attach launch authority report and reject invalid requested receipts."""
    report = evaluate_launch_bypass_authority(
        repo_root=repo_root,
        bypass_receipt_id=str(getattr(args, "bypass_receipt_id", "") or ""),
        now_utc=now_utc,
    )
    setattr(args, "launch_authority_report", report)
    if report["bypass_receipt_id"] and not report["bypass_receipt_validated"]:
        reason = str(report.get("rejected_reason") or "invalid_receipt")
        raise ValueError(
            "Launch bypass receipt rejected before bridge/projection gates: "
            f"{reason}"
        )
    return report


def launch_bridge_gate_bypassed(report: Mapping[str, object] | None) -> bool:
    """Return whether launch bridge preconditions should be bypassed."""
    return bool(report and report.get("bridge_gate_bypassed"))


def _rejected_reason_for_receipt(
    *,
    store_path: Path,
    receipt_id: str,
    now_utc: datetime | None,
) -> str:
    load_result = load_bypass_lifecycles_with_errors(store_path)
    if load_result.errors:
        return "invalid_receipt_store"
    matching_lifecycle = None
    for lifecycle in load_result.lifecycles:
        if lifecycle.receipt is not None and lifecycle.receipt.receipt_id == receipt_id:
            matching_lifecycle = lifecycle
    if matching_lifecycle is None or matching_lifecycle.receipt is None:
        return "invalid_receipt"
    if matching_lifecycle.state is not BypassLifecycleState.ACTIVE:
        return "inactive_receipt"
    receipt = matching_lifecycle.receipt
    if receipt.revoked_at_utc:
        return "revoked_receipt"
    if not bypass_receipt_active(receipt, now_utc=now_utc):
        return "expired_receipt"
    if not bypass_receipt_grants_scope(receipt, BypassAuthorityScope.EDIT_ONLY):
        return "out_of_scope_receipt"
    return "invalid_receipt"


__all__ = [
    "LAUNCH_AUTHORITY_REPORT_FIELDS",
    "LAUNCH_BYPASS_SCOPE",
    "default_launch_authority_report",
    "evaluate_launch_bypass_authority",
    "launch_authority_report_fields",
    "launch_authority_report_from_args",
    "launch_bridge_gate_bypassed",
    "require_valid_launch_bypass_if_requested",
]
