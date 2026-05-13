"""Assembly phases for the read-only develop controller report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...config import REPO_ROOT
from ...runtime.development_team import build_default_development_topology
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL
from . import report as development_report
from .actions import resolve_action
from .actor_resolution import resolve_actor
from .attention_commands import (
    next_commands_with_attention,
    peer_mind_alias_warnings,
)
from .lifecycle import lifecycle_plan
from .models import DevelopmentLoopReport
from .next_slice import select_next_slice
from .packet_debt import packet_debt_payload
from .peer_mind import peer_mind_snapshots
from .report import (
    _action_findings,
    _controller_inputs,
    _controller_state,
    _master_plan_payload,
    _next_commands,
    _next_step_command_for_report,
    _operator_override_loop_intent,
    _operator_override_packet_id,
    _operator_override_plan_ref,
    _required_checks,
    _topology_summary,
)
from .report_assembly_collaboration import build_collaboration_mode
from .report_assembly_final import build_final_parts
from .report_context import (
    packet_attention_context,
    packet_ingestion_next_command,
)
from .runtime_snapshot import runtime_snapshot_from_review_state
from .snapshots import discovery_snapshot, learning_snapshot


@dataclass(frozen=True, slots=True)
class _ReportCore:
    action: str
    topology: Any
    rows: tuple[Any, ...]
    review_state: dict[str, object]
    actor: str
    actor_source: str
    packet_attention: Any
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    runtime: Any
    dashboard: dict[str, object]
    orchestration: Any
    next_slice: Any
    peer_minds: tuple[Any, ...]
    packet_pressure: dict[str, object]
    classifications: tuple[Any, ...]
    ingestion_decision: dict[str, object]
    packet_ingest_decisions: tuple[Any, ...]
    next_commands: tuple[str, ...]
    required_checks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _FinalParts:
    design_preflight: dict[str, object]
    watcher_lease: Any
    campaign: dict[str, object]
    continuation: Any
    final_response_gate: Any
    status: str
    summary: str
    reviewer_response_shape: Any


def build_report_impl(args: Any) -> DevelopmentLoopReport:
    """Build the read-only controller report from existing typed surfaces."""
    core = _build_core(args)
    collaboration_mode, warnings, blockers = build_collaboration_mode(
        args,
        core=core,
    )
    final = build_final_parts(
        args,
        core=core,
        blockers=blockers,
        final_parts_type=_FinalParts,
    )
    return DevelopmentLoopReport(
        action=core.action,
        status=final.status,
        ok=not blockers,
        controller_state=_controller_state(core.action, args),
        summary=final.summary,
        topology=_topology_summary(core.topology),
        next_slice=core.next_slice,
        packet_attention=core.packet_attention,
        runtime=core.runtime,
        peer_minds=core.peer_minds,
        orchestration=core.orchestration,
        collaboration_mode=collaboration_mode,
        packet_pressure=core.packet_pressure,
        selected_packet_classifications=tuple(core.classifications),
        packet_ingestion_decision=core.ingestion_decision,
        packet_ingest_decisions=tuple(core.packet_ingest_decisions),
        watcher_lease=final.watcher_lease,
        continuation=final.continuation,
        final_response_gate=final.final_response_gate,
        reviewer_response_shape=final.reviewer_response_shape,
        learning=learning_snapshot(REPO_ROOT),
        discovery=discovery_snapshot(REPO_ROOT),
        required_checks=core.required_checks,
        next_commands=core.next_commands,
        next_step_command=_next_step_command_for_report(
            final_response_gate=final.final_response_gate,
            continuation=final.continuation,
            packet_attention_required=(
                core.packet_attention.attention_required
                and core.packet_attention.authority_affecting
            ),
            packet_attention_command=core.packet_attention.required_command,
            next_commands=core.next_commands,
        ),
        lifecycle=lifecycle_plan(
            action=core.action,
            actor=core.actor,
            args=args,
            next_slice=core.next_slice,
            packet_attention=core.packet_attention,
            required_checks=core.required_checks,
        ),
        campaign=final.campaign,
        design_preflight=final.design_preflight,
        packet_debt_remediation=packet_debt_payload(
            core.action,
            args,
            repo_root=REPO_ROOT,
        ),
        blockers=blockers,
        warnings=warnings,
        inputs=_controller_inputs(
            args,
            plan_rows=len(core.rows),
            actor=core.actor,
            actor_source=core.actor_source,
        ),
    )


def _build_core(args: Any) -> _ReportCore:
    action = resolve_action(args)
    topology = build_default_development_topology()
    rows = development_report.read_plan_rows_jsonl(
        REPO_ROOT / DEFAULT_MASTER_PLAN_STORE_REL
    )
    review_state = development_report.review_state_payload(REPO_ROOT)
    actor, actor_source = resolve_actor(args, review_state)
    terminal_receipts, packet_attention = packet_attention_context(
        review_state,
        rows=rows,
        agent=actor,
    )
    blockers, warnings = _action_findings(action, args)
    runtime = runtime_snapshot_from_review_state(
        review_state,
        repo_root=REPO_ROOT,
        actor=actor,
        actor_source=actor_source,
    )
    dashboard = development_report._orchestration_dashboard(REPO_ROOT)
    orchestration = development_report.orchestration_snapshot(
        REPO_ROOT,
        review_state,
        actor=actor,
        dashboard=dashboard,
        master_plan=_master_plan_payload(rows),
        loop_intent=_operator_override_loop_intent(args),
        requested_plan_ref=_operator_override_plan_ref(args),
        requested_packet_id=_operator_override_packet_id(args),
        operator_override_requested=bool(getattr(args, "operator_override", False)),
        operator_override_reason=str(getattr(args, "override_reason", "") or ""),
        operator_override_scope=str(getattr(args, "override_scope", "edit-only") or ""),
        operator_override_by=str(getattr(args, "override_by", "operator") or ""),
    )
    next_slice = select_next_slice(
        rows,
        packet_attention=packet_attention,
        orchestration=orchestration,
    )
    peer_minds = peer_mind_snapshots(REPO_ROOT, review_state, actor=actor)
    warnings = (*warnings, *peer_mind_alias_warnings(peer_minds))
    pressure_result = development_report.packet_pressure_report(
        review_state,
        rows=rows,
        actor=actor,
        terminal_receipt_by_packet=terminal_receipts,
    )
    next_commands = _next_commands_with_ingestion(
        action=action,
        pressure_result=pressure_result,
        packet_attention=packet_attention,
        peer_minds=peer_minds,
    )
    return _ReportCore(
        action=action,
        topology=topology,
        rows=rows,
        review_state=review_state,
        actor=actor,
        actor_source=actor_source,
        packet_attention=packet_attention,
        blockers=blockers,
        warnings=warnings,
        runtime=runtime,
        dashboard=dashboard,
        orchestration=orchestration,
        next_slice=next_slice,
        peer_minds=peer_minds,
        packet_pressure=pressure_result[0],
        classifications=pressure_result[1],
        ingestion_decision=pressure_result[2],
        packet_ingest_decisions=pressure_result[3] if len(pressure_result) > 3 else (),
        next_commands=next_commands,
        required_checks=_required_checks(action),
    )


def _next_commands_with_ingestion(
    *,
    action: str,
    pressure_result: tuple[Any, ...],
    packet_attention: Any,
    peer_minds: tuple[Any, ...],
) -> tuple[str, ...]:
    ingestion_decision = pressure_result[2]
    next_commands = next_commands_with_attention(
        _next_commands(action),
        packet_attention=packet_attention,
        peer_minds=peer_minds,
    )
    decision_command = packet_ingestion_next_command(ingestion_decision)
    if not decision_command and action == "audit-packets":
        decision_command = str(ingestion_decision.get("next_command") or "").strip()
    if decision_command:
        return tuple(dict.fromkeys((decision_command, *next_commands)))
    return next_commands
