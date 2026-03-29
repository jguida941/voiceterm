"""devctl startup-context command implementation."""

from __future__ import annotations

from ...common_io import display_path
from ...common import add_standard_output_arguments
from .startup_context_render import (
    publication_backlog_count,
    publication_backlog_guidance,
    render_markdown as _render_markdown,
)
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

_CONTEXT_GRAPH_BOOTSTRAP_COMMAND = (
    "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md"
)
_SUMMARY_RERUN_COMMAND = (
    "python3 dev/scripts/devctl.py startup-context --format summary"
)


def _summary_blockers(ctx_dict: dict) -> str:
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
    ):
        block_reason = str(
            reviewer_gate.get("implementation_block_reason") or ""
        ).strip()
        blockers.append(block_reason or "reviewer_gate")

    return ",".join(blockers) if blockers else "none"


def _summary_next_command(ctx_dict: dict) -> str:
    if _summary_blockers(ctx_dict) == "none":
        return _CONTEXT_GRAPH_BOOTSTRAP_COMMAND

    push_decision = ctx_dict.get("push_decision")
    if isinstance(push_decision, dict):
        next_step_command = str(push_decision.get("next_step_command") or "").strip()
        if next_step_command:
            return next_step_command

        if str(push_decision.get("action") or "").strip() == "await_checkpoint":
            return f"checkpoint current slice, then rerun {_SUMMARY_RERUN_COMMAND}"

    return f"resolve blockers, then rerun {_SUMMARY_RERUN_COMMAND}"


def _render_summary(ctx_dict: dict) -> str:
    action = str(ctx_dict.get("advisory_action") or "").strip() or "unknown"
    reason = str(ctx_dict.get("advisory_reason") or "").strip() or "unknown"
    lines = [
        f"action={action}",
        f"reason={reason}",
        f"blockers={_summary_blockers(ctx_dict)}",
        f"next={_summary_next_command(ctx_dict)}",
    ]
    ahead = publication_backlog_count(ctx_dict)
    if ahead is not None and ahead > 0:
        lines.append(f"ahead_of_upstream_commits={ahead}")
    backlog_guidance = publication_backlog_guidance(ctx_dict)
    if backlog_guidance:
        lines.append(f"push_guidance={backlog_guidance.replace('`', '')}")
    return "\n".join(lines)


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
    add_standard_output_arguments(sc_cmd, format_choices=("json", "md", "summary"))


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
    summary["push_eligible_now"] = bool(ctx.push_decision.push_eligible_now)
    summary["push_action"] = ctx.push_decision.action
    summary["push_next_step_command"] = ctx.push_decision.next_step_command
    summary["publication_backlog_state"] = (
        ctx.push_decision.publication_backlog.backlog_state
    )
    summary["publication_backlog_recommended"] = bool(
        ctx.push_decision.publication_backlog.backlog_recommended
    )
    summary["publication_backlog_urgent"] = bool(
        ctx.push_decision.publication_backlog.backlog_urgent
    )
    summary["publication_guidance"] = ctx.push_decision.publication_guidance
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
    human_output = _render_summary(payload)
    if getattr(args, "format", "") == "md":
        human_output = _render_markdown(payload)
    return emit_machine_artifact_output(
        args,
        command="startup-context",
        json_payload=payload,
        human_output=human_output,
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
