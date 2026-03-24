"""devctl startup-context command implementation."""

from __future__ import annotations

from ...context_graph.render import append_quality_signal_lines
from ...common import add_standard_output_arguments
from ...runtime.machine_output import (
    ArtifactOutputOptions,
    emit_machine_artifact_output,
)
from ...runtime.startup_context import build_startup_context, blocks_new_implementation


def _render_markdown(ctx_dict: dict) -> str:
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
    lines.append("")

    gate = ctx_dict.get("reviewer_gate", {})
    lines.append("## Reviewer Gate")
    lines.append(f"- bridge_active: {gate.get('bridge_active', False)}")
    lines.append(f"- reviewer_mode: {gate.get('reviewer_mode', 'single_agent')}")
    lines.append(f"- review_accepted: {gate.get('review_accepted', False)}")
    lines.append(f"- push_permitted: {gate.get('push_permitted', False)}")
    lines.append("")

    pe = gov.get("push_enforcement", {})
    if pe:
        lines.append("## Push/Checkpoint State")
        lines.append(f"- worktree_dirty: {pe.get('worktree_dirty', False)}")
        lines.append(
            f"- checkpoint_required: {pe.get('checkpoint_required', False)}"
        )
        lines.append(
            f"- safe_to_continue_editing: "
            f"{pe.get('safe_to_continue_editing', True)}"
        )
        lines.append(f"- recommended_action: `{pe.get('recommended_action', '?')}`")
        lines.append("")

    intake = ctx_dict.get("work_intake", {})
    if isinstance(intake, dict) and intake:
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
        warm_refs = intake.get("warm_refs")
        if isinstance(warm_refs, list) and warm_refs:
            lines.append(f"- warm_refs: {_join_paths(warm_refs)}")
        writeback_sinks = intake.get("writeback_sinks")
        if isinstance(writeback_sinks, list) and writeback_sinks:
            lines.append(f"- writeback_sinks: {_join_paths(writeback_sinks)}")
        lines.append("")

    memory_roots = gov.get("memory_roots", {})
    if isinstance(memory_roots, dict) and any(str(memory_roots.get(key) or "").strip() for key in ("memory_root", "context_store_root")):
        lines.append("## Continuity Roots")
        if str(memory_roots.get("memory_root") or "").strip():
            lines.append(f"- memory_root: `{memory_roots.get('memory_root')}`")
        if str(memory_roots.get("context_store_root") or "").strip():
            lines.append(f"- context_store_root: `{memory_roots.get('context_store_root')}`")
        lines.append("")

    append_quality_signal_lines(lines, ctx_dict.get("quality_signals"))

    return "\n".join(lines)


def _join_paths(paths: list[object], *, limit: int = 4) -> str:
    cleaned = [str(path).strip() for path in paths if str(path).strip()]
    if len(cleaned) <= limit:
        return ", ".join(f"`{path}`" for path in cleaned)
    head = ", ".join(f"`{path}`" for path in cleaned[:limit])
    return f"{head}, +{len(cleaned) - limit} more"


def add_parser(subparsers) -> None:
    """Register the startup-context CLI parser."""
    sc_cmd = subparsers.add_parser(
        "startup-context",
        help="Emit typed startup-context packet for AI agent sessions",
    )
    add_standard_output_arguments(sc_cmd, format_choices=("json", "md"))


def run(args) -> int:
    """Emit the typed startup-context packet."""
    ctx = build_startup_context()
    payload = ctx.to_dict()
    blocked = blocks_new_implementation(ctx)
    governance = ctx.governance
    push = governance.push_enforcement if governance is not None else None
    return emit_machine_artifact_output(
        args,
        command="startup-context",
        json_payload=payload,
        human_output=_render_markdown(payload),
        options=ArtifactOutputOptions(
            ok=not blocked,
            summary={
                "advisory_action": ctx.advisory_action,
                "advisory_reason": ctx.advisory_reason,
                "bridge_active": ctx.reviewer_gate.bridge_active,
                "checkpoint_required": (
                    bool(push.checkpoint_required) if push is not None else False
                ),
                "safe_to_continue_editing": (
                    bool(push.safe_to_continue_editing) if push is not None else True
                ),
            }
        ),
    )
