"""devctl startup-context command implementation."""

from __future__ import annotations

from ...common import add_standard_output_arguments
from ...runtime.machine_output import (
    ArtifactOutputOptions,
    emit_machine_artifact_output,
)
from ...runtime.startup_context import build_startup_context


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

    memory_roots = gov.get("memory_roots", {})
    if isinstance(memory_roots, dict) and any(str(memory_roots.get(key) or "").strip() for key in ("memory_root", "context_store_root")):
        lines.append("## Continuity Roots")
        if str(memory_roots.get("memory_root") or "").strip():
            lines.append(f"- memory_root: `{memory_roots.get('memory_root')}`")
        if str(memory_roots.get("context_store_root") or "").strip():
            lines.append(f"- context_store_root: `{memory_roots.get('context_store_root')}`")
        lines.append("")

    return "\n".join(lines)


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
    return emit_machine_artifact_output(
        args,
        command="startup-context",
        json_payload=payload,
        human_output=_render_markdown(payload),
        options=ArtifactOutputOptions(
            summary={
                "advisory_action": ctx.advisory_action,
                "advisory_reason": ctx.advisory_reason,
                "bridge_active": ctx.reviewer_gate.bridge_active,
            }
        ),
    )
