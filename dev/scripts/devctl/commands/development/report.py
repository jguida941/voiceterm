"""Report builder for the read-only develop controller."""

from __future__ import annotations

from typing import Any

from ...config import REPO_ROOT
from ...runtime.development_collaboration_modes import collaboration_mode_report
from ...runtime.development_packet_pressure import packet_pressure_report
from ...runtime.development_team import build_default_development_topology
from ...runtime.dashboard_snapshot_authority import build_dashboard_snapshot
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL
from ...runtime.master_plan_store import read_plan_rows_jsonl
from .actions import resolve_action
from .actor_resolution import resolve_actor
from .attention_commands import (
    next_commands_with_attention,
    peer_mind_alias_warnings,
)
from .continuation import continuation_signal, watcher_lease_status
from .design_preflight import build_design_preflight
from .lifecycle import LIFECYCLE_ACTIONS
from .lifecycle import lifecycle_next_commands, lifecycle_plan
from .models import (
    DevelopmentControllerInputs,
    DevelopmentLoopReport,
    DevelopmentTopologySummary,
    DevelopmentWorkstreamSummary,
    scaling_summary_from_contract,
)
from .next_slice import select_next_slice
from .orchestration_inputs import orchestration_snapshot
from .packet_attention import packet_attention_from_review_state, review_state_payload
from .packet_debt import packet_debt_payload
from .peer_mind import peer_mind_snapshots
from .runtime_snapshot import runtime_snapshot_from_review_state
from .snapshots import discovery_snapshot, learning_snapshot
from .status_summary import status_for_report, summary_for_action


def build_report(args: Any) -> DevelopmentLoopReport:
    """Build the read-only controller report from existing typed surfaces."""
    action = resolve_action(args)
    topology = build_default_development_topology()
    rows = read_plan_rows_jsonl(REPO_ROOT / DEFAULT_MASTER_PLAN_STORE_REL)
    review_state = review_state_payload(REPO_ROOT)
    actor, actor_source = resolve_actor(args, review_state)
    packet_attention = packet_attention_from_review_state(
        review_state,
        rows=rows,
        agent=actor,
    )
    blockers, warnings = _action_findings(action, args)
    base_next_commands = _next_commands(action)
    next_slice = select_next_slice(rows, packet_attention=packet_attention)
    required_checks = _required_checks(action)
    runtime = runtime_snapshot_from_review_state(
        review_state,
        repo_root=REPO_ROOT,
        actor=actor,
        actor_source=actor_source,
    )
    dashboard = _orchestration_dashboard(REPO_ROOT)
    peer_minds = peer_mind_snapshots(REPO_ROOT, review_state, actor=actor)
    warnings = (*warnings, *peer_mind_alias_warnings(peer_minds))
    next_commands = next_commands_with_attention(
        base_next_commands,
        packet_attention=packet_attention,
        peer_minds=peer_minds,
    )
    orchestration = orchestration_snapshot(
        REPO_ROOT,
        review_state,
        actor=actor,
        dashboard=dashboard,
    )
    collaboration_mode = collaboration_mode_report(
        requested_mode=getattr(args, "collaboration_mode", ""),
        requested_role_preset=getattr(args, "role_preset", ""),
        max_workers=int(getattr(args, "max_workers", 0) or 0),
    )
    packet_pressure, classifications, ingestion_decision = packet_pressure_report(
        review_state,
        rows=rows,
        actor=actor,
    )
    design_preflight = build_design_preflight(
        args=args,
        repo_root=REPO_ROOT,
        review_state=review_state,
    )
    watcher_lease = watcher_lease_status(REPO_ROOT, review_state, actor=actor)
    continuation = continuation_signal(
        packet_attention=packet_attention,
        orchestration=orchestration,
        watcher_lease=watcher_lease,
        packet_pressure=packet_pressure,
        current_action=action,
        fallback_commands=next_commands,
    )

    status = status_for_report(blockers=blockers, continuation=continuation)
    return DevelopmentLoopReport(
        action=action,
        status=status,
        ok=not blockers,
        controller_state=_controller_state(action, args),
        summary=summary_for_action(
            action,
            blockers=blockers,
            continuation=continuation,
            lifecycle_actions=LIFECYCLE_ACTIONS,
            drain_packets=bool(getattr(args, "drain_packets", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
        ),
        topology=_topology_summary(topology),
        next_slice=next_slice,
        packet_attention=packet_attention,
        runtime=runtime,
        peer_minds=peer_minds,
        orchestration=orchestration,
        collaboration_mode=collaboration_mode,
        packet_pressure=packet_pressure,
        selected_packet_classifications=tuple(classifications),
        packet_ingestion_decision=ingestion_decision,
        watcher_lease=watcher_lease,
        continuation=continuation,
        learning=learning_snapshot(REPO_ROOT),
        discovery=discovery_snapshot(REPO_ROOT),
        required_checks=required_checks,
        next_commands=next_commands,
        next_step_command=_next_step_command(
            packet_attention_required=packet_attention.attention_required,
            packet_attention_command=packet_attention.required_command,
            next_commands=next_commands,
        ),
        lifecycle=lifecycle_plan(
            action=action,
            actor=actor,
            args=args,
            next_slice=next_slice,
            packet_attention=packet_attention,
            required_checks=required_checks,
        ),
        design_preflight=design_preflight,
        packet_debt_remediation=packet_debt_payload(
            action,
            args,
            repo_root=REPO_ROOT,
        ),
        blockers=blockers,
        warnings=warnings,
        inputs=_controller_inputs(
            args,
            plan_rows=len(rows),
            actor=actor,
            actor_source=actor_source,
        ),
    )


def _orchestration_dashboard(repo_root) -> dict[str, Any]:
    """Return the dashboard-backed blocker view used by agent-loop, if available."""
    try:
        return build_dashboard_snapshot(
            repo_root=repo_root,
            view="overview",
            role="dashboard",
            include_review_state=False,
        )
    except Exception:  # broad-except: allow reason=dashboard snapshot is advisory context for /develop fallback=omit orchestration dashboard
        return {}

def _controller_state(action: str, args: Any) -> str:
    if action in LIFECYCLE_ACTIONS:
        return f"read_only_{action}_preview"
    if action == "launch":
        return "read_only_launch_preview"
    if action == "design-preflight":
        if bool(getattr(args, "record_ground_truth_receipt", False)):
            return "ground_truth_receipt_recorded"
        return "read_only_design_preflight"
    if action in {"pause", "resume"}:
        return f"read_only_{action}_preview"
    if action == "audit-guards":
        return "read_only_guard_audit"
    if action == "audit-packets":
        if bool(getattr(args, "drain_packets", False)):
            if bool(getattr(args, "dry_run", False)):
                return "read_only_packet_debt_drain_preview"
            return "packet_debt_drain"
        return "read_only_packet_debt_audit"
    return "read_only"


def _controller_inputs(
    args: Any,
    *,
    plan_rows: int,
    actor: str,
    actor_source: str,
) -> DevelopmentControllerInputs:
    return DevelopmentControllerInputs(
        master_plan_store=DEFAULT_MASTER_PLAN_STORE_REL,
        plan_rows=plan_rows,
        actor=actor,
        requested_actor=str(getattr(args, "actor", "auto") or "auto"),
        actor_source=actor_source,
        fleet=str(getattr(args, "fleet", "default") or "default"),
        max_cycles=int(getattr(args, "max_cycles", 1) or 1),
        max_workers=int(getattr(args, "max_workers", 0) or 0),
        dry_run=bool(getattr(args, "dry_run", False)),
        drain_packets=bool(getattr(args, "drain_packets", False)),
    )


def _topology_summary(topology) -> DevelopmentTopologySummary:
    return DevelopmentTopologySummary(
        contract_id=topology.contract_id,
        schema_version=topology.schema_version,
        topology_id=topology.topology_id,
        workstreams=tuple(
            DevelopmentWorkstreamSummary(
                workstream_id=item.workstream_id,
                display_name=item.display_name,
                mutation_policy=item.mutation_policy,
                runtime_role=item.runtime_role,
            )
            for item in topology.workstreams
        ),
        assignment_policy=topology.assignment_policy,
        provider_policy=topology.provider_policy,
        mutation_policy=topology.mutation_policy,
        default_worker_fanout=topology.default_worker_fanout,
        scaling=scaling_summary_from_contract(topology.scaling),
    )


def _action_findings(action: str, args: Any) -> tuple[tuple[str, ...], tuple[str, ...]]:
    blockers: list[str] = []
    warnings: list[str] = []
    fleet = str(getattr(args, "fleet", "default") or "default")
    max_cycles = int(getattr(args, "max_cycles", 1) or 1)
    max_workers = int(getattr(args, "max_workers", 0) or 0)

    if fleet != "default":
        blockers.append("Only the default DevelopmentModeTopology fleet is implemented.")
    if max_cycles < 1:
        blockers.append("--max-cycles must be at least 1.")
    if max_workers < 0:
        blockers.append("--max-workers cannot be negative.")
    if bool(getattr(args, "drain_packets", False)) and action != "audit-packets":
        blockers.append("--drain-packets is only valid with audit-packets.")
    if (
        bool(getattr(args, "drain_packets", False))
        and bool(getattr(args, "dry_run", False))
        and action == "audit-packets"
    ):
        warnings.append("--dry-run suppresses packet debt writer execution.")
    if action == "launch":
        warnings.append(
            "launch is a read-only controller cycle preview; no worker process is spawned"
        )
        if max_cycles > 1:
            warnings.append(
                "multi-cycle launch is not active yet; this command renders one bounded report"
            )
    if action in {"pause", "resume"}:
        warnings.append(
            f"{action} is report-only until the typed controller-state writer lands"
        )
    if action in LIFECYCLE_ACTIONS:
        warnings.append(
            f"{action} is a lifecycle preview; no lease, commit, reset, or packet write occurs"
        )
    return tuple(blockers), tuple(warnings)


def _required_checks(action: str) -> tuple[str, ...]:
    checks = [
        "python3 dev/scripts/checks/check_active_plan_sync.py",
        "python3 dev/scripts/checks/check_platform_contract_closure.py --format md",
        "python3 dev/scripts/checks/check_governance_closure.py --format md",
        "python3 dev/scripts/checks/check_multi_agent_sync.py",
    ]
    if action in {"audit-guards", "audit-packets", "launch", "design-preflight"}:
        checks.append("python3 dev/scripts/devctl.py probe-report --format md")
        checks.append("python3 dev/scripts/devctl.py governance-quality-feedback --format md")
    if action == "design-preflight":
        checks.append(
            "python3 dev/scripts/checks/check_ground_truth_probe_gate.py --format md"
        )
    return tuple(checks)


def _next_commands(action: str) -> tuple[str, ...]:
    lifecycle_commands = lifecycle_next_commands(action)
    if lifecycle_commands is not None:
        return lifecycle_commands
    if action == "next":
        return ("python3 dev/scripts/devctl.py develop launch --dry-run --max-cycles 1",)
    if action == "audit-guards":
        return (
            "python3 dev/scripts/devctl.py governance-quality-feedback --format md",
            "python3 dev/scripts/devctl.py probe-report --format md",
        )
    if action == "audit-packets":
        return (
            "python3 dev/scripts/checks/probe_packet_carry_forward_debt.py --format md",
            "python3 dev/scripts/devctl.py develop next --format md",
        )
    if action == "design-preflight":
        return (
            "python3 dev/scripts/devctl.py develop design-preflight "
            "--topic \"<state/proof topic>\" --record-ground-truth-receipt --format json",
            "python3 dev/scripts/checks/check_ground_truth_probe_gate.py --format md",
        )
    if action == "launch":
        return (
            "python3 dev/scripts/devctl.py review-channel --action sync-status --terminal none --format md",
            "python3 dev/scripts/devctl.py develop next --format md",
        )
    return ("python3 dev/scripts/devctl.py develop next --format md",)


def _next_step_command(
    *,
    packet_attention_required: bool,
    packet_attention_command: str,
    next_commands: tuple[str, ...],
) -> str:
    if packet_attention_required and packet_attention_command:
        return packet_attention_command
    return next_commands[0] if next_commands else ""


_next_commands_with_attention = next_commands_with_attention
_peer_mind_alias_warnings = peer_mind_alias_warnings
__all__ = ["build_report"]
