"""Assembly phases for the read-only develop controller report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...config import REPO_ROOT
from ...runtime.development_team import build_default_development_topology
from ...runtime.finding_backlog import load_finding_backlog
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL
from ...triage.findings_priority_models import RankedFinding
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
from .operator_command_wrappers import build_operator_command_wrappers
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


_SEVERITY_RANK_MAP: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def _finding_source_stale_blocker(reason_detail: str) -> "DevelopmentNextSlice":
    """Typed fail-loud blocker when FindingBacklog source is unavailable or stale.

    Per codex rev_pkt_4513 (review_failed SLICE-Y 148f4c4e): soft-fall to plan rows
    silently recreates the original silent-fallback bug. When the canonical finding
    source cannot be loaded, develop next must surface an attention_required slice
    naming the failure mode instead of silently selecting ordinary plan rows.
    """
    from .models import DevelopmentNextSlice

    return DevelopmentNextSlice(
        slice_id="finding-source-stale-blocker",
        source="FindingBacklog.load",
        title="FindingBacklog unavailable; bug-priority preemption cannot evaluate",
        target_ref=reason_detail,
        status="attention_required",
        reason=(
            "FindingBacklog source unavailable or stale: "
            f"{reason_detail}. develop next refuses silent fallback to ordinary "
            "plan rows; restore finding_reviews source or post an explicit typed "
            "bypass before selecting a plan slice."
        ),
    )


def _ranked_findings_for_develop_next() -> tuple[
    tuple[RankedFinding, ...], "DevelopmentNextSlice | None"
]:
    """SLICE-Y wire: load FindingBacklog + project minimal RankedFinding tuple.

    Per codex rev_pkt_4495/rev_pkt_4511 + repair rev_pkt_4513 (Role-flip cycle 2):
    feed select_next_slice with critical/high open findings derived from the
    canonical FindingBacklog source. On stale/missing source, fail-loud with a
    typed DevelopmentNextSlice blocker (no silent fallback to plan rows).

    Returns (ranked_findings, stale_blocker). Caller inspects stale_blocker; if
    not None, that slice preempts select_next_slice entirely.

    Composes with SLICE-X helper; does NOT create a parallel bug queue.
    """
    try:
        backlog = load_finding_backlog(
            repo_root=REPO_ROOT, governance=None, max_rows=5_000
        )
    except (FileNotFoundError, OSError, ValueError) as exc:
        return (), _finding_source_stale_blocker(
            f"{type(exc).__name__}: {exc}"[:200]
        )
    sorted_findings = sorted(
        backlog.open_findings,
        key=lambda finding: _SEVERITY_RANK_MAP.get(finding.severity, 99),
    )
    ranked: list[RankedFinding] = []
    for index, finding in enumerate(sorted_findings, start=1):
        primary_file = finding.file_path or ""
        check_label = finding.check_id or finding.rule_id or ""
        ranked.append(
            RankedFinding(
                rank=index,
                qid=finding.finding_id,
                heading=check_label,
                severity=finding.severity,
                severity_rank=_SEVERITY_RANK_MAP.get(finding.severity, 99),
                status="confirmed_issue",
                summary=f"{check_label} at {primary_file}" if primary_file else check_label,
                resolution_state="open",
                primary_file=primary_file,
                file_refs=(primary_file,) if primary_file else (),
                matched_file_refs=(),
                max_fan_out=0,
                fan_out_by_file=(),
            )
        )
    return tuple(ranked), None


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
    next_step_command = _next_step_command_for_report(
        final_response_gate=final.final_response_gate,
        continuation=final.continuation,
        packet_attention_required=(
            core.packet_attention.attention_required
            and core.packet_attention.authority_affecting
        ),
        packet_attention_command=core.packet_attention.required_command,
        next_commands=core.next_commands,
    )
    operator_command_wrappers = build_operator_command_wrappers(
        _operator_command_sources(
            core=core,
            final=final,
            next_step_command=next_step_command,
        )
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
        operator_command_wrappers=operator_command_wrappers,
        next_step_command=next_step_command,
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


def _operator_command_sources(
    *,
    core: _ReportCore,
    final: _FinalParts,
    next_step_command: str,
) -> tuple[tuple[str, str], ...]:
    sources: list[tuple[str, str]] = [
        ("next_step_command", next_step_command),
        (
            "packet_attention.required_command",
            str(getattr(core.packet_attention, "required_command", "") or ""),
        ),
        (
            "continuation.next_required_command",
            str(getattr(final.continuation, "next_required_command", "") or ""),
        ),
        (
            "continuation.required_packet_command",
            str(getattr(final.continuation, "required_packet_command", "") or ""),
        ),
        (
            "final_response_gate.next_required_command",
            _object_field(final.final_response_gate, "next_required_command"),
        ),
        (
            "final_response_gate.required_packet_command",
            _object_field(final.final_response_gate, "required_packet_command"),
        ),
        (
            "reviewer_response_shape.next_required_command",
            _object_field(final.reviewer_response_shape, "next_required_command"),
        ),
    ]
    sources.extend(
        (f"required_checks[{index}]", command)
        for index, command in enumerate(core.required_checks)
    )
    sources.extend(
        (f"next_commands[{index}]", command)
        for index, command in enumerate(core.next_commands)
    )
    campaign = final.campaign
    for key in (
        "pending_packet_required_command",
        "codex_next_command",
        "claude_next_command",
    ):
        sources.append((f"campaign.{key}", _object_field(campaign, key)))
    roles = _raw_object_field(campaign, "roles", default=())
    if isinstance(roles, tuple):
        for index, role in enumerate(roles):
            sources.append(
                (
                    f"campaign.roles[{index}].next_command",
                    _object_field(role, "next_command"),
                )
            )
    return tuple(sources)


def _object_field(value: Any, key: str, *, default: object = "") -> str:
    return str(_raw_object_field(value, key, default=default) or "")


def _raw_object_field(value: Any, key: str, *, default: object = "") -> object:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


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
    ranked_findings, finding_source_blocker = _ranked_findings_for_develop_next()
    if finding_source_blocker is not None:
        next_slice = finding_source_blocker
    else:
        next_slice = select_next_slice(
            rows,
            packet_attention=packet_attention,
            orchestration=orchestration,
            ranked_findings=ranked_findings,
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
