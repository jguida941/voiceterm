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
from .startup_context_recovery import (
    append_recovery_authority_summary_lines,
    apply_recovery_authority_summary,
)
from ...runtime.machine_output import (
    ArtifactOutputOptions,
    emit_machine_artifact_output,
)
from ...runtime.action_routing import project_startup_action_routing
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

    coordination = _coordination_dict(ctx_dict)
    if bool(coordination.get("resync_required", False)):
        blockers.append("coordination_resync_required")

    permission = str(ctx_dict.get("implementation_permission") or "").strip()
    if permission in {"blocked", "suspended"}:
        blockers.append(f"implementation_permission_{permission}")

    return ",".join(blockers) if blockers else "none"


def _summary_next_command(ctx_dict: dict) -> str:
    blockers = _summary_blockers(ctx_dict)
    if blockers == "none":
        return _CONTEXT_GRAPH_BOOTSTRAP_COMMAND

    reviewer_command = _reviewer_recovery_command(ctx_dict)
    if reviewer_command:
        return reviewer_command

    coordination = _coordination_dict(ctx_dict)
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


def _reviewer_recovery_command(ctx_dict: dict) -> str:
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


def _coordination_dict(ctx_dict: dict) -> dict[str, object]:
    coordination = ctx_dict.get("coordination")
    return coordination if isinstance(coordination, dict) else {}


def _summary_coordination_lines(ctx_dict: dict) -> list[str]:
    coordination = _coordination_dict(ctx_dict)
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


def _render_summary(ctx_dict: dict) -> str:
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
        f"blockers={_summary_blockers(ctx_dict)}",
        f"next={_summary_next_command(ctx_dict)}",
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
    append_recovery_authority_summary_lines(ctx_dict, lines)
    lines.extend(_summary_coordination_lines(ctx_dict))
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
        trigger = str(pacing.get("implementation_trigger") or "").strip()
        if trigger:
            lines.append(f"pacing_trigger={trigger}")
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
        choices=("dashboard", "implementer", "observer", "reviewer"),
        default=None,
        help=(
            "Declare caller lane. Dashboard/observer lanes are read/findings "
            "only. In active_dual_agent mode, --role reviewer blocks "
            "implementation work unless --reviewer-override is passed."
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
    summary["observed_control_topology"] = getattr(
        ctx,
        "observed_control_topology",
        "no_live_agents",
    )
    summary["implementation_permission"] = getattr(
        ctx,
        "implementation_permission",
        "blocked",
    )
    apply_recovery_authority_summary(summary, ctx)
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
    if ctx.work_intake is not None:
        summary["work_intake"] = {
            "coordination": ctx.work_intake.coordination.to_dict(),
        }
    if ctx.coordination is not None:
        summary["coordination"] = {
            "declared_topology": ctx.coordination.declared_topology,
            "observed_topology": ctx.coordination.observed_topology,
            "recommended_topology": ctx.coordination.recommended_topology,
            "fanout_posture": ctx.coordination.fanout_posture,
            "safe_to_fanout": bool(ctx.coordination.safe_to_fanout),
            "worktree_strategy": ctx.coordination.worktree_strategy,
            "resync_required": bool(ctx.coordination.resync_required),
            "current_slice": ctx.coordination.current_slice,
            "active_target": (
                ctx.coordination.active_target.to_dict()
                if ctx.coordination.active_target is not None
                else None
            ),
        }
    project_startup_action_routing(summary, next_command=_summary_next_command(summary))
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
    project_startup_action_routing(
        payload,
        next_command=_summary_next_command(payload),
        caller_role=caller_role,
        reviewer_override=reviewer_override,
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
