"""Summary helpers for the `startup-context` command."""

from __future__ import annotations

from ...runtime.authority_snapshot import (
    reviewer_recovery_command as _reviewer_recovery_command,
    summary_blockers_csv as _summary_blockers_csv,
    summary_next_command as _summary_next_command,
)
from .startup_context_render import publication_backlog_count, publication_backlog_guidance
from .startup_context_recovery import append_recovery_authority_summary_lines


def summary_blockers(ctx_dict: dict) -> str:
    return _summary_blockers_csv(ctx_dict)


def summary_next_command(ctx_dict: dict) -> str:
    return _summary_next_command(ctx_dict)


def reviewer_recovery_command(ctx_dict: dict) -> str:
    return _reviewer_recovery_command(ctx_dict)


def coordination_dict(ctx_dict: dict) -> dict[str, object]:
    coordination = ctx_dict.get("coordination")
    return coordination if isinstance(coordination, dict) else {}


def _push_enforcement_dict(ctx_dict: dict) -> dict[str, object]:
    governance = ctx_dict.get("governance")
    if not isinstance(governance, dict):
        return {}
    push_enforcement = governance.get("push_enforcement")
    return push_enforcement if isinstance(push_enforcement, dict) else {}


def managed_projection_summary_lines(ctx_dict: dict) -> list[str]:
    push_enforcement = _push_enforcement_dict(ctx_dict)
    if not bool(push_enforcement.get("managed_projection_drift", False)):
        return []
    paths = push_enforcement.get("managed_projection_dirty_paths")
    if not isinstance(paths, (list, tuple)):
        paths = ()
    path_text = ",".join(str(path) for path in paths if str(path).strip())
    lines = ["managed_projection_drift=True"]
    if path_text:
        lines.append(f"managed_projection_dirty_paths={path_text}")
    return lines


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
    posture = ctx_dict.get("session_posture")
    if isinstance(posture, dict):
        posture_mode = str(posture.get("interaction_mode") or "").strip()
        if posture_mode and posture_mode != "unresolved":
            interaction_mode = posture_mode
    lines = [
        f"action={action}",
        f"reason={reason}",
        f"interaction_mode={interaction_mode}",
        f"blockers={summary_blockers(ctx_dict)}",
        f"next={summary_next_command(ctx_dict)}",
    ]
    if interaction_mode == "remote_control":
        lines.insert(
            3,
            "remote_control_routing=typed_action_request_or_bounded_repo_command",
        )
    lines.extend(managed_projection_summary_lines(ctx_dict))
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
    anchors = ctx_dict.get("packet_intent_anchors")
    if isinstance(anchors, list):
        lines.append(f"packet_intent_anchors={len(anchors)}")
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
