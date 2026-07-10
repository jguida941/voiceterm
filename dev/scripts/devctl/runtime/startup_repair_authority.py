"""AuthoritySnapshot-driven startup repair issue helpers."""

from __future__ import annotations

from .startup_context import StartupContext
from .startup_repair_models import StartupRepairIssue


def authority_follow_up_issue(
    *,
    ctx: StartupContext,
    review_issue: StartupRepairIssue | None,
    approval_boundary_active: bool,
    default_command: str,
) -> StartupRepairIssue | None:
    """Project a manual follow-up issue from authority/coordination state."""
    if approval_boundary_active:
        return None
    snapshot = ctx.authority_snapshot
    coordination = ctx.coordination
    if snapshot is not None and bool(snapshot.safe_to_continue):
        return None
    if snapshot is None and not bool(getattr(coordination, "resync_required", False)):
        return None

    issue_id = _issue_id(ctx=ctx)
    duplicate_ids: set[str] = set()
    if review_issue is not None:
        review_issue_id = str(review_issue.issue_id or "").strip()
        if review_issue_id:
            duplicate_ids.add(review_issue_id)
    implementation_block_reason = str(
        ctx.reviewer_gate.implementation_block_reason or ""
    ).strip()
    if implementation_block_reason:
        duplicate_ids.add(implementation_block_reason)
    if issue_id in duplicate_ids:
        return None

    return StartupRepairIssue(
        issue_id=issue_id,
        issue_class="manual_follow_up",
        source="authority_snapshot",
        owner="system",
        summary=_issue_summary(ctx=ctx, issue_id=issue_id),
        detail=_issue_detail(ctx=ctx),
        recommended_command=_issue_command(ctx=ctx, default_command=default_command),
    )


def _issue_id(*, ctx: StartupContext) -> str:
    snapshot = ctx.authority_snapshot
    if snapshot is not None:
        coordination_state = str(snapshot.coordination_state or "").strip()
        if coordination_state == "resync_required":
            return "coordination_resync_required"
        if coordination_state:
            return coordination_state
    if ctx.coordination is not None and bool(ctx.coordination.resync_required):
        return "coordination_resync_required"
    return "authority_blocked"


def _issue_summary(*, ctx: StartupContext, issue_id: str) -> str:
    if issue_id == "coordination_resync_required":
        return "Coordination snapshot requires a resync before another implementation step."
    if issue_id == "handshake_stale":
        return "Authority snapshot reports a stale reviewer/implementer handshake."
    if issue_id == "implementation_blocked":
        return "Authority snapshot blocks implementation until the reviewer state is repaired."
    snapshot = ctx.authority_snapshot
    if snapshot is not None:
        root_cause = str(snapshot.root_cause or "").strip()
        if root_cause:
            return root_cause
    return issue_id.replace("_", " ")


def _issue_detail(*, ctx: StartupContext) -> str:
    detail_parts: list[str] = []
    coordination = ctx.coordination
    snapshot = ctx.authority_snapshot
    if coordination is not None:
        summary = str(coordination.summary or "").strip()
        if summary:
            detail_parts.append(summary)
        resync_reasons = tuple(
            str(item).strip() for item in coordination.resync_reasons if str(item).strip()
        )
        if resync_reasons:
            detail_parts.append(f"resync_reasons={','.join(resync_reasons)}")
    if snapshot is not None:
        required_action = str(snapshot.required_action or "").strip()
        if required_action:
            detail_parts.append(f"required_action={required_action}")
        next_command = str(snapshot.next_command or "").strip()
        if next_command:
            detail_parts.append(f"next_command={next_command}")
    return " | ".join(detail_parts)


def _issue_command(*, ctx: StartupContext, default_command: str) -> str:
    snapshot = ctx.authority_snapshot
    if snapshot is not None:
        command = str(snapshot.next_command or "").strip()
        if command:
            return command
    return default_command
