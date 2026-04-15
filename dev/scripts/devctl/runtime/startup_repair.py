"""Typed startup repair classification for bounded repo-owned recovery."""

from __future__ import annotations

from .review_state_models import ReviewState
from .startup_context import StartupContext
from .startup_repair_authority import authority_follow_up_issue
from .startup_repair_models import (
    StartupRepairActionRecord,
    StartupRepairActionId,
    StartupRepairIssue,
    StartupRepairResult,
)

STARTUP_REPAIR_APPLY_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --repair --apply-safe-fixes --format md"
)
STARTUP_CONTEXT_SUMMARY_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)
REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
_SAFE_FIX_PRIORITY = (
    StartupRepairActionId.ENSURE_RUNTIME.value,
    StartupRepairActionId.RENDER_BRIDGE.value,
    StartupRepairActionId.RESET_IMPLEMENTER_STATE.value,
)


def build_startup_repair_result(
    *,
    ctx: StartupContext,
    authority_report: dict[str, object],
    startup_receipt_path: str,
    review_state: ReviewState | None = None,
    review_error: str | None = None,
    applied_actions: tuple[StartupRepairActionRecord, ...] = (),
) -> StartupRepairResult:
    """Classify startup state into approval, safe-repair, and manual issues."""
    checkpoint_required, safe_to_continue_editing = _push_state(ctx)
    approval_boundary_active = checkpoint_required or not safe_to_continue_editing
    issues = _classified_issues(
        ctx=ctx,
        authority_report=authority_report,
        review_state=review_state,
        review_error=review_error,
        approval_boundary_active=approval_boundary_active,
    )
    review_attention = _review_attention(review_state=review_state, review_error=review_error)
    next_action, next_reason, next_command = _next_step(
        ctx=ctx,
        issues=issues,
        approval_boundary_active=approval_boundary_active,
    )

    governance = ctx.governance
    repo_identity = governance.repo_identity if governance is not None else None
    return StartupRepairResult(
        repo_name=repo_identity.repo_name if repo_identity is not None else "",
        current_branch=repo_identity.current_branch if repo_identity is not None else "",
        startup_receipt_path=startup_receipt_path,
        advisory_action=str(ctx.advisory_action or "").strip(),
        advisory_reason=str(ctx.advisory_reason or "").strip(),
        reviewer_mode=str(ctx.reviewer_gate.reviewer_mode or "").strip() or "single_agent",
        bridge_active=bool(ctx.reviewer_gate.bridge_active),
        startup_authority_ok=bool(authority_report.get("ok", False)),
        checkpoint_required=checkpoint_required,
        safe_to_continue_editing=safe_to_continue_editing,
        review_attention_status=review_attention[0],
        review_attention_owner=review_attention[1],
        review_attention_summary=review_attention[2],
        issue_count=len(issues),
        repairable_issue_count=sum(1 for issue in issues if issue.repairable),
        safe_fix_available_count=sum(1 for issue in issues if issue.safe_to_apply_now),
        issues=issues,
        applied_actions=applied_actions,
        next_action=next_action,
        next_reason=next_reason,
        next_command=next_command,
        ok=not issues,
    )


def select_safe_repair_action(
    result: StartupRepairResult,
    *,
    attempted_actions: tuple[str, ...] = (),
) -> str | None:
    """Return the next safe repair action to try."""
    attempted = set(attempted_actions)
    available = {
        issue.apply_action
        for issue in result.issues
        if issue.safe_to_apply_now and issue.apply_action and issue.apply_action not in attempted
    }
    for action_id in _SAFE_FIX_PRIORITY:
        if action_id in available:
            return action_id
    return None


def _push_state(ctx: StartupContext) -> tuple[bool, bool]:
    governance = ctx.governance
    push = governance.push_enforcement if governance is not None else None
    checkpoint_required = bool(push.checkpoint_required) if push is not None else False
    safe_to_continue_editing = (
        bool(push.safe_to_continue_editing) if push is not None else True
    )
    return checkpoint_required, safe_to_continue_editing


def _classified_issues(
    *,
    ctx: StartupContext,
    authority_report: dict[str, object],
    review_state: ReviewState | None,
    review_error: str | None,
    approval_boundary_active: bool,
) -> tuple[StartupRepairIssue, ...]:
    issues: list[StartupRepairIssue] = []
    if approval_boundary_active:
        issues.append(_approval_boundary_issue(ctx))

    review_issue = _review_issue(
        review_state=review_state,
        review_error=review_error,
        approval_boundary_active=approval_boundary_active,
    )
    if review_issue is not None:
        issues.append(review_issue)

    authority_issue = authority_follow_up_issue(
        ctx=ctx,
        review_issue=review_issue,
        approval_boundary_active=approval_boundary_active,
        default_command=REVIEW_STATUS_COMMAND,
    )
    if authority_issue is not None:
        issues.append(authority_issue)

    if _needs_generic_startup_authority_issue(
        ctx=ctx,
        authority_report=authority_report,
        review_issue=review_issue,
        approval_boundary_active=approval_boundary_active,
    ):
        issues.append(_startup_authority_issue(authority_report))
    return tuple(issues)


def _review_attention(
    *,
    review_state: ReviewState | None,
    review_error: str | None,
) -> tuple[str, str, str]:
    assessment = (
        review_state.recovery_assessment if review_state is not None else None
    )
    if assessment is not None:
        return (
            str(assessment.diagnosis.status or "").strip() or "unknown",
            str(assessment.decision.execution_owner or "").strip() or "system",
            str(assessment.diagnosis.root_cause or "").strip(),
        )
    attention = review_state.attention if review_state is not None else None
    if attention is not None:
        return (
            str(attention.status or "").strip() or "unknown",
            str(attention.owner or "").strip() or "system",
            str(attention.summary or "").strip(),
        )
    if review_error:
        return ("status_unavailable", "system", review_error)
    return ("inactive", "system", "")


def _approval_boundary_issue(ctx: StartupContext) -> StartupRepairIssue:
    push_decision = ctx.push_decision
    recommended_command = str(push_decision.next_step_command or "").strip()
    if not recommended_command:
        recommended_command = (
            "checkpoint current slice, then rerun "
            "python3 dev/scripts/devctl.py startup-context --format summary"
        )
    return StartupRepairIssue(
        issue_id="checkpoint_required",
        issue_class="approval_boundary",
        source="startup_context",
        owner="system",
        summary="Checkpoint required before another implementation or launcher step.",
        detail=str(push_decision.next_step_summary or "").strip(),
        recommended_command=recommended_command,
    )


def _review_issue(
    *,
    review_state: ReviewState | None,
    review_error: str | None,
    approval_boundary_active: bool,
) -> StartupRepairIssue | None:
    if review_error:
        return StartupRepairIssue(
            issue_id="review_channel_status_unavailable",
            issue_class="manual_follow_up",
            source="review_channel",
            owner="system",
            summary="Unable to refresh typed review-channel status during startup repair.",
            detail=review_error,
            recommended_command=REVIEW_STATUS_COMMAND,
        )
    if review_state is None:
        return None

    assessment = review_state.recovery_assessment
    if assessment is None and review_state.attention is None:
        return None

    status = (
        str(assessment.diagnosis.status or "").strip()
        if assessment is not None
        else str(review_state.attention.status or "").strip()
    )
    if status in {"", "healthy", "checkpoint_required"}:
        return None

    action = _attention_safe_fix(status, review_state=review_state)
    changes_tracked_state = action[1] if action is not None else False
    blocked_by_approval_boundary = approval_boundary_active and changes_tracked_state
    summary = (
        str(assessment.diagnosis.root_cause or "").strip()
        if assessment is not None
        else str(review_state.attention.summary or "").strip()
    ) or status.replace("_", " ")
    detail = (
        str(assessment.decision.rationale or "").strip()
        if assessment is not None
        else str(review_state.attention.recommended_action or "").strip()
    )
    if action is None and status in {
        "bridge_contract_error",
        "review_loop_relaunch_required",
    } and review_state.errors:
        detail = str(review_state.errors[0]).strip() or detail
    return StartupRepairIssue(
        issue_id=status,
        issue_class="safe_local_repair" if action is not None else "manual_follow_up",
        source="review_channel",
        owner=(
            str(assessment.decision.execution_owner or "").strip()
            if assessment is not None
            else str(review_state.attention.owner or "").strip()
        )
        or "system",
        summary=summary,
        detail=detail,
        recommended_command=(
            str(assessment.decision.command or "").strip()
            if assessment is not None
            else str(review_state.attention.recommended_command or "").strip()
        ),
        repairable=action is not None,
        safe_to_apply_now=action is not None and not blocked_by_approval_boundary,
        apply_action=action[0] if action is not None else "",
        changes_tracked_state=changes_tracked_state,
        blocked_by_approval_boundary=blocked_by_approval_boundary,
    )
def _attention_safe_fix(
    status: str,
    *,
    review_state: ReviewState,
) -> tuple[str, bool] | None:
    if status in {
        "runtime_missing",
        "publisher_missing",
        "publisher_failed_start",
        "publisher_detached_exit",
        "reviewer_supervisor_required",
    }:
        return (StartupRepairActionId.ENSURE_RUNTIME.value, False)
    if status == "bridge_contract_error":
        if (
            not review_state.bridge.codex_conductor_active
            and not review_state.bridge.claude_conductor_active
        ):
            return None
        return (StartupRepairActionId.RENDER_BRIDGE.value, True)
    if status == "implementer_state_reset_required":
        return (StartupRepairActionId.RESET_IMPLEMENTER_STATE.value, True)
    return None


def _needs_generic_startup_authority_issue(
    *,
    ctx: StartupContext,
    authority_report: dict[str, object],
    review_issue: StartupRepairIssue | None,
    approval_boundary_active: bool,
) -> bool:
    if bool(authority_report.get("ok", False)) or approval_boundary_active:
        return False
    if review_issue is None:
        return True
    return not (
        ctx.reviewer_gate.implementation_blocked
        and str(ctx.reviewer_gate.implementation_block_reason or "").strip()
        == review_issue.issue_id
    )


def _startup_authority_issue(
    authority_report: dict[str, object],
) -> StartupRepairIssue:
    errors = [
        str(row).strip()
        for row in authority_report.get("errors", ())
        if str(row).strip()
    ]
    warnings = [
        str(row).strip()
        for row in authority_report.get("warnings", ())
        if str(row).strip()
    ]
    detail_parts = errors[:3]
    if warnings:
        detail_parts.extend(f"warning: {warning}" for warning in warnings[:2])
    return StartupRepairIssue(
        issue_id="startup_authority_failure",
        issue_class="manual_follow_up",
        source="startup_authority",
        owner="system",
        summary=errors[0] if errors else "Startup authority reported a blocking failure.",
        detail=" | ".join(detail_parts),
        recommended_command=STARTUP_CONTEXT_SUMMARY_COMMAND,
    )


def _next_step(
    *,
    ctx: StartupContext,
    issues: tuple[StartupRepairIssue, ...],
    approval_boundary_active: bool,
) -> tuple[str, str, str]:
    if approval_boundary_active:
        command = str(ctx.push_decision.next_step_command or "").strip()
        if not command:
            command = (
                "checkpoint current slice, then rerun "
                "python3 dev/scripts/devctl.py startup-context --format summary"
            )
        return (
            "approval_required",
            "Checkpoint budget is already red; do not widen the slice before a checkpoint.",
            command,
        )
    if any(issue.safe_to_apply_now for issue in issues):
        return (
            "apply_safe_fixes",
            "Repo-owned safe fixes are available for the current startup state.",
            STARTUP_REPAIR_APPLY_COMMAND,
        )
    if issues:
        issue = issues[0]
        return ("manual_follow_up", issue.summary, issue.recommended_command)
    return (
        "healthy",
        "Startup state is healthy; no bounded repair action is required.",
        STARTUP_CONTEXT_SUMMARY_COMMAND,
    )
