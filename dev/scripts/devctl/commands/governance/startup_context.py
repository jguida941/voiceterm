"""devctl startup-context command implementation."""

from __future__ import annotations

from ...common_io import display_path
from ...context_graph.render import append_quality_signal_lines
from ...common import add_standard_output_arguments
from ...runtime.machine_output import (
    ArtifactOutputOptions,
    emit_machine_artifact_output,
)
from ...runtime.startup_receipt import (
    build_startup_receipt,
    write_startup_receipt,
)
from ...runtime.startup_authority import build_startup_authority_report
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
    lines.append(
        "- review_gate_allows_push: "
        f"{gate.get('review_gate_allows_push', False)}"
    )
    lines.append("")

    pe = gov.get("push_enforcement", {})
    if pe:
        lines.append("## Push/Checkpoint State")
        lines.append(f"- worktree_dirty: {pe.get('worktree_dirty', False)}")
        lines.append(f"- worktree_clean: {pe.get('worktree_clean', True)}")
        lines.append(
            f"- checkpoint_required: {pe.get('checkpoint_required', False)}"
        )
        lines.append(
            f"- safe_to_continue_editing: "
            f"{pe.get('safe_to_continue_editing', True)}"
        )
        lines.append(f"- recommended_action: `{pe.get('recommended_action', '?')}`")
        lines.append("")

    authority = ctx_dict.get("startup_authority", {})
    receipt = ctx_dict.get("startup_receipt", {})
    if isinstance(authority, dict) and authority:
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
    sc_cmd.add_argument(
        "--role",
        choices=("implementer", "reviewer"),
        default=None,
        help=(
            "Declare caller role. In active_dual_agent mode, --role reviewer "
            "blocks implementation work unless --reviewer-override is passed."
        ),
    )
    sc_cmd.add_argument(
        "--reviewer-override",
        action="store_true",
        default=False,
        help="Allow reviewer to proceed with implementation in active_dual_agent.",
    )
    add_standard_output_arguments(sc_cmd, format_choices=("json", "md"))


def _startup_authority_payload(authority_report: dict[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["ok"] = bool(authority_report.get("ok", False))
    payload["checks_run"] = int(authority_report.get("checks_run", 0) or 0)
    payload["checks_passed"] = int(authority_report.get("checks_passed", 0) or 0)
    payload["error_count"] = len(authority_report.get("errors", ()) or ())
    payload["warning_count"] = len(authority_report.get("warnings", ()) or ())
    return payload


def _startup_receipt_payload(receipt_path: str, head_commit_sha: str) -> dict[str, object]:
    return {
        "path": receipt_path,
        "head_commit_sha": head_commit_sha,
    }


def _machine_summary(
    *,
    ctx,
    push,
    authority_report: dict[str, object],
    startup_receipt_path: str,
) -> dict[str, object]:
    summary: dict[str, object] = {}
    summary["advisory_action"] = ctx.advisory_action
    summary["advisory_reason"] = ctx.advisory_reason
    summary["bridge_active"] = ctx.reviewer_gate.bridge_active
    summary["checkpoint_required"] = (
        bool(push.checkpoint_required) if push is not None else False
    )
    summary["safe_to_continue_editing"] = (
        bool(push.safe_to_continue_editing) if push is not None else True
    )
    summary["startup_authority_ok"] = bool(authority_report.get("ok", False))
    summary["startup_receipt_path"] = startup_receipt_path
    return summary


def run(args) -> int:
    """Emit the typed startup-context packet."""
    ctx = build_startup_context()
    governance = ctx.governance
    authority_report = build_startup_authority_report()
    receipt = build_startup_receipt(
        ctx,
        authority_report=authority_report,
    )
    receipt_path = write_startup_receipt(receipt, governance=governance)
    receipt_display_path = display_path(receipt_path)
    payload = ctx.to_dict()
    payload["startup_authority"] = _startup_authority_payload(authority_report)
    payload["startup_receipt"] = _startup_receipt_payload(
        receipt_display_path,
        receipt.head_commit_sha,
    )
    blocked = blocks_new_implementation(ctx) or not bool(authority_report.get("ok", False))
    # Role-aware reviewer gate: in active_dual_agent, reviewer must not
    # start implementation work unless explicitly overridden.
    caller_role = getattr(args, "role", None)
    reviewer_override = getattr(args, "reviewer_override", False)
    reviewer_blocked = False
    if (
        caller_role == "reviewer"
        and ctx.reviewer_gate.reviewer_mode == "active_dual_agent"
        and not reviewer_override
    ):
        reviewer_blocked = True
        blocked = True
    push = governance.push_enforcement if governance is not None else None
    return emit_machine_artifact_output(
        args,
        command="startup-context",
        json_payload=payload,
        human_output=_render_markdown(payload),
        options=ArtifactOutputOptions(
            ok=not blocked,
            summary=_machine_summary(
                ctx=ctx,
                push=push,
                authority_report=authority_report,
                startup_receipt_path=receipt_display_path,
            ),
        ),
    )
