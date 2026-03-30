"""Repo-owned startup repair facade for `startup-context --repair`."""

from __future__ import annotations

from ...config import REPO_ROOT
from ...runtime.startup_repair import StartupRepairActionRecord, StartupRepairResult
from ...runtime.startup_repair import select_safe_repair_action
from .common import emit_governance_command_output, render_governance_value_error
from .startup_repair_runtime import (
    apply_safe_repair_action as _apply_safe_repair_action,
)
from .startup_repair_runtime import collect_state as _collect_state

_MAX_SAFE_FIX_ATTEMPTS = 3


def _render_markdown(result: StartupRepairResult) -> str:
    lines = ["# devctl startup-context --repair", ""]
    lines.append(f"- repo: {result.repo_name or '(unknown)'}")
    lines.append(f"- branch: {result.current_branch or '(unknown)'}")
    lines.append(f"- advisory_action: {result.advisory_action or '(unknown)'}")
    lines.append(f"- advisory_reason: {result.advisory_reason or '(unknown)'}")
    lines.append(f"- startup_authority_ok: {result.startup_authority_ok}")
    lines.append(f"- checkpoint_required: {result.checkpoint_required}")
    lines.append(f"- safe_to_continue_editing: {result.safe_to_continue_editing}")
    lines.append(f"- bridge_active: {result.bridge_active}")
    lines.append(f"- reviewer_mode: {result.reviewer_mode}")
    lines.append(f"- review_attention_status: {result.review_attention_status}")
    lines.append(f"- issue_count: {result.issue_count}")
    lines.append(f"- repairable_issue_count: {result.repairable_issue_count}")
    lines.append(f"- safe_fix_available_count: {result.safe_fix_available_count}")
    lines.append(
        f"- startup_receipt_path: {result.startup_receipt_path or '(not written)'}"
    )
    if result.review_attention_summary:
        lines.append(f"- review_attention_summary: {result.review_attention_summary}")

    _append_issue_lines(lines, result)
    _append_applied_action_lines(lines, result.applied_actions)
    lines.extend(["", "## Next step"])
    lines.append(f"- action: {result.next_action}")
    lines.append(f"- reason: {result.next_reason}")
    if result.next_command:
        lines.append(f"- command: `{result.next_command}`")
    return "\n".join(lines)


def _append_issue_lines(lines: list[str], result: StartupRepairResult) -> None:
    if not result.issues:
        return
    lines.extend(["", "## Issues"])
    for issue in result.issues:
        line = (
            f"- [{issue.issue_class}] `{issue.issue_id}` ({issue.source}/{issue.owner}): "
            f"{issue.summary}"
        )
        if issue.safe_to_apply_now:
            line += f" | safe_fix={issue.apply_action}"
        elif issue.repairable and issue.blocked_by_approval_boundary:
            line += f" | safe_fix={issue.apply_action} blocked_by=approval_boundary"
        lines.append(line)
        if issue.detail:
            lines.append(f"  detail: {issue.detail}")
        if issue.recommended_command:
            lines.append(f"  command: `{issue.recommended_command}`")


def _append_applied_action_lines(
    lines: list[str],
    actions: tuple[StartupRepairActionRecord, ...],
) -> None:
    if not actions:
        return
    lines.extend(["", "## Applied fixes"])
    for action in actions:
        line = f"- `{action.action_id}`: ok={action.ok} exit_code={action.exit_code}"
        if action.changed_tracked_state:
            line += " tracked_state=yes"
        lines.append(line)
        if action.detail:
            lines.append(f"  detail: {action.detail}")
        if action.resulting_attention_status:
            lines.append(
                f"  resulting_attention_status: {action.resulting_attention_status}"
            )


def run_startup_repair(args) -> int:
    """Classify startup issues and optionally apply bounded safe fixes."""
    try:
        state = _run_repair_pass(
            repo_root=REPO_ROOT.resolve(),
            apply_safe_fixes=bool(getattr(args, "apply_safe_fixes", False)),
        )
    except ValueError as exc:
        return render_governance_value_error(exc)

    return emit_governance_command_output(
        args,
        command="startup-context",
        json_payload=state.result.to_dict(),
        markdown_output=_render_markdown(state.result),
        ok=state.result.ok,
        summary={
            "repair_mode": True,
            "issue_count": state.result.issue_count,
            "safe_fix_available_count": state.result.safe_fix_available_count,
            "next_action": state.result.next_action,
            "checkpoint_required": state.result.checkpoint_required,
        },
    )


def _run_repair_pass(
    *,
    repo_root,
    apply_safe_fixes: bool,
):
    applied_actions: list[StartupRepairActionRecord] = []
    attempted_actions: list[str] = []
    state = _collect_state(
        repo_root=repo_root,
        applied_actions=tuple(applied_actions),
    )
    if not apply_safe_fixes:
        return state

    for _ in range(_MAX_SAFE_FIX_ATTEMPTS):
        action_id = select_safe_repair_action(
            state.result,
            attempted_actions=tuple(attempted_actions),
        )
        if action_id is None:
            return state
        attempted_actions.append(action_id)
        applied_actions.append(
            _apply_safe_repair_action(
                action_id=action_id,
                repo_root=repo_root,
                runtime_paths=state.runtime_paths,
            )
        )
        state = _collect_state(
            repo_root=repo_root,
            applied_actions=tuple(applied_actions),
        )
    return state
