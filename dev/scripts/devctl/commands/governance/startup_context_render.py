"""Markdown rendering helpers for the startup-context command."""

from __future__ import annotations

from ...context_graph.render import append_quality_signal_lines
from ...review_channel.ack_contract import packet_ack_is_transport_lifecycle_line
from ...runtime.conductor_capability import (
    context_graph_bootstrap_command,
    session_resume_command_for_role,
    startup_context_command_for_role,
)
from ...runtime.startup_continuity_render import (
    append_continuity_attention_lines as _append_continuity_attention_lines,
)
from .startup_context_connectivity_render import (
    append_connectivity_registry as _append_connectivity_registry,
)
from .startup_context_posture_render import (
    append_packet_intent_anchors as _append_packet_intent_anchors,
    append_remote_control_boundaries as _append_remote_control_boundaries,
    interaction_mode as _interaction_mode,
)
from .startup_context_push_render import (
    append_push_decision as _append_push_decision,
    append_push_state as _append_push_state,
    publication_backlog_count,
    publication_backlog_guidance,
)
from .startup_context_blocker_render import append_blocker_table
from .startup_context_work_render import (
    append_coordination_snapshot as _append_coordination_snapshot,
    append_work_intake as _append_work_intake,
)


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
    lines.append(packet_ack_is_transport_lifecycle_line())
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
    _append_operator_override_discovery(lines, ctx_dict)

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
    if bool(ctx_dict.get("publication_deferred_active", False)):
        lines.append("- publication_deferred_active: `true`")
        reason = str(ctx_dict.get("publication_deferred_reason") or "").strip()
        if reason:
            lines.append(f"- publication_deferred_reason: `{reason}`")
        command = str(ctx_dict.get("deferred_publication_command") or "").strip()
        if command:
            lines.append(f"- deferred_publication_command: `{command}`")
        actions = ctx_dict.get("deferred_publication_actions")
        if isinstance(actions, list) and actions:
            action_text = ", ".join(f"`{action}`" for action in actions)
            lines.append(f"- deferred_publication_actions: {action_text}")
    lines.append(f"- interaction_mode: `{_interaction_mode(ctx_dict)}`")
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
    _append_remote_control_boundaries(lines, ctx_dict)
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
    _append_packet_intent_anchors(lines, ctx_dict)
    role = str(ctx_dict.get("agent_lane") or ctx_dict.get("role") or "").strip()
    if role not in {"dashboard", "implementer", "observer", "reviewer"}:
        role = "implementer"
    _append_continuity_attention_lines(
        lines,
        ctx_dict.get("continuity_attention"),
        startup_command=startup_context_command_for_role(role),
        session_resume_command=session_resume_command_for_role(role),
        status_command=(
            "python3 dev/scripts/devctl.py review-channel --action status "
            "--terminal none --format json"
        ),
        context_graph_command=context_graph_bootstrap_command(),
    )
    _append_work_intake(
        lines,
        ctx_dict,
        append_rule_explanation_fn=_append_rule_explanation,
    )
    _append_coordination_snapshot(lines, ctx_dict)
    _append_connectivity_registry(lines, ctx_dict)
    _append_continuity_roots(lines, gov)

    append_quality_signal_lines(lines, ctx_dict.get("quality_signals"))

    return "\n".join(lines)


def _append_operator_override_discovery(lines: list[str], ctx_dict: dict) -> None:
    if not _startup_has_blocking_gate(ctx_dict):
        return
    lines.append("## Operator Override Discovery")
    lines.append(
        "- edit_only: `agent-loop --operator-override --override-scope edit-only "
        "--override-reason '<typed reason>'`; still blocks `vcs.stage`, "
        "`vcs.commit`, `vcs.push`; lifecycle owner: `MP377-P0-EXC-S1`."
    )
    lines.append("")


def _startup_has_blocking_gate(ctx_dict: dict) -> bool:
    advisory_action = str(ctx_dict.get("advisory_action") or "").strip()
    if advisory_action in {
        "await_review",
        "checkpoint_before_continue",
        "repair_reviewer_loop",
    }:
        return True
    gate = ctx_dict.get("reviewer_gate")
    if isinstance(gate, dict) and bool(gate.get("implementation_blocked")):
        return True
    push = ctx_dict.get("push_decision")
    if isinstance(push, dict) and str(push.get("action") or "").strip() in {
        "await_checkpoint",
        "await_review",
    }:
        return True
    blocker = ctx_dict.get("blocker")
    return isinstance(blocker, dict) and str(
        blocker.get("top_blocker") or ""
    ).strip() not in {"", "none"}
