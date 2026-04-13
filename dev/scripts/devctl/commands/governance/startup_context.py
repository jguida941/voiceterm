"""devctl startup-context command implementation."""

from __future__ import annotations

import os
from dataclasses import asdict, replace

from . import startup_repair as startup_repair_flow
from ...common_io import display_path
from ...common import add_standard_output_arguments
from .common import render_governance_value_error
from .startup_context_advisory_coherence import (
    build_blocker_probe_payload,
    coerce_advisory_for_blockers,
)
from .startup_context_render import (
    publication_backlog_count,
    publication_backlog_guidance,
    render_markdown as _render_markdown,
)
from .startup_context_summary import (
    render_summary as _render_summary,
    summary_blockers as _summary_blockers,
    summary_next_command as _summary_next_command,
)
from .startup_context_recovery import (
    apply_recovery_authority_summary,
)
from ...runtime.machine_output import (
    ArtifactOutputOptions,
    emit_machine_artifact_output,
)
from ...runtime.action_routing import project_startup_action_routing
from ...runtime.conductor_capability import (
    reviewer_local_implementation_allowed,
    session_resume_command_for_role,
)
from ...runtime.startup_receipt import (
    build_startup_receipt,
    startup_receipt_path,
    write_startup_receipt,
)
from ...runtime.startup_authority import build_startup_authority_report
from ...runtime.startup_context import build_startup_context, blocks_new_implementation

_IMPLEMENTATION_STRICT_INTENT = "implementation_strict"
_REVIEWER_BOOTSTRAP_INTENT = "reviewer_bootstrap"


def _startup_authority_intent(*, caller_role: str | None, reviewer_override: bool) -> str:
    """Return the startup-authority intent for the current caller role."""
    if caller_role == "reviewer" and not reviewer_override:
        return _REVIEWER_BOOTSTRAP_INTENT
    return _IMPLEMENTATION_STRICT_INTENT


def _role_bootstrap_command(caller_role: str | None) -> str:
    normalized = str(caller_role or "").strip().lower()
    if normalized not in {"reviewer", "implementer"}:
        return ""
    return session_resume_command_for_role(normalized)


def _role_bootstrap_summary(caller_role: str | None) -> str:
    normalized = str(caller_role or "").strip().lower()
    if normalized == "reviewer":
        return (
            "Refresh the reviewer bootstrap packet first, then follow the typed "
            "checkpoint and packet-handshake instructions it emits."
        )
    if normalized == "implementer":
        return (
            "Refresh the implementer bootstrap packet first, then follow the typed "
            "checkpoint and instruction-ack path it emits."
        )
    return ""


def _role_bound_checkpoint_receipt(ctx, *, caller_role: str | None):
    """Project role-specific bootstrap guidance into checkpoint-blocked receipts."""
    role_command = _role_bootstrap_command(caller_role)
    if not role_command:
        return ctx
    if str(ctx.push_decision.next_step_command or "").strip():
        return ctx
    if str(ctx.push_decision.action or "").strip() != "await_checkpoint":
        return ctx
    if str(ctx.advisory_action or "").strip() == "repair_reviewer_loop":
        return ctx
    coordination = ctx.coordination
    if coordination is not None and bool(coordination.resync_required):
        return ctx
    push_decision = replace(
        ctx.push_decision,
        next_step_summary=_role_bootstrap_summary(caller_role),
        next_step_command=role_command,
    )
    return replace(ctx, push_decision=push_decision)


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


def _packet_inbox_agent_summary(record) -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["agent"] = str(record.agent or "")
    payload["attention_status"] = str(record.attention_status or "")
    payload["wake_reason"] = str(record.wake_reason or "")
    payload["required_command"] = str(record.required_command or "")
    payload["delivery_state"] = str(record.delivery_state or "")
    payload["current_instruction_packet_id"] = str(
        record.current_instruction_packet_id or ""
    )
    payload["latest_finding_packet_id"] = str(record.latest_finding_packet_id or "")
    payload["pending_actionable_total"] = len(record.pending_actionable_packet_ids)
    payload["expired_unresolved_total"] = len(record.expired_unresolved_packet_ids)
    return payload


def _machine_summary_packet_inbox(packet_inbox) -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["attention_revision"] = str(packet_inbox.attention_revision or "")
    payload["agents"] = [
        _packet_inbox_agent_summary(record)
        for record in packet_inbox.agents
        if (
            record.current_instruction_packet_id
            or record.latest_finding_packet_id
            or record.pending_actionable_packet_ids
            or record.expired_unresolved_packet_ids
            or str(record.attention_status or "").strip() not in {"", "none"}
        )
    ]
    return payload


def _machine_summary_coordination(coordination) -> dict[str, object]:
    payload: dict[str, object] = {}
    payload["declared_topology"] = coordination.declared_topology
    payload["observed_topology"] = coordination.observed_topology
    payload["recommended_topology"] = coordination.recommended_topology
    payload["fanout_posture"] = coordination.fanout_posture
    payload["safe_to_fanout"] = bool(coordination.safe_to_fanout)
    payload["worktree_strategy"] = coordination.worktree_strategy
    payload["resync_required"] = bool(coordination.resync_required)
    payload["current_slice"] = coordination.current_slice
    payload["active_target"] = (
        coordination.active_target.to_dict()
        if coordination.active_target is not None
        else None
    )
    return payload


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
    if getattr(ctx, "attention", None) is not None:
        summary["attention"] = asdict(ctx.attention)
    if getattr(ctx, "packet_inbox", None) is not None:
        summary["packet_inbox"] = _machine_summary_packet_inbox(ctx.packet_inbox)
    if ctx.work_intake is not None:
        summary["work_intake"] = {
            "coordination": ctx.work_intake.coordination.to_dict(),
        }
    if ctx.coordination is not None:
        summary["coordination"] = _machine_summary_coordination(ctx.coordination)
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
    authority_intent = _startup_authority_intent(
        caller_role=caller_role,
        reviewer_override=reviewer_override,
    )
    authority_report = build_startup_authority_report(
        intent=authority_intent,
        governance=governance,
        reviewer_gate=ctx.reviewer_gate,
    )
    # Codex P1 finding: advisory_action must not stay on `push_allowed`
    # when the typed summary blocker list is non-empty. The coercion has
    # to land before `build_startup_receipt` so the persisted receipt,
    # the human summary, and the machine summary all observe the same
    # consistent (advisory_action, advisory_reason) pair.
    authority_payload = _startup_authority_payload(authority_report)
    blocker_probe_payload = build_blocker_probe_payload(ctx, authority_payload)
    coerced_action, coerced_reason = coerce_advisory_for_blockers(
        ctx.advisory_action,
        ctx.advisory_reason,
        _summary_blockers(blocker_probe_payload),
    )
    if coerced_action != ctx.advisory_action or coerced_reason != ctx.advisory_reason:
        ctx = replace(
            ctx,
            advisory_action=coerced_action,
            advisory_reason=coerced_reason,
        )
    ctx = _role_bound_checkpoint_receipt(ctx, caller_role=caller_role)
    receipt = build_startup_receipt(
        ctx,
        authority_report=authority_report,
        intent_scope=authority_intent,
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
    push = governance.push_enforcement if governance is not None else None
    payload = ctx.to_dict()
    payload["checkpoint_required"] = (
        bool(push.checkpoint_required) if push is not None else False
    )
    payload["safe_to_continue_editing"] = (
        bool(push.safe_to_continue_editing) if push is not None else True
    )
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
