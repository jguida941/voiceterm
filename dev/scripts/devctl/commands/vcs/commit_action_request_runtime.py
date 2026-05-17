"""Runtime glue for packet-authorized governed commits."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .commit_action_request_lifecycle import (
    apply_commit_action_request_packet,
    record_commit_action_request_apply_pending,
    record_commit_action_request_execution_failure,
)


def emit_action_request_block_report(
    *,
    args,
    repo_root: Path,
    grant,
    report: dict[str, object],
    reason: str,
    emit_report,
) -> None:
    """Record packet execution failure before emitting a blocked report."""
    if grant is None:
        emit_report(args, report)
        return
    try:
        record_commit_action_request_execution_failure(
            repo_root=repo_root,
            grant=grant,
            reason=reason,
        )
        grant = replace(
            grant,
            lifecycle_state="failed",
            execution_failure_reason=reason,
        )
    except (OSError, ValueError) as exc:
        warnings = list(report.get("warnings") or [])
        warnings.append(f"action_request_execution_failure_receipt_error: {exc}")
        report["warnings"] = warnings
    report["action_request_authority"] = grant.to_dict()
    emit_report(args, report)


def finalize_commit_action_request(
    *,
    repo_root: Path,
    grant,
    pipeline,
    commit_result,
    commit_sha: str,
) -> tuple[object, str, str, bool]:
    """Apply or mark failure for the action_request after commit execution."""
    if grant is None:
        return grant, commit_result.reason, "", True
    if not commit_result.ok:
        record_commit_action_request_execution_failure(
            repo_root=repo_root,
            grant=grant,
            reason=commit_result.reason,
        )
        return (
            replace(
                grant,
                lifecycle_state="failed",
                execution_failure_reason=commit_result.reason,
            ),
            commit_result.reason,
            "",
            False,
        )
    try:
        apply_event = apply_commit_action_request_packet(
            repo_root=repo_root,
            grant=grant,
            pipeline=pipeline,
            commit_result=commit_result,
            commit_sha=commit_sha,
        )
    except (OSError, ValueError) as exc:
        reason = _record_apply_pending(repo_root=repo_root, grant=grant, error=exc)
        return (
            replace(
                grant,
                lifecycle_state="apply_pending_after_execution",
                apply_pending_reason=reason,
            ),
            "action_request_apply_pending_after_execution",
            reason,
            False,
        )
    return (
        replace(
            grant,
            apply_event_id=str(apply_event.get("event_id") or ""),
            lifecycle_state="applied",
        ),
        commit_result.reason,
        "",
        True,
    )


def _record_apply_pending(*, repo_root: Path, grant, error: Exception) -> str:
    reason = str(error)
    try:
        record_commit_action_request_apply_pending(
            repo_root=repo_root,
            grant=grant,
            reason=reason,
        )
    except (OSError, ValueError) as receipt_exc:
        reason = f"{reason}; apply_pending_receipt_error={receipt_exc}"
    return reason
