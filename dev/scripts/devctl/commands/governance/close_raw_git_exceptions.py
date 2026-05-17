"""Close raw-git governed exception lifecycles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ...common import display_path, resolve_repo_path
from ...config import REPO_ROOT
from ...runtime.governed_exception_lifecycle import GovernedExceptionLifecycle
from ...runtime.governed_exception_store import (
    DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL,
    load_governed_exception_lifecycles_with_errors,
)
from ...runtime.governed_exception_validation import pending_lifecycle_status
from ...runtime.raw_git_bypass_lifecycle_closure import (
    close_raw_git_bypass_lifecycle,
    is_open_raw_git_bypass_lifecycle,
    raw_git_receipt_id_for_lifecycle,
)
from ...runtime.raw_git_bypass_receipts import (
    DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL,
    RawGitBypassReceipt,
    read_raw_git_bypass_receipts,
)
from ...runtime.state_store_authority import replace_json_mappings
from ...time_utils import utc_timestamp
from .exceptions_report import base_report

_NORMAL_COMMAND = (
    "python3 dev/scripts/devctl.py exceptions close-raw-git --backfill"
)


def close_raw_git_action(args: Any) -> tuple[dict[str, object], int]:
    """Close open raw-git governed exception rows by commit anchor."""
    store_path = resolve_repo_path(
        getattr(args, "store_path", ""),
        DEFAULT_GOVERNED_EXCEPTION_LIFECYCLE_STORE_REL,
        repo_root=REPO_ROOT,
    )
    receipt_store_path = resolve_repo_path(
        getattr(args, "receipt_store_path", ""),
        DEFAULT_RAW_GIT_BYPASS_RECEIPT_STORE_REL,
        repo_root=REPO_ROOT,
    )
    dry_run = bool(getattr(args, "dry_run", False))
    result = load_governed_exception_lifecycles_with_errors(store_path)
    payload = base_report(
        "close-raw-git",
        store_path=store_path,
        receipt_store_path=receipt_store_path,
    )
    payload["dry_run"] = dry_run
    payload["backfill"] = bool(getattr(args, "backfill", False))
    if result.errors:
        payload["ok"] = False
        payload["errors"] = list(result.errors)
        return payload, 1

    receipts, receipt_errors = _receipt_index(receipt_store_path)
    if receipt_errors:
        payload["ok"] = False
        payload["errors"] = receipt_errors
        return payload, 1

    closed_at_utc = utc_timestamp()
    replacement_rows: list[GovernedExceptionLifecycle] = []
    closed_rows: list[dict[str, object]] = []
    skipped_rows: list[dict[str, object]] = []
    transition_errors: list[str] = []
    open_raw_before = 0

    for lifecycle in result.lifecycles:
        if not is_open_raw_git_bypass_lifecycle(lifecycle):
            replacement_rows.append(lifecycle)
            continue
        open_raw_before += 1
        receipt_id = raw_git_receipt_id_for_lifecycle(lifecycle)
        receipt = receipts.get(receipt_id)
        if receipt is None:
            replacement_rows.append(lifecycle)
            skipped_rows.append(
                {
                    "lifecycle_id": lifecycle.lifecycle_id,
                    "receipt_id": receipt_id,
                    "reason": "raw_git_receipt_not_found",
                }
            )
            continue
        closed, check = close_raw_git_bypass_lifecycle(
            lifecycle,
            receipt=receipt,
            closed_at_utc=closed_at_utc,
            normal_command=_NORMAL_COMMAND,
        )
        if not check.ok:
            replacement_rows.append(lifecycle)
            errors = [error.to_dict() for error in check.errors]
            transition_errors.append(f"{lifecycle.lifecycle_id}:transition_failed")
            skipped_rows.append(
                {
                    "lifecycle_id": lifecycle.lifecycle_id,
                    "receipt_id": receipt_id,
                    "reason": "transition_failed",
                    "transition_check": check.to_dict(),
                    "errors": errors,
                }
            )
            continue
        replacement_rows.append(closed)
        closed_rows.append(
            {
                "lifecycle_id": closed.lifecycle_id,
                "receipt_id": receipt_id,
                "status": closed.status,
                "fixed_by_commit": closed.resolution.fixed_by_commit
                if closed.resolution
                else "",
                "assertions_evaluated": check.assertions_evaluated,
            }
        )

    pending_after = sum(
        1 for lifecycle in replacement_rows if pending_lifecycle_status(lifecycle.status)
    )
    write_result = None
    if not dry_run and closed_rows:
        write_result = replace_json_mappings(
            store_path,
            [lifecycle.to_dict() for lifecycle in replacement_rows],
            store_id="GovernedExceptionLifecycle",
        )

    payload["ok"] = not transition_errors and not skipped_rows
    payload["open_raw_before_count"] = open_raw_before
    payload["closed_count"] = len(closed_rows)
    payload["skipped_count"] = len(skipped_rows)
    payload["pending_after_count"] = pending_after
    payload["closed_lifecycles"] = closed_rows
    payload["skipped_lifecycles"] = skipped_rows
    payload["errors"] = transition_errors
    payload["write_result"] = write_result.to_dict() if write_result else None
    payload["store_path_display"] = display_path(store_path)
    return payload, 0 if payload["ok"] else 1


def _receipt_index(
    receipt_store_path: Path,
) -> tuple[dict[str, RawGitBypassReceipt], list[str]]:
    try:
        receipts = read_raw_git_bypass_receipts(receipt_store_path)
    except (OSError, ValueError) as exc:
        return {}, [f"raw_git_receipt_store_load_failed:{exc}"]
    return {receipt.receipt_id: receipt for receipt in receipts}, []


__all__ = ["close_raw_git_action"]
