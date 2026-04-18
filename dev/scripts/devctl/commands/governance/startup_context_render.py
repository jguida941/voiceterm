"""Markdown rendering helpers for the startup-context command."""

from __future__ import annotations

from ...context_graph.render import append_quality_signal_lines
from ...runtime.work_intake_models import session_pacing_markdown_lines
from ...runtime.work_intake_plan_routing import plan_routing_markdown_lines
from .startup_context_push_render import (
    append_push_decision as _append_push_decision,
    append_push_state as _append_push_state,
    publication_backlog_count,
    publication_backlog_guidance,
)
from .startup_context_blocker_render import append_blocker_table


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
    if isinstance(continuity, dict) and continuity:
        lines.append(
            f"- continuity: `{continuity.get('alignment_status', 'missing')}` "
            f"({continuity.get('alignment_reason', '')})"
        )
        summary = str(continuity.get("summary") or "").strip()
        if summary:
            lines.append(f"- continuity_summary: {summary}")
    ownership = intake.get("ownership", {})
    if isinstance(ownership, dict) and ownership:
        lines.append(
            f"- ownership: `{ownership.get('status', 'clear')}`"
            + (
                f" ({ownership.get('scope_source')})"
                if ownership.get("scope_source")
                else ""
            )
        )
        ownership_summary = str(ownership.get("summary") or "").strip()
        if ownership_summary:
            lines.append(f"- ownership_summary: {ownership_summary}")
        outside_scope = ownership.get("outside_scope_dirty_paths")
        if isinstance(outside_scope, list) and outside_scope:
            lines.append(
                f"- outside_scope_dirty_paths: {_join_paths(outside_scope)}"
            )
        live_agents = ownership.get("live_agents")
        if isinstance(live_agents, list) and live_agents:
            lines.append(f"- live_agents: {_join_paths(live_agents)}")
    if isinstance(coordination, dict) and coordination:
        lines.append(
            "- collaboration_topology: "
            f"`{coordination.get('collaboration_topology', 'single_agent')}`"
        )
        lines.append(
            f"- authority_mode: `{coordination.get('authority_mode', 'self_directed')}`"
        )
        lines.append(
            "- work_ownership_mode: "
            f"`{coordination.get('work_ownership_mode', 'exclusive_slice')}`"
        )
        lines.append(
            f"- sync_cadence_mode: `{coordination.get('sync_cadence_mode', 'continuous')}`"
        )
        coordination_summary = str(coordination.get("summary") or "").strip()
        if coordination_summary:
            lines.append(f"- coordination_summary: {coordination_summary}")
        active_roles = coordination.get("active_roles")
        if isinstance(active_roles, list) and active_roles:
            lines.append(f"- active_roles: {_join_paths(active_roles)}")
        active_participants = coordination.get("active_participants")
        if isinstance(active_participants, list) and active_participants:
            lines.append(
                f"- active_participants: {_join_paths(active_participants)}"
            )
        delegated_agents = coordination.get("delegated_agents")
        if isinstance(delegated_agents, list) and delegated_agents:
            lines.append(f"- delegated_agents: {_join_paths(delegated_agents)}")
        delegated_worktrees = coordination.get("delegated_worktrees")
        if isinstance(delegated_worktrees, list) and delegated_worktrees:
            lines.append(
                f"- delegated_worktrees: {_join_paths(delegated_worktrees)}"
            )
        duplicate_worktrees = coordination.get("duplicate_delegated_worktrees")
        if isinstance(duplicate_worktrees, list) and duplicate_worktrees:
            lines.append(
                "- duplicate_delegated_worktrees: "
                f"{_join_paths(duplicate_worktrees)}"
            )
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
    lines.extend(plan_routing_markdown_lines(intake.get("plan_routing")))
    lines.extend(session_pacing_markdown_lines(intake.get("session_pacing")))
    warm_refs = intake.get("warm_refs")
    if isinstance(warm_refs, list) and warm_refs:
        lines.append(f"- warm_refs: {_join_paths(warm_refs)}")
    writeback_sinks = intake.get("writeback_sinks")
    if isinstance(writeback_sinks, list) and writeback_sinks:
        lines.append(f"- writeback_sinks: {_join_paths(writeback_sinks)}")
    lines.append("")


def _append_coordination_snapshot(lines: list[str], ctx_dict: dict) -> None:
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
    lines.append(f"- fanout_posture: `{coordination.get('fanout_posture', 'single_agent_only')}`")
    lines.append(f"- safe_to_fanout: {coordination.get('safe_to_fanout', False)}")
    lines.append(
        f"- worktree_strategy: `{coordination.get('worktree_strategy', 'shared_primary_worktree')}`"
    )
    lines.append(f"- resync_required: {coordination.get('resync_required', False)}")
    resync_reasons = coordination.get("resync_reasons")
    if isinstance(resync_reasons, list) and resync_reasons:
        lines.append(f"- resync_reasons: {_join_paths(resync_reasons)}")
    duplicate_worktrees = coordination.get("duplicate_worktrees")
    if isinstance(duplicate_worktrees, list) and duplicate_worktrees:
        lines.append(f"- duplicate_worktrees: {_join_paths(duplicate_worktrees)}")
    actors = coordination.get("actors")
    if isinstance(actors, list) and actors:
        actor_labels = []
        for row in actors:
            if not isinstance(row, dict):
                continue
            actor_id = str(row.get("actor_id") or "").strip()
            if not actor_id:
                continue
            detail = f"{actor_id}:{str(row.get('presence') or '').strip()}"
            provider = str(row.get("provider") or "").strip()
            role = str(row.get("role") or "").strip()
            lane = str(row.get("lane") or "").strip()
            worktree = str(row.get("worktree") or "").strip()
            branch = str(row.get("branch") or "").strip()
            mp_scope = str(row.get("mp_scope") or "").strip()
            if provider:
                detail += f"|provider={provider}"
            if role:
                detail += f"|role={role}"
            if lane:
                detail += f"|lane={lane}"
            if worktree:
                detail += f"|worktree={worktree}"
            if branch:
                detail += f"|branch={branch}"
            if mp_scope:
                detail += f"|scope={mp_scope}"
            actor_labels.append(detail)
        if actor_labels:
            lines.append(f"- actors: {_join_paths(actor_labels)}")
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


def _append_pending_inbox(lines: list[str], ctx_dict: dict) -> None:
    packet_inbox = ctx_dict.get("packet_inbox", {})
    if not isinstance(packet_inbox, dict):
        return
    agents = packet_inbox.get("agents")
    if not isinstance(agents, list) or not agents:
        return
    lines.append("## Pending Inbox")
    attention_revision = str(packet_inbox.get("attention_revision") or "").strip()
    if attention_revision:
        lines.append(f"- attention_revision: `{attention_revision}`")
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        agent_id = str(agent.get("agent") or "").strip() or "agent"
        attention_status = str(agent.get("attention_status") or "none").strip()
        wake_reason = str(agent.get("wake_reason") or "").strip()
        delivery_state = str(agent.get("delivery_state") or "").strip()
        required_command = str(agent.get("required_command") or "").strip()
        current_instruction_packet_id = str(
            agent.get("current_instruction_packet_id") or ""
        ).strip()
        latest_finding_packet_id = str(
            agent.get("latest_finding_packet_id") or ""
        ).strip()
        pending_actionable_total = int(agent.get("pending_actionable_total") or 0)
        expired_unresolved_total = int(agent.get("expired_unresolved_total") or 0)
        details = [f"attention={attention_status}"]
        if wake_reason:
            details.append(f"wake_reason={wake_reason}")
        if delivery_state:
            details.append(f"delivery={delivery_state}")
        if current_instruction_packet_id:
            details.append(f"instruction={current_instruction_packet_id}")
        if latest_finding_packet_id:
            details.append(f"finding={latest_finding_packet_id}")
        if pending_actionable_total:
            details.append(f"pending_actionable={pending_actionable_total}")
        if expired_unresolved_total:
            details.append(f"expired_unresolved={expired_unresolved_total}")
        lines.append(f"- {agent_id}: " + ", ".join(details))
        if required_command:
            lines.append(f"  required_command: `{required_command}`")
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
    append_blocker_table(lines, ctx_dict)

    thesis = str(ctx_dict.get("product_thesis") or "").strip()
    if thesis:
        lines.append("## Why Stack")
        lines.append("")
        lines.append(thesis)
        lines.append("")

    gate = ctx_dict.get("reviewer_gate", {})
    gate_mode = str(
        gate.get("effective_reviewer_mode")
        or gate.get("reviewer_mode")
        or "tools_only"
    ).strip()
    lines.append("## Reviewer Gate")
    lines.append(f"- bridge_active: {gate.get('bridge_active', False)}")
    lines.append(f"- reviewer_mode: {gate_mode}")
    lines.append(f"- review_accepted: {gate.get('review_accepted', False)}")
    lines.append(
        "- review_gate_allows_push: "
        f"{gate.get('review_gate_allows_push', False)}"
    )
    observed_control_topology = str(
        ctx_dict.get("observed_control_topology") or ""
    ).strip()
    if observed_control_topology:
        lines.append(f"- observed_control_topology: `{observed_control_topology}`")
    implementation_permission = str(
        ctx_dict.get("implementation_permission") or ""
    ).strip()
    if implementation_permission:
        lines.append(f"- implementation_permission: `{implementation_permission}`")
    recovery_action = str(ctx_dict.get("recovery_action") or "").strip()
    if recovery_action:
        lines.append(f"- recovery_action: `{recovery_action}`")
    recovery_basis = str(ctx_dict.get("recovery_basis") or "").strip()
    if recovery_basis:
        lines.append(f"- recovery_basis: `{recovery_basis}`")
    recovery_scope = str(ctx_dict.get("recovery_scope") or "").strip()
    if recovery_scope:
        lines.append(f"- recovery_scope: `{recovery_scope}`")
    lines.append("")
    _append_push_state(lines, ctx_dict)
    push_decision = ctx_dict.get("push_decision", {})
    if isinstance(push_decision, dict):
        _append_push_decision(
            lines,
            push_decision,
            append_rule_explanation_fn=_append_rule_explanation,
        )
    _append_startup_gate(lines, ctx_dict)
    _append_pending_inbox(lines, ctx_dict)
    _append_work_intake(lines, ctx_dict)
    _append_coordination_snapshot(lines, ctx_dict)
    _append_continuity_roots(lines, gov)

    append_quality_signal_lines(lines, ctx_dict.get("quality_signals"))

    return "\n".join(lines)
