"""devctl startup-context command implementation."""

from __future__ import annotations

import os

from . import startup_repair as startup_repair_flow
from ...common_io import display_path
from ...common import add_standard_output_arguments
from .common import render_governance_value_error
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
    startup_receipt_path,
    write_startup_receipt,
)
from ...runtime.conductor_capability import reviewer_local_implementation_allowed
from ...runtime.startup_authority import build_startup_authority_report
from ...runtime.startup_context import build_startup_context, blocks_new_implementation

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
_IMPLEMENTATION_STRICT_INTENT = "implementation_strict"
_REVIEWER_BOOTSTRAP_INTENT = "reviewer_bootstrap"


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
    ) and not bool(reviewer_gate.get("review_gate_allows_push", False)):
        block_reason = str(
            reviewer_gate.get("implementation_block_reason") or ""
        ).strip()
        blockers.append(block_reason or "reviewer_gate")

    return ",".join(blockers) if blockers else "none"


def _summary_next_command(ctx_dict: dict) -> str:
    if _summary_blockers(ctx_dict) == "none":
        return _CONTEXT_GRAPH_BOOTSTRAP_COMMAND

    reviewer_command = _reviewer_recovery_command(ctx_dict)
    if reviewer_command:
        return reviewer_command

    push_decision = ctx_dict.get("push_decision")
    if isinstance(push_decision, dict):
        next_step_command = str(push_decision.get("next_step_command") or "").strip()
        if next_step_command:
            return next_step_command

        if str(push_decision.get("action") or "").strip() == "await_checkpoint":
            return f"checkpoint current slice, then rerun {_SUMMARY_RERUN_COMMAND}"

    return f"resolve blockers, then rerun {_SUMMARY_RERUN_COMMAND}"


def _reviewer_recovery_command(ctx_dict: dict) -> str:
    action = str(ctx_dict.get("advisory_action") or "").strip()
    if action != "repair_reviewer_loop":
        return ""
    reviewer_gate = ctx_dict.get("reviewer_gate")
    if not isinstance(reviewer_gate, dict):
        return _REVIEW_STATUS_COMMAND
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


def _startup_authority_intent(*, caller_role: str | None, reviewer_override: bool) -> str:
    """Return the startup-authority intent for the current caller role."""
    if caller_role == "reviewer" and not reviewer_override:
        return _REVIEWER_BOOTSTRAP_INTENT
    return _IMPLEMENTATION_STRICT_INTENT


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
    sc_cmd.add_argument(
        "--repair",
        action="store_true",
        default=False,
        help=(
            "Classify startup blockers and emit the bounded startup repair report "
            "instead of the normal startup receipt."
        ),
    )
    sc_cmd.add_argument(
        "--apply-safe-fixes",
        action="store_true",
        default=False,
        help=(
            "Only valid with --repair. Apply repo-owned safe local fixes while "
            "still failing closed on approval-boundary work."
        ),
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
    if getattr(args, "apply_safe_fixes", False) and not getattr(args, "repair", False):
        return render_governance_value_error(
            ValueError("startup-context --apply-safe-fixes requires --repair.")
        )
    if getattr(args, "repair", False):
        return startup_repair_flow.run_startup_repair(args)

    ctx = build_startup_context()
    governance = ctx.governance
    caller_role = getattr(args, "role", None)
    reviewer_override = getattr(args, "reviewer_override", False)
    authority_report = build_startup_authority_report(
        intent=_startup_authority_intent(
            caller_role=caller_role,
            reviewer_override=reviewer_override,
        ),
        governance=governance,
        reviewer_gate=ctx.reviewer_gate,
    )
    receipt = build_startup_receipt(
        ctx,
        authority_report=authority_report,
    )
    # The startup receipt is the command's primary output — the launcher
    # validates it to gate subsequent actions.  On intentional read-only
    # mounts (DEVCTL_NO_ARTIFACT_WRITES=1, MCP adapters, containers) skip
    # the write entirely and fall back to the expected path.  When the env
    # var is not set, let any OSError (disk-full, permissions) propagate so
    # callers see real failures.
    if os.environ.get("DEVCTL_NO_ARTIFACT_WRITES") == "1":
        try:
            receipt_path = write_startup_receipt(receipt, governance=governance)
        except OSError:
            receipt_path = startup_receipt_path(governance=governance)
    else:
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
    reviewer_blocked = False
    if caller_role == "reviewer" and not reviewer_local_implementation_allowed(
        reviewer_mode=ctx.reviewer_gate.reviewer_mode,
        reviewer_override=reviewer_override,
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
