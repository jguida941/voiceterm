"""Summary helpers for the `startup-context` command."""

from __future__ import annotations

from .startup_context_render import (
    publication_backlog_count,
    publication_backlog_guidance,
)
from .startup_context_recovery import append_recovery_authority_summary_lines

_CONTEXT_GRAPH_BOOTSTRAP_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)
_SUMMARY_RERUN_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)
_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)


def summary_blockers(ctx_dict: dict) -> str:
    blockers: list[str] = []

    authority = ctx_dict.get("startup_authority")
    if isinstance(authority, dict) and authority and not bool(authority.get("ok", False)):
        blockers.append("startup_authority")

    governance = ctx_dict.get("governance")
    if isinstance(governance, dict):
        push_enforcement = governance.get("push_enforcement")
        if isinstance(push_enforcement, dict):
            if bool(push_enforcement.get("checkpoint_required", False)):
                blockers.append("checkpoint_required")
            elif not bool(push_enforcement.get("safe_to_continue_editing", True)):
                blockers.append("continuation_blocked")

    reviewer_gate = ctx_dict.get("reviewer_gate")
    if isinstance(reviewer_gate, dict) and bool(
        reviewer_gate.get("implementation_blocked", False)
    ) and not bool(reviewer_gate.get("review_gate_allows_push", False)):
        block_reason = str(
            reviewer_gate.get("implementation_block_reason") or ""
        ).strip()
        blockers.append(block_reason or "reviewer_gate")

    coordination = coordination_dict(ctx_dict)
    if bool(coordination.get("resync_required", False)):
        blockers.append("coordination_resync_required")

    permission = str(ctx_dict.get("implementation_permission") or "").strip()
    if permission in {"blocked", "suspended"}:
        blockers.append(f"implementation_permission_{permission}")

    return ",".join(blockers) if blockers else "none"


def summary_next_command(ctx_dict: dict) -> str:
    blockers = summary_blockers(ctx_dict)
    if blockers == "none":
        return _CONTEXT_GRAPH_BOOTSTRAP_COMMAND

    reviewer_command = reviewer_recovery_command(ctx_dict)
    if reviewer_command:
        return reviewer_command

    coordination = coordination_dict(ctx_dict)
    if bool(coordination.get("resync_required", False)):
        return _REVIEW_STATUS_COMMAND
    if "implementation_permission_" in blockers:
        return _REVIEW_STATUS_COMMAND

    push_decision = ctx_dict.get("push_decision")
    if isinstance(push_decision, dict):
        next_step_command = str(push_decision.get("next_step_command") or "").strip()
        if next_step_command:
            return next_step_command

        if str(push_decision.get("action") or "").strip() == "await_checkpoint":
            return f"checkpoint current slice, then rerun {_SUMMARY_RERUN_COMMAND}"

    return f"resolve blockers, then rerun {_SUMMARY_RERUN_COMMAND}"


def reviewer_recovery_command(ctx_dict: dict) -> str:
    action = str(ctx_dict.get("advisory_action") or "").strip()
    if action != "repair_reviewer_loop":
        return ""
    reviewer_gate = ctx_dict.get("reviewer_gate")
    if not isinstance(reviewer_gate, dict):
        return _REVIEW_STATUS_COMMAND
    recovery_command = str(reviewer_gate.get("recovery_command") or "").strip()
    if recovery_command:
        return recovery_command
    if not bool(reviewer_gate.get("implementation_blocked", False)):
        return ""
    if bool(reviewer_gate.get("review_gate_allows_push", False)):
        return ""
    block_reason = str(
        reviewer_gate.get("implementation_block_reason") or ""
    ).strip()
    try:
        from ...review_channel.peer_recovery import STALE_PEER_RECOVERY
    except ImportError:
        return _REVIEW_STATUS_COMMAND
    entry = STALE_PEER_RECOVERY.get(block_reason, {})
    command = str(entry.get("recommended_command") or "").strip()
    return command or _REVIEW_STATUS_COMMAND


def coordination_dict(ctx_dict: dict) -> dict[str, object]:
    coordination = ctx_dict.get("coordination")
    return coordination if isinstance(coordination, dict) else {}


def summary_coordination_lines(ctx_dict: dict) -> list[str]:
    coordination = coordination_dict(ctx_dict)
    if not coordination:
        return []
    declared = str(coordination.get("declared_topology") or "single_agent").strip()
    observed = str(coordination.get("observed_topology") or "single_agent").strip()
    recommended = str(
        coordination.get("recommended_topology") or observed or "single_agent"
    ).strip()
    lines = [
        f"coordination={declared}/{observed}->{recommended}",
        f"safe_to_fanout={bool(coordination.get('safe_to_fanout', False))}",
        f"resync_required={bool(coordination.get('resync_required', False))}",
    ]
    ownership_status = str(coordination.get("ownership_status") or "").strip()
    if ownership_status:
        lines.append(f"ownership_status={ownership_status}")
    fanout_posture = str(coordination.get("fanout_posture") or "").strip()
    if fanout_posture:
        lines.append(f"fanout_posture={fanout_posture}")
    worktree_strategy = str(coordination.get("worktree_strategy") or "").strip()
    if worktree_strategy:
        lines.append(f"worktree_strategy={worktree_strategy}")
    current_slice = str(coordination.get("current_slice") or "").strip()
    if current_slice:
        lines.append(f"current_slice={current_slice}")
    active_target = coordination.get("active_target")
    if isinstance(active_target, dict):
        plan_path = str(active_target.get("plan_path") or "").strip()
        if plan_path:
            lines.append(f"active_target={plan_path}")
    return lines


def render_summary(ctx_dict: dict) -> str:
    action = str(ctx_dict.get("advisory_action") or "").strip() or "unknown"
    reason = str(ctx_dict.get("advisory_reason") or "").strip() or "unknown"
    reviewer_gate = ctx_dict.get("reviewer_gate")
    interaction_mode = "unresolved"
    if isinstance(reviewer_gate, dict):
        interaction_mode = (
            str(reviewer_gate.get("operator_interaction_mode") or "").strip()
            or "unresolved"
        )
    lines = [
        f"action={action}",
        f"reason={reason}",
        f"interaction_mode={interaction_mode}",
        f"blockers={summary_blockers(ctx_dict)}",
        f"next={summary_next_command(ctx_dict)}",
    ]
    observed_control_topology = str(
        ctx_dict.get("observed_control_topology") or ""
    ).strip()
    if observed_control_topology:
        lines.append(f"observed_control_topology={observed_control_topology}")
    implementation_permission = str(
        ctx_dict.get("implementation_permission") or ""
    ).strip()
    if implementation_permission:
        lines.append(f"implementation_permission={implementation_permission}")
    attention = ctx_dict.get("attention")
    if isinstance(attention, dict):
        attention_status = str(attention.get("status") or "").strip()
        if attention_status:
            lines.append(f"attention_status={attention_status}")
    packet_inbox = ctx_dict.get("packet_inbox")
    if isinstance(packet_inbox, dict):
        attention_revision = str(packet_inbox.get("attention_revision") or "").strip()
        if attention_revision:
            lines.append(f"attention_revision={attention_revision}")
    append_recovery_authority_summary_lines(ctx_dict, lines)
    lines.extend(summary_coordination_lines(ctx_dict))
    ahead = publication_backlog_count(ctx_dict)
    if ahead is not None and ahead > 0:
        lines.append(f"ahead_of_upstream_commits={ahead}")
    backlog_guidance = publication_backlog_guidance(ctx_dict)
    if backlog_guidance:
        lines.append(f"push_guidance={backlog_guidance.replace('`', '')}")
    pacing = {}
    work_intake = ctx_dict.get("work_intake")
    if isinstance(work_intake, dict):
        pacing = work_intake.get("session_pacing")
        if not isinstance(pacing, dict):
            pacing = {}
    if pacing:
        lines.append(
            "session_pacing="
            f"{pacing.get('complexity_band', 'unknown')}/"
            f"{pacing.get('research_ref_budget', 0)}refs/"
            f"{pacing.get('focus_file_count', 0)}files/"
            f"{pacing.get('dependency_edge_count', 0)}deps"
        )
        live_finding_count = int(pacing.get("live_finding_count", 0) or 0)
        if live_finding_count:
            lines.append(f"pacing_live_findings={live_finding_count}")
        hot_path_count = int(pacing.get("hot_path_count", 0) or 0)
        if hot_path_count:
            lines.append(f"pacing_hot_paths={hot_path_count}")
        trigger = str(pacing.get("implementation_trigger") or "").strip()
        if trigger:
            lines.append(f"pacing_trigger={trigger}")
    plan_routing = {}
    if isinstance(work_intake, dict):
        raw_plan_routing = work_intake.get("plan_routing")
        if isinstance(raw_plan_routing, dict):
            plan_routing = raw_plan_routing
    if plan_routing:
        phase_id = str(plan_routing.get("phase_id") or "").strip()
        task_id = str(plan_routing.get("task_id") or "").strip()
        if phase_id or task_id:
            lines.append(
                "plan_routing="
                + "/".join(value for value in (phase_id, task_id) if value)
            )
    return "\n".join(lines)


__all__ = [
    "render_summary",
    "summary_blockers",
    "summary_next_command",
]
