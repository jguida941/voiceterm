"""Push/checkpoint rendering helpers for startup-context markdown surfaces."""

from __future__ import annotations

from ...runtime.project_governance_push import push_enforcement_from_mapping
from ...runtime.startup_push_recovery import (
    artifact_publication_truth,
    artifact_push_in_progress_for_current_head,
    effective_publication_summary,
)

_DEVCTL_PUSH_EXECUTE_COMMAND = "python3 dev/scripts/devctl.py push --execute"


def _push_decision_mapping(ctx_dict: dict) -> dict:
    push_decision = ctx_dict.get("push_decision")
    return push_decision if isinstance(push_decision, dict) else {}


def _push_enforcement_mapping(ctx_dict: dict) -> dict:
    governance = ctx_dict.get("governance")
    push_enforcement = governance.get("push_enforcement") if isinstance(governance, dict) else None
    return push_enforcement if isinstance(push_enforcement, dict) else {}


def _publication_backlog_mapping(ctx_dict: dict) -> dict:
    push_decision = _push_decision_mapping(ctx_dict)
    backlog = push_decision.get("publication_backlog")
    if isinstance(backlog, dict):
        return backlog
    push_enforcement = _push_enforcement_mapping(ctx_dict)
    if not push_enforcement:
        return {}
    return {
        "pending_publication_commits": push_enforcement.get(
            "pending_publication_commits"
        ),
        "backlog_state": push_enforcement.get("publication_backlog_state"),
        "backlog_summary": push_enforcement.get("publication_backlog_summary"),
        "backlog_recommended": push_enforcement.get(
            "publication_backlog_recommended"
        ),
        "backlog_urgent": push_enforcement.get("publication_backlog_urgent"),
    }


def publication_backlog_count(ctx_dict: dict) -> int | None:
    """Return ahead-of-upstream count when startup can see one."""
    backlog = _publication_backlog_mapping(ctx_dict)
    raw_count = backlog.get("pending_publication_commits")
    if isinstance(raw_count, int):
        return raw_count
    if isinstance(raw_count, str) and raw_count.isdigit():
        return int(raw_count)
    push_enforcement = _push_enforcement_mapping(ctx_dict)
    if not push_enforcement:
        return None
    raw_count = push_enforcement.get("ahead_of_upstream_commits")
    if isinstance(raw_count, int):
        return raw_count
    if isinstance(raw_count, str) and raw_count.isdigit():
        return int(raw_count)
    return None


def _append_latest_push_receipt(lines: list[str], push_enforcement: dict) -> None:
    latest_push_path = str(push_enforcement.get("latest_push_report_path") or "").strip()
    latest_push_status = str(push_enforcement.get("latest_push_report_status") or "").strip()
    latest_push_reason = str(push_enforcement.get("latest_push_report_reason") or "").strip()
    if not (latest_push_path or latest_push_status or latest_push_reason):
        return
    push_record = push_enforcement_from_mapping(push_enforcement)
    published_remote, post_push_green = artifact_publication_truth(push_record)
    if artifact_push_in_progress_for_current_head(push_record):
        effective_state = "Governed push in progress for current HEAD"
    else:
        effective_state = effective_publication_summary(
            published_remote,
            post_push_green,
        )
    lines.append(f"- effective_publication_state: {effective_state}")
    lines.append(f"- published_remote: {published_remote}")
    lines.append(f"- post_push_green: {post_push_green}")
    if latest_push_status:
        lines.append(f"- latest_push_status: `{latest_push_status}`")
    if latest_push_reason:
        lines.append(f"- latest_push_reason: `{latest_push_reason}`")
    lines.append("")
    lines.append("#### Diagnostic: raw push-report booleans")
    lines.append(f"- latest_push_report: `{latest_push_path or 'n/a'}`")
    for label, value in (
        (
            "latest_push_matches_current_branch",
            bool(push_enforcement.get("latest_push_report_matches_current_branch")),
        ),
        (
            "latest_push_matches_current_head",
            bool(push_enforcement.get("latest_push_report_matches_current_head")),
        ),
        (
            "latest_push_matches_current_approved_target",
            bool(push_enforcement.get("latest_push_report_matches_current_approved_target")),
        ),
        (
            "latest_push_report_published_remote",
            bool(push_enforcement.get("latest_push_report_published_remote")),
        ),
        ("latest_push_receipt_current", published_remote),
    ):
        lines.append(f"- {label}: {value}")


def publication_backlog_guidance(ctx_dict: dict) -> str:
    """Describe when pending remote publication should happen."""
    push_decision = _push_decision_mapping(ctx_dict)
    if not push_decision:
        return ""
    guidance = str(push_decision.get("publication_guidance") or "").strip()
    if guidance:
        return guidance
    if not bool(push_decision.get("has_remote_work_to_push", False)):
        return ""
    ahead = publication_backlog_count(ctx_dict)
    if ahead is not None and ahead > 0:
        subject = f"{ahead} local commit(s) waiting for governed push"
    else:
        subject = "Local branch still has unpublished work waiting for governed push"
    if bool(push_decision.get("push_eligible_now", False)):
        return f"{subject}. Run `{_DEVCTL_PUSH_EXECUTE_COMMAND}` now."
    action = str(push_decision.get("action") or "").strip()
    if action == "await_review":
        return f"{subject} once review is accepted."
    if action == "await_checkpoint":
        return f"{subject} once the current slice is checkpoint-clean."
    return f"{subject} after the current startup blocker clears."


def append_push_state(lines: list[str], ctx_dict: dict) -> None:
    push_enforcement = _push_enforcement_mapping(ctx_dict)
    if not push_enforcement:
        return
    lines.append("## Push/Checkpoint State")
    _append_latest_push_receipt(lines, push_enforcement)
    lines.append(f"- worktree_dirty: {push_enforcement.get('worktree_dirty', False)}")
    lines.append(f"- worktree_clean: {push_enforcement.get('worktree_clean', True)}")
    lines.append(f"- staged_path_count: {push_enforcement.get('staged_path_count', 0)}")
    lines.append(
        f"- unstaged_path_count: {push_enforcement.get('unstaged_path_count', 0)}"
    )
    ahead = publication_backlog_count(ctx_dict)
    if ahead is not None:
        lines.append(f"- ahead_of_upstream_commits: {ahead}")
    lines.append(f"- checkpoint_required: {push_enforcement.get('checkpoint_required', False)}")
    lines.append(f"- safe_to_continue_editing: {push_enforcement.get('safe_to_continue_editing', True)}")
    lines.append(f"- recommended_action: `{push_enforcement.get('recommended_action', '?')}`")
    backlog_state = str(push_enforcement.get("publication_backlog_state") or "").strip()
    if backlog_state:
        lines.append(f"- publication_backlog_state: `{backlog_state}`")
    backlog_summary = str(
        push_enforcement.get("publication_backlog_summary") or ""
    ).strip()
    if backlog_summary:
        lines.append(f"- publication_backlog_summary: {backlog_summary}")
    backlog_guidance = publication_backlog_guidance(ctx_dict)
    if backlog_guidance:
        lines.append(f"- publication_backlog: {backlog_guidance}")
    lines.append("")


def append_push_decision(
    lines: list[str],
    push_decision: dict,
    *,
    append_rule_explanation_fn,
) -> None:
    if not push_decision:
        return
    lines.append("## Push Decision")
    lines.append(f"- action: `{push_decision.get('action', '?')}`")
    lines.append(f"- reason: `{push_decision.get('reason', '')}`")
    lines.append(
        f"- push_eligible_now: {push_decision.get('push_eligible_now', False)}"
    )
    lines.append(
        "- has_remote_work_to_push: "
        f"{push_decision.get('has_remote_work_to_push', False)}"
    )
    next_step_summary = str(push_decision.get("next_step_summary") or "").strip()
    next_step_command = str(push_decision.get("next_step_command") or "").strip()
    publication_state = str(
        _publication_backlog_mapping({"push_decision": push_decision}).get(
            "backlog_state"
        )
        or ""
    ).strip()
    if publication_state:
        lines.append(f"- publication_backlog_state: `{publication_state}`")
    publication_guidance = str(push_decision.get("publication_guidance") or "").strip()
    if publication_guidance:
        lines.append(f"- publication_guidance: {publication_guidance}")
    if next_step_summary:
        lines.append(f"- next_step_summary: {next_step_summary}")
    if next_step_command:
        lines.append(f"- next_step_command: `{next_step_command}`")
    append_rule_explanation_fn(
        lines,
        push_decision,
        summary_label="push_rule_summary",
    )
    lines.append("")
