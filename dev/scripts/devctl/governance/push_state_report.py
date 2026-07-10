"""Push-report helpers for push-state detection."""

from __future__ import annotations


def current_target_remote(*, upstream_ref: str, default_remote: str) -> str:
    """Return the publish remote implied by the current upstream or policy default."""
    if "/" in upstream_ref:
        return upstream_ref.split("/", 1)[0]
    return default_remote


def latest_push_report_approved_target_identity(
    report: dict[str, object],
) -> str:
    """Return the approved target identity carried by one push report."""
    direct_value = str(report.get("approved_target_identity") or "").strip()
    if direct_value:
        return direct_value
    typed_action = report.get("typed_action")
    if not isinstance(typed_action, dict):
        return ""
    parameters = typed_action.get("parameters")
    if not isinstance(parameters, dict):
        return ""
    return str(parameters.get("approved_target_identity") or "").strip()


def latest_push_report_approved_worktree_identity(
    report: dict[str, object],
) -> str:
    """Return the approved worktree identity carried by one push report."""
    direct_value = str(report.get("approved_worktree_identity") or "").strip()
    if direct_value:
        return direct_value
    typed_action = report.get("typed_action")
    if not isinstance(typed_action, dict):
        return ""
    parameters = typed_action.get("parameters")
    if not isinstance(parameters, dict):
        return ""
    return str(parameters.get("approved_worktree_identity") or "").strip()


def latest_push_report_state(
    *,
    report: dict[str, object],
    current_branch: str,
    current_head_commit: str,
    current_approved_target_identity: str,
    current_worktree_identity: str,
) -> tuple[str, str, str, str, str, bool, bool, bool, bool]:
    """Return the current-branch/head/identity parity summary for one push report."""
    branch = str(report.get("branch") or "").strip()
    remote = str(report.get("remote") or "").strip()
    head_commit = str(report.get("head_commit") or "").strip()
    approved_target_identity = latest_push_report_approved_target_identity(report)
    approved_worktree_identity = latest_push_report_approved_worktree_identity(report)
    return (
        branch,
        remote,
        head_commit,
        approved_target_identity,
        approved_worktree_identity,
        bool(current_branch and branch and current_branch == branch),
        bool(current_head_commit and head_commit and current_head_commit == head_commit),
        bool(
            (
                not current_approved_target_identity
                and not approved_target_identity
            )
            or (
                current_approved_target_identity
                and approved_target_identity
                and current_approved_target_identity == approved_target_identity
            )
        ),
        bool(
            not approved_worktree_identity
            or (
                current_worktree_identity
                and current_worktree_identity == approved_worktree_identity
            )
        ),
    )
