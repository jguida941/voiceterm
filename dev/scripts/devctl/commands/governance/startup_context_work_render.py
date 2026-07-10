"""Work-intake and coordination rendering for startup-context markdown."""

from __future__ import annotations

from ...runtime.work_intake_models import session_pacing_markdown_lines
from ...runtime.work_intake_plan_routing import plan_routing_markdown_lines
from .startup_context_render_format import join_paths as _join_paths


def append_work_intake(
    lines: list[str],
    ctx_dict: dict,
    *,
    append_rule_explanation_fn,
) -> None:
    """Render work-intake details from the typed startup payload."""
    intake = ctx_dict.get("work_intake", {})
    if not isinstance(intake, dict) or not intake:
        return
    target = intake.get("active_target", {})
    continuity = intake.get("continuity", {})
    routing = intake.get("routing", {})
    coordination = intake.get("coordination", {})
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
    _append_work_intake_continuity(lines, continuity)
    _append_work_intake_ownership(lines, intake.get("ownership", {}))
    _append_work_intake_coordination(lines, coordination)
    _append_work_intake_routing(
        lines,
        routing,
        append_rule_explanation_fn=append_rule_explanation_fn,
    )
    lines.extend(plan_routing_markdown_lines(intake.get("plan_routing")))
    lines.extend(session_pacing_markdown_lines(intake.get("session_pacing")))
    _append_path_rows(
        lines,
        warm_refs=intake.get("warm_refs"),
        writeback_sinks=intake.get("writeback_sinks"),
    )
    lines.append("")


def append_coordination_snapshot(lines: list[str], ctx_dict: dict) -> None:
    """Render the bounded coordination snapshot."""
    coordination = ctx_dict.get("coordination", {})
    if not isinstance(coordination, dict) or not coordination:
        return
    lines.append("## Coordination Snapshot")
    target = coordination.get("active_target", {})
    if isinstance(target, dict) and target:
        lines.append(
            f"- active_target: `{target.get('plan_path', '?')}` "
            f"[{target.get('target_kind', '?')}]"
        )
    current_slice = str(coordination.get("current_slice") or "").strip()
    if current_slice:
        lines.append(f"- current_slice: {current_slice}")
    scope_paths = coordination.get("scope_paths")
    if isinstance(scope_paths, list) and scope_paths:
        lines.append(f"- scope_paths: {_join_paths(scope_paths)}")
    lines.append(
        "- topology: "
        f"`{coordination.get('declared_topology', 'single_agent')}` / "
        f"`{coordination.get('observed_topology', 'single_agent')}` -> "
        f"`{coordination.get('recommended_topology', 'single_agent')}`"
    )
    lines.append(
        f"- fanout_posture: `{coordination.get('fanout_posture', 'single_agent_only')}`"
    )
    lines.append(f"- safe_to_fanout: {coordination.get('safe_to_fanout', False)}")
    lines.append(
        f"- worktree_strategy: `{coordination.get('worktree_strategy', 'shared_primary_worktree')}`"
    )
    lines.append(f"- resync_required: {coordination.get('resync_required', False)}")
    _append_coordination_lists(lines, coordination)
    _append_actor_labels(lines, coordination.get("actors"))
    lines.append("")


def _append_work_intake_continuity(lines: list[str], continuity: object) -> None:
    if not isinstance(continuity, dict) or not continuity:
        return
    lines.append(
        f"- continuity: `{continuity.get('alignment_status', 'missing')}` "
        f"({continuity.get('alignment_reason', '')})"
    )
    summary = str(continuity.get("summary") or "").strip()
    if summary:
        lines.append(f"- continuity_summary: {summary}")


def _append_work_intake_ownership(lines: list[str], ownership: object) -> None:
    if not isinstance(ownership, dict) or not ownership:
        return
    lines.append(
        f"- ownership: `{ownership.get('status', 'clear')}`"
        + (f" ({ownership.get('scope_source')})" if ownership.get("scope_source") else "")
    )
    ownership_summary = str(ownership.get("summary") or "").strip()
    if ownership_summary:
        lines.append(f"- ownership_summary: {ownership_summary}")
    outside_scope = ownership.get("outside_scope_dirty_paths")
    if isinstance(outside_scope, list) and outside_scope:
        lines.append(f"- outside_scope_dirty_paths: {_join_paths(outside_scope)}")
    live_agents = ownership.get("live_agents")
    if isinstance(live_agents, list) and live_agents:
        lines.append(f"- live_agents: {_join_paths(live_agents)}")


def _append_work_intake_coordination(lines: list[str], coordination: object) -> None:
    if not isinstance(coordination, dict) or not coordination:
        return
    lines.append(
        "- collaboration_topology: "
        f"`{coordination.get('collaboration_topology', 'single_agent')}`"
    )
    lines.append(f"- authority_mode: `{coordination.get('authority_mode', 'self_directed')}`")
    lines.append(
        "- work_ownership_mode: "
        f"`{coordination.get('work_ownership_mode', 'exclusive_slice')}`"
    )
    lines.append(f"- sync_cadence_mode: `{coordination.get('sync_cadence_mode', 'continuous')}`")
    coordination_summary = str(coordination.get("summary") or "").strip()
    if coordination_summary:
        lines.append(f"- coordination_summary: {coordination_summary}")
    for key in (
        "active_roles",
        "active_participants",
        "delegated_agents",
        "delegated_worktrees",
        "duplicate_delegated_worktrees",
    ):
        values = coordination.get(key)
        if isinstance(values, list) and values:
            lines.append(f"- {key}: {_join_paths(values)}")


def _append_work_intake_routing(
    lines: list[str],
    routing: object,
    *,
    append_rule_explanation_fn,
) -> None:
    if not isinstance(routing, dict) or not routing:
        return
    profile = str(routing.get("selected_workflow_profile") or "").strip()
    if profile:
        lines.append(f"- selected_workflow_profile: `{profile}`")
    preflight = str(routing.get("preflight_command") or "").strip()
    if preflight:
        lines.append(f"- preflight_command: `{preflight}`")
    append_rule_explanation_fn(
        lines,
        routing,
        summary_label="workflow_profile_rule_summary",
    )


def _append_path_rows(lines: list[str], **rows: object) -> None:
    for key, value in rows.items():
        if isinstance(value, list) and value:
            lines.append(f"- {key}: {_join_paths(value)}")


def _append_coordination_lists(lines: list[str], coordination: dict) -> None:
    for key in ("resync_reasons", "duplicate_worktrees"):
        values = coordination.get(key)
        if isinstance(values, list) and values:
            lines.append(f"- {key}: {_join_paths(values)}")


def _append_actor_labels(lines: list[str], actors: object) -> None:
    if not isinstance(actors, list) or not actors:
        return
    actor_labels = []
    for row in actors:
        if isinstance(row, dict):
            label = _actor_label(row)
            if label:
                actor_labels.append(label)
    if actor_labels:
        lines.append(f"- actors: {_join_paths(actor_labels)}")


def _actor_label(row: dict) -> str:
    actor_id = str(row.get("actor_id") or "").strip()
    if not actor_id:
        return ""
    detail = f"{actor_id}:{str(row.get('presence') or '').strip()}"
    for source, label in (
        ("provider", "provider"),
        ("role", "role"),
        ("lane", "lane"),
        ("worktree", "worktree"),
        ("branch", "branch"),
        ("mp_scope", "scope"),
    ):
        value = str(row.get(source) or "").strip()
        if value:
            detail += f"|{label}={value}"
    return detail


__all__ = ["append_coordination_snapshot", "append_work_intake"]
