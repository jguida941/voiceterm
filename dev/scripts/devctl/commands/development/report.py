"""Report builder for the read-only develop controller."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ...config import REPO_ROOT
from ...review_channel.event_store import load_events, resolve_artifact_paths
from ...runtime.command_envelope_classification import classify_command_envelope
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
    from .report_assembly import build_report_impl

    return build_report_impl(args)


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
    current_actor: str = "",
    proxy_authority_ref: str = "",
    decision_authority_refs: tuple[str, ...] = (),
) -> str:
    """Return the next step command, refusing peer-lane and unrunnable shapes.

    v4.32 (rev_pkt_4706): proxy authority must be BOUND to the active
    decision's authority refs. Each candidate (gate, continuation, packet
    attention, campaign next) is classified; only ``same_actor_executable``
    or ``proxy_authorized_executable`` (with bound proxy) emits a command.
    """
    runnable = _final_gate_repair_command_runnable(final_response_gate)
    gate_command = str(
        getattr(final_response_gate, "next_required_command", "") or ""
    ).strip()
    if gate_command:
        gate_classification = classify_command_envelope(
            command=gate_command,
            current_actor=current_actor,
            proxy_authority_ref=proxy_authority_ref,
            decision_authority_refs=decision_authority_refs,
            repair_command_runnable=runnable,
        )
        # v4.39.1 (rev_pkt_4711): is_safe_to_render combines actor/proxy
        # check with v4.39 governed-mutation default-deny.
        if not gate_classification.is_safe_to_render:
            return ""
        return gate_command
    if _final_gate_is_active_edit_override(final_response_gate):
        return ""
    if not runnable:
        return ""
    fallback = str(
        getattr(continuation, "next_required_command", "") or ""
    ).strip() or _next_step_command(
        packet_attention_required=packet_attention_required,
        packet_attention_command=packet_attention_command,
        next_commands=next_commands,
    )
    if not fallback:
        return ""
    fallback_classification = classify_command_envelope(
        command=fallback,
        current_actor=current_actor,
        proxy_authority_ref=proxy_authority_ref,
        decision_authority_refs=decision_authority_refs,
        repair_command_runnable=runnable,
    )
    if not fallback_classification.is_safe_to_render:
        return ""
    return fallback


def _final_gate_repair_command_runnable(final_response_gate: Any) -> bool:
    """Read repair_command_runnable from the gate preserving True default.

    v4.30 link 9 (rev_pkt_4698): the field is True by default for legacy
    gates that predate the typed-blocker fields. Only an EXPLICIT False or
    a JSON-projection "false"/"0" disables runnable-command emission so the
    consumer refuses to resurrect a command from fallback sources.
    """
    value = getattr(final_response_gate, "repair_command_runnable", None)
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off"}
    return bool(value)


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
