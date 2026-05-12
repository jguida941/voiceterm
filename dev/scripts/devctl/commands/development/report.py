"""Report builder for the read-only develop controller."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...review_channel.event_store import load_events, resolve_artifact_paths
from ...runtime.development_collaboration_profiles import (
    AgentCollaborationProfile,
    CollaborationRoleCountRequest,
    CollaborationStopAnchorRequest,
    build_agent_collaboration_profile,
)
from ...runtime.development_collaboration_modes import collaboration_mode_report
from ...runtime.development_packet_pressure import packet_pressure_report
from ...runtime.development_team import build_default_development_topology
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL
from ...runtime.master_plan_store import read_plan_rows_jsonl
from ...runtime.reviewer_response_shape import reviewer_response_shape_for_gate
from ...runtime.session_activity_log import session_activity_log_ref
from .actions import resolve_action
from .actor_resolution import resolve_actor
from .attention_commands import (
    next_commands_with_attention,
    peer_mind_alias_warnings,
)
from .campaign import campaign_report
from .continuation import continuation_signal, watcher_lease_status
from .design_preflight import build_design_preflight
from .final_response_gate import enforce_final_response_gate
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
from .packet_attention import review_state_payload
from .packet_debt import packet_debt_payload
from .peer_mind import peer_mind_snapshots
from .report_context import (
    orchestration_dashboard as _orchestration_dashboard,
    packet_attention_context,
    packet_ingestion_next_command,
)
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
    terminal_packet_receipts, packet_attention = packet_attention_context(
        review_state,
        rows=rows,
        agent=actor,
    )
    blockers, warnings = _action_findings(action, args)
    base_next_commands = _next_commands(action)
    required_checks = _required_checks(action)
    runtime = runtime_snapshot_from_review_state(
        review_state,
        repo_root=REPO_ROOT,
        actor=actor,
        actor_source=actor_source,
    )
    dashboard = _orchestration_dashboard(REPO_ROOT)
    orchestration = orchestration_snapshot(
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
    packet_pressure_result = packet_pressure_report(
        review_state,
        rows=rows,
        actor=actor,
        terminal_receipt_by_packet=terminal_packet_receipts,
    )
    packet_pressure, classifications, ingestion_decision = packet_pressure_result[:3]
    packet_ingest_decisions = (
        packet_pressure_result[3] if len(packet_pressure_result) > 3 else ()
    )
    next_commands = next_commands_with_attention(
        base_next_commands,
        packet_attention=packet_attention,
        peer_minds=peer_minds,
    )
    decision_command = packet_ingestion_next_command(ingestion_decision)
    if not decision_command and action == "audit-packets":
        decision_command = str(ingestion_decision.get("next_command") or "").strip()
    if decision_command:
        next_commands = tuple(dict.fromkeys((decision_command, *next_commands)))
    collaboration_mode = collaboration_mode_report(
        requested_mode=getattr(args, "collaboration_mode", ""),
        requested_role_preset=getattr(args, "role_preset", ""),
        max_workers=int(getattr(args, "max_workers", 0) or 0),
        chain_phases=tuple(getattr(args, "chain_phase", ()) or ()),
        dogfood=bool(getattr(args, "dogfood", False)),
        generic_agent_count=int(getattr(args, "generic_agents", 0) or 0),
        chain_scope=getattr(args, "chain_scope", ""),
        receipt_refs=tuple(getattr(args, "chain_receipt_ref", ()) or ()),
        role_counts=tuple(getattr(args, "role_count", ()) or ()),
        effective_reviewer_mode=_effective_reviewer_mode_from_review_state(
            review_state
        ),
    )
    selected_role_preset_id = str(
        collaboration_mode.get("selected_role_preset_id") or "dashboard"
    )
    collaboration_profile = build_agent_collaboration_profile(
        profile_id=getattr(args, "profile", ""),
        selected_mode_id=str(collaboration_mode.get("selected_mode_id") or "solo"),
        selected_role_preset_id=selected_role_preset_id,
        providers=tuple(getattr(args, "provider", ()) or ()),
        role_bindings=tuple(getattr(args, "role_binding", ()) or ()),
        role_counts=_profile_role_counts(args, selected_role_preset_id),
        agent_mind_providers=tuple(getattr(args, "agent_mind_provider", ()) or ()),
        remote_provider=getattr(args, "remote_provider", ""),
        architecture_agent_count=int(getattr(args, "architecture_agents", 0) or 0),
        review_agent_count=int(getattr(args, "review_agents", 0) or 0),
        source_packet_id=getattr(args, "source_packet_id", ""),
        target_packet_id=getattr(args, "target_packet_id", ""),
        stop_at_packet_id=getattr(args, "stop_at_packet", ""),
        stop_at_mp_row_id=getattr(args, "stop_at_mp_row", ""),
        source_ref=getattr(args, "source_ref", ""),
        target_ref=getattr(args, "target_ref", ""),
        max_workers=int(getattr(args, "max_workers", 0) or 0),
        emit_template=bool(getattr(args, "emit_profile_template", False)),
        review_state=review_state,
        events=_review_channel_events(REPO_ROOT),
        plan_rows=rows,
    )
    collaboration_mode["profile"] = collaboration_profile.to_dict()
    collaboration_mode["profile_contract_refs"] = _profile_contract_refs(
        collaboration_profile
    )
    warnings = (*warnings, *collaboration_profile.validation_warnings)
    if (
        action == "collaboration-profile"
        and bool(getattr(args, "validate_profile", False))
        and not collaboration_profile.ok
    ):
        blockers = (*blockers, *collaboration_profile.validation_errors)
    mode_chain = collaboration_mode.get("mode_chain")
    if (
        _mode_chain_errors_should_block(action, args)
        and isinstance(mode_chain, Mapping)
        and mode_chain.get("validation_errors")
    ):
        blockers = (
            *blockers,
            *tuple(str(item) for item in mode_chain.get("validation_errors") or ()),
        )
    design_preflight = build_design_preflight(
        args=args,
        repo_root=REPO_ROOT,
        review_state=review_state,
    )
    watcher_lease = watcher_lease_status(REPO_ROOT, review_state, actor=actor)
    campaign = campaign_report(
        review_state,
        packet_attention=packet_attention,
    )
    continuation = continuation_signal(
        packet_attention=packet_attention,
        orchestration=orchestration,
        watcher_lease=watcher_lease,
        packet_pressure=packet_pressure,
        review_state=review_state,
        actor=actor,
        current_action=action,
        fallback_commands=next_commands,
    )
    final_response_gate = enforce_final_response_gate(
        continuation,
        packet_attention=packet_attention,
        orchestration=orchestration,
        next_slice_id=next_slice.slice_id,
    )
    status = status_for_report(blockers=blockers, continuation=continuation)
    summary = summary_for_action(
        action,
        blockers=blockers,
        continuation=continuation,
        lifecycle_actions=LIFECYCLE_ACTIONS,
        drain_packets=bool(getattr(args, "drain_packets", False)),
        dry_run=bool(getattr(args, "dry_run", False)),
    )
    response_text, response_text_source = _proposed_response_text_for_shape(
        args,
        summary=summary,
    )
    reviewer_response_shape = reviewer_response_shape_for_gate(
        final_response_gate,
        actor_id=actor,
        role=_runtime_role_for_actor(runtime, actor),
        session_activity_log_ref=_session_activity_log_ref_for_actor(runtime, actor),
        proposed_response_text=response_text,
        proposed_response_text_source=response_text_source,
    )

    return DevelopmentLoopReport(
        action=action,
        status=status,
        ok=not blockers,
        controller_state=_controller_state(action, args),
        summary=summary,
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
        packet_ingest_decisions=tuple(packet_ingest_decisions),
        watcher_lease=watcher_lease,
        continuation=continuation,
        final_response_gate=final_response_gate,
        reviewer_response_shape=reviewer_response_shape,
        learning=learning_snapshot(REPO_ROOT),
        discovery=discovery_snapshot(REPO_ROOT),
        required_checks=required_checks,
        next_commands=next_commands,
        next_step_command=_next_step_command_for_report(
            final_response_gate=final_response_gate,
            continuation=continuation,
            packet_attention_required=(
                packet_attention.attention_required
                and packet_attention.authority_affecting
            ),
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
        campaign=campaign,
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


def _profile_contract_refs(profile: AgentCollaborationProfile) -> dict[str, object]:
    role_count_requests: tuple[CollaborationRoleCountRequest, ...] = (
        profile.role_count_requests
    )
    stop_anchor_request: CollaborationStopAnchorRequest | None = (
        profile.stop_anchor_request
    )
    return {
        "profile_contract_id": profile.contract_id,
        "role_count_request_count": len(role_count_requests),
        "role_count_request_roles": [row.role for row in role_count_requests],
        "stop_anchor_status": (
            stop_anchor_request.status if stop_anchor_request is not None else ""
        ),
    }


def _runtime_role_for_actor(runtime: Any, actor: str) -> str:
    for row in getattr(runtime, "rows", ()) or ():
        if getattr(row, "actor_id", "") == actor:
            return str(getattr(row, "role", "") or "")
    return ""


def _session_activity_log_ref_for_actor(runtime: Any, actor: str) -> str:
    for row in getattr(runtime, "rows", ()) or ():
        if getattr(row, "actor_id", "") != actor:
            continue
        session_id = str(getattr(row, "session_id", "") or "").strip()
        if session_id:
            return session_activity_log_ref(f"{actor}:{session_id}")
    return ""


def _master_plan_payload(rows: tuple[Any, ...]) -> dict[str, object]:
    return {
        "contract_id": "MasterPlan",
        "rows": [
            row.to_dict() if hasattr(row, "to_dict") else row
            for row in rows
            if isinstance(row, Mapping) or hasattr(row, "to_dict")
        ],
    }


def _next_step_command_for_report(
    *,
    final_response_gate: Any,
    continuation: Any,
    packet_attention_required: bool,
    packet_attention_command: str,
    next_commands: tuple[str, ...],
) -> str:
    gate_command = str(
        getattr(final_response_gate, "next_required_command", "") or ""
    ).strip()
    if gate_command:
        return gate_command
    if _final_gate_is_active_edit_override(final_response_gate):
        return ""
    return str(getattr(continuation, "next_required_command", "") or "").strip() or (
        _next_step_command(
            packet_attention_required=packet_attention_required,
            packet_attention_command=packet_attention_command,
            next_commands=next_commands,
        )
    )


def _final_gate_is_active_edit_override(final_response_gate: Any) -> bool:
    if bool(getattr(final_response_gate, "allow_final_response", True)):
        return False
    if str(getattr(final_response_gate, "action", "") or "") != "continue_to_goal":
        return False
    user_action = str(getattr(final_response_gate, "user_action", "") or "")
    why_not_done = str(getattr(final_response_gate, "why_not_done", "") or "")
    return (
        "scoped implementation edits" in user_action.lower()
        or "edit-only operator override is active" in why_not_done.lower()
    )


def _operator_override_loop_intent(args: Any) -> str:
    if not bool(getattr(args, "operator_override", False)):
        return ""
    if _operator_override_packet_id(args):
        return "packet"
    if _operator_override_plan_ref(args):
        return "plan"
    return ""


def _operator_override_plan_ref(args: Any) -> str:
    if not bool(getattr(args, "operator_override", False)):
        return ""
    return str(getattr(args, "slice_id", "") or "").strip()


def _operator_override_packet_id(args: Any) -> str:
    if not bool(getattr(args, "operator_override", False)):
        return ""
    return str(getattr(args, "packet_id", "") or "").strip()


def _controller_state(action: str, args: Any) -> str:
    if action in LIFECYCLE_ACTIONS:
        return f"read_only_{action}_preview"
    if action == "launch":
        return "read_only_launch_preview"
    if action == "design-preflight":
        if bool(getattr(args, "record_ground_truth_receipt", False)):
            return "ground_truth_receipt_recorded"
        return "read_only_design_preflight"
    if action == "campaign":
        return "read_only_remote_control_campaign"
    if action == "collaboration-profile":
        if bool(getattr(args, "validate_profile", False)):
            return "read_only_collaboration_profile_validation"
        return "read_only_collaboration_profile"
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
    if int(getattr(args, "architecture_agents", 0) or 0) < 0:
        blockers.append("--architecture-agents cannot be negative.")
    if int(getattr(args, "review_agents", 0) or 0) < 0:
        blockers.append("--review-agents cannot be negative.")
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
    if action in {
        "audit-guards",
        "audit-packets",
        "launch",
        "design-preflight",
        "campaign",
        "collaboration-profile",
    }:
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
    if action == "campaign":
        return (
            "python3 dev/scripts/devctl.py review-channel --action inbox "
            "--target claude --actor claude --status pending --terminal none --format md",
            "python3 dev/scripts/devctl.py develop next --actor codex --format md",
        )
    if action == "collaboration-profile":
        return (
            "python3 dev/scripts/devctl.py develop collaboration-profile "
            "--collaboration-mode agent_sync --role-preset architect "
            "--role-binding implementer=claude --role-binding reviewer=codex "
            "--role-binding architect=codex --role-binding watcher=claude "
            "--role-count architect=3 --role-count researcher=2 "
            "--agent-mind-provider claude --agent-mind-provider codex "
            "--architecture-agents 3 --validate-profile --format md",
        )
    return ("python3 dev/scripts/devctl.py develop next --format md",)


def _review_channel_events(repo_root: Path) -> tuple[Mapping[str, object], ...]:
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    try:
        rows = load_events(Path(artifact_paths.event_log_path))
    except (OSError, ValueError):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _next_step_command(
    *,
    packet_attention_required: bool,
    packet_attention_command: str,
    next_commands: tuple[str, ...],
) -> str:
    if packet_attention_required and packet_attention_command:
        return packet_attention_command
    return next_commands[0] if next_commands else ""


def _proposed_response_text_for_shape(
    args: Any,
    *,
    summary: str,
) -> tuple[str, str]:
    explicit = str(getattr(args, "proposed_response_text", "") or "")
    if explicit:
        return explicit, "cli_arg:proposed_response_text"
    return summary, "development_report.summary"


def _profile_role_counts(args: Any, selected_role_preset_id: str) -> tuple[object, ...]:
    """Return role counts, including the generic `--agents` shorthand."""
    role_counts = list(getattr(args, "role_count", ()) or ())
    generic_count = int(getattr(args, "generic_agents", 0) or 0)
    if generic_count > 0 and selected_role_preset_id:
        role_counts.append(f"{selected_role_preset_id}={generic_count}")
    return tuple(role_counts)


def _effective_reviewer_mode_from_review_state(
    review_state: Mapping[str, object],
) -> str:
    coordination = review_state.get("coordination_state")
    if not isinstance(coordination, Mapping):
        return ""
    return str(
        coordination.get("effective_reviewer_mode")
        or coordination.get("reviewer_mode")
        or ""
    ).strip()


def _mode_chain_errors_should_block(action: str, args: Any) -> bool:
    if action == "collaboration-profile":
        return True
    return bool(
        getattr(args, "chain_phase", ())
        or getattr(args, "dogfood", False)
        or getattr(args, "chain_scope", "")
        or getattr(args, "chain_receipt_ref", ())
    )


_next_commands_with_attention = next_commands_with_attention
_peer_mind_alias_warnings = peer_mind_alias_warnings
__all__ = ["build_report"]
