"""Markdown rendering helpers for the startup-context command."""

from __future__ import annotations

from ...context_graph.render import append_quality_signal_lines
from ...runtime.project_governance_push import push_enforcement_from_mapping
from ...runtime.startup_push_recovery import artifact_publication_truth

_DEVCTL_PUSH_EXECUTE_COMMAND = "python3 dev/scripts/devctl.py push --execute"


def _append_rule_explanation(
    lines: list[str],
    payload: dict,
    *,
    summary_label: str,
) -> None:
    rule_summary = str(payload.get("rule_summary") or "").strip()
    if rule_summary:
        lines.append(f"- {summary_label}: {rule_summary}")
    match_evidence = payload.get("match_evidence")
    if isinstance(match_evidence, list):
        for row in match_evidence[:3]:
            if not isinstance(row, dict):
                continue
            summary = str(row.get("summary") or "").strip()
            if summary:
                lines.append(f"- match_evidence: {summary}")
            evidence = row.get("evidence")
            if isinstance(evidence, list):
                for item in evidence[:2]:
                    text = str(item).strip()
                    if text:
                        lines.append(f"- evidence: {text}")
    rejected = payload.get("rejected_rule_traces")
    if isinstance(rejected, list):
        for row in rejected[:2]:
            if not isinstance(row, dict):
                continue
            summary = str(row.get("summary") or "").strip()
            rejected_because = str(row.get("rejected_because") or "").strip()
            if summary and rejected_because:
                lines.append(f"- rejected_rule: {summary} -> {rejected_because}")
def _join_paths(paths: list[object], *, limit: int = 4) -> str:
    cleaned = [str(path).strip() for path in paths if str(path).strip()]
    if len(cleaned) <= limit:
        return ", ".join(f"`{path}`" for path in cleaned)
    head = ", ".join(f"`{path}`" for path in cleaned[:limit])
    return f"{head}, +{len(cleaned) - limit} more"
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
def _effective_publication_summary(published_remote: bool, post_push_green: bool) -> str:
    """Return a one-line human-readable summary of effective publication state."""
    if published_remote and post_push_green:
        return "Published to origin at HEAD"
    if published_remote:
        return "Published but post-push validation failed"
    return "Not yet published (push report is from different branch/commit)"


def _append_latest_push_receipt(lines: list[str], push_enforcement: dict) -> None:
    latest_push_path = str(push_enforcement.get("latest_push_report_path") or "").strip()
    latest_push_status = str(push_enforcement.get("latest_push_report_status") or "").strip()
    latest_push_reason = str(push_enforcement.get("latest_push_report_reason") or "").strip()
    if not (latest_push_path or latest_push_status or latest_push_reason):
        return
    published_remote, post_push_green = artifact_publication_truth(
        push_enforcement_from_mapping(push_enforcement)
    )
    lines.append(
        f"- effective_publication_state: "
        f"{_effective_publication_summary(published_remote, post_push_green)}"
    )
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
def _append_push_state(lines: list[str], ctx_dict: dict) -> None:
    push_enforcement = _push_enforcement_mapping(ctx_dict)
    if not push_enforcement:
        return
    lines.append("## Push/Checkpoint State")
    _append_latest_push_receipt(lines, push_enforcement)
    lines.append(f"- worktree_dirty: {push_enforcement.get('worktree_dirty', False)}")
    lines.append(f"- worktree_clean: {push_enforcement.get('worktree_clean', True)}")
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
def _append_push_decision(lines: list[str], push_decision: dict) -> None:
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
    _append_rule_explanation(
        lines,
        push_decision,
        summary_label="push_rule_summary",
    )
    lines.append("")
def _append_startup_gate(lines: list[str], ctx_dict: dict) -> None:
    authority = ctx_dict.get("startup_authority", {})
    receipt = ctx_dict.get("startup_receipt", {})
    if not isinstance(authority, dict) or not authority:
        return
    lines.append("## Startup Gate")
    lines.append(f"- startup_authority_ok: {authority.get('ok', False)}")
    lines.append(
        f"- startup_authority_checks: "
        f"{authority.get('checks_passed', 0)}/{authority.get('checks_run', 0)}"
    )
    lines.append(
        f"- startup_authority_errors: {authority.get('error_count', 0)}"
    )
    receipt_path = str(receipt.get("path") or "").strip()
    if receipt_path:
        lines.append(f"- startup_receipt: `{receipt_path}`")
    lines.append("")
def _append_work_intake(lines: list[str], ctx_dict: dict) -> None:
    intake = ctx_dict.get("work_intake", {})
    if not isinstance(intake, dict) or not intake:
        return
    target = intake.get("active_target", {})
    continuity = intake.get("continuity", {})
    routing = intake.get("routing", {})
    lines.append("## Work Intake")
    if isinstance(target, dict) and target:
        lines.append(
            f"- active_target: `{target.get('plan_path', '?')}` "
            f"[{target.get('target_kind', '?')}]"
        )
    lines.append(
        f"- confidence: `{intake.get('confidence', 'low')}`"
        + (
            f" ({intake.get('fallback_reason')})"
            if intake.get("fallback_reason")
            else ""
        )
    )
    if isinstance(continuity, dict) and continuity:
        lines.append(
            f"- continuity: `{continuity.get('alignment_status', 'missing')}` "
            f"({continuity.get('alignment_reason', '')})"
        )
        summary = str(continuity.get("summary") or "").strip()
        if summary:
            lines.append(f"- continuity_summary: {summary}")
    if isinstance(routing, dict) and routing:
        profile = str(routing.get("selected_workflow_profile") or "").strip()
        if profile:
            lines.append(f"- selected_workflow_profile: `{profile}`")
        preflight = str(routing.get("preflight_command") or "").strip()
        if preflight:
            lines.append(f"- preflight_command: `{preflight}`")
        _append_rule_explanation(
            lines,
            routing,
            summary_label="workflow_profile_rule_summary",
        )
    warm_refs = intake.get("warm_refs")
    if isinstance(warm_refs, list) and warm_refs:
        lines.append(f"- warm_refs: {_join_paths(warm_refs)}")
    writeback_sinks = intake.get("writeback_sinks")
    if isinstance(writeback_sinks, list) and writeback_sinks:
        lines.append(f"- writeback_sinks: {_join_paths(writeback_sinks)}")
    lines.append("")
def _append_continuity_roots(lines: list[str], gov: dict) -> None:
    memory_roots = gov.get("memory_roots", {})
    if not isinstance(memory_roots, dict):
        return
    has_memory_root = any(
        str(memory_roots.get(key) or "").strip()
        for key in ("memory_root", "context_store_root")
    )
    if not has_memory_root:
        return
    lines.append("## Continuity Roots")
    if str(memory_roots.get("memory_root") or "").strip():
        lines.append(f"- memory_root: `{memory_roots.get('memory_root')}`")
    if str(memory_roots.get("context_store_root") or "").strip():
        lines.append(
            f"- context_store_root: `{memory_roots.get('context_store_root')}`"
        )
    lines.append("")
def render_markdown(ctx_dict: dict) -> str:
    """Render startup context as concise AI-ready markdown."""
    lines = ["# Startup Context", ""]
    gov = ctx_dict.get("governance", {})
    repo_id = gov.get("repo_identity", {})
    lines.append(
        f"**Repo:** {repo_id.get('repo_name', '?')} | "
        f"**Branch:** `{repo_id.get('current_branch', '?')}`"
    )
    lines.append(
        f"**Action:** `{ctx_dict.get('advisory_action', '?')}` "
        f"({ctx_dict.get('advisory_reason', '')})"
    )
    _append_rule_explanation(
        lines,
        ctx_dict,
        summary_label="startup_rule_summary",
    )
    lines.append("")

    thesis = str(ctx_dict.get("product_thesis") or "").strip()
    if thesis:
        lines.append("## Why Stack")
        lines.append("")
        lines.append(thesis)
        lines.append("")

    gate = ctx_dict.get("reviewer_gate", {})
    lines.append("## Reviewer Gate")
    lines.append(f"- bridge_active: {gate.get('bridge_active', False)}")
    lines.append(f"- reviewer_mode: {gate.get('reviewer_mode', 'single_agent')}")
    lines.append(f"- review_accepted: {gate.get('review_accepted', False)}")
    lines.append(
        "- review_gate_allows_push: "
        f"{gate.get('review_gate_allows_push', False)}"
    )
    lines.append("")
    _append_push_state(lines, ctx_dict)
    push_decision = ctx_dict.get("push_decision", {})
    if isinstance(push_decision, dict):
        _append_push_decision(lines, push_decision)
    _append_startup_gate(lines, ctx_dict)
    _append_work_intake(lines, ctx_dict)
    _append_continuity_roots(lines, gov)

    append_quality_signal_lines(lines, ctx_dict.get("quality_signals"))

    return "\n".join(lines)
