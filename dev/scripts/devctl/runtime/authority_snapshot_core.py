"""Core authority snapshot models and summary helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .authority_snapshot_actor_authority import authority_rows_for_output
from .authority_snapshot_parse_support import mapping_or_empty as _mapping
from .authority_snapshot_parse_support import string_items as _string_items
from .post_checkpoint_dirty_support import (
    COMMIT_CHECKPOINT_COMMAND,
    requires_commit_before_push,
)
from .review_state_collaboration_models import (
    ActorAuthorityState,
    actor_authorities_from_value,
)
from .review_state_packet_models import (
    AgentAttentionRecord,
    agent_attention_record_from_mapping,
)
from .surface_provenance import attach_surface_provenance, surface_provenance_kwargs

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


@dataclass(frozen=True, slots=True)
class AuthorityPacketTarget:
    """Current packet/inbox target that most directly affects the next turn."""

    attention_revision: str = ""
    agent: str = ""
    attention_status: str = ""
    wake_reason: str = ""
    required_command: str = ""
    delivery_state: str = ""
    current_instruction_packet_id: str = ""
    latest_finding_packet_id: str = ""
    pending_actionable_total: int = 0
    expired_unresolved_total: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuthoritySnapshot:
    """One reduced authority contract for turn-sized AI guidance."""

    schema_version: int = 1
    contract_id: str = "AuthoritySnapshot"
    snapshot_id: str = ""
    zref: str = ""
    source_identity: dict[str, str] = field(default_factory=dict)
    source_contract: str = ""
    source_command: str = ""
    observed_fields: tuple[str, ...] = ()
    inferred_fields: tuple[str, ...] = ()
    coordination_state: str = "ready"
    root_cause: str = ""
    required_action: str = ""
    next_command: str = ""
    actor_role: str = ""
    actor_identity: str = ""
    safe_to_continue: bool = True
    reviewer_mode: str = ""
    reviewer_freshness: str = ""
    attention_status: str = ""
    observed_control_topology: str = ""
    implementation_permission: str = ""
    current_instruction_revision: str = ""
    implementer_ack_state: str = ""
    resync_required: bool = False
    current_slice: str = ""
    active_target_path: str = ""
    allowed_actions: tuple[str, ...] = ()
    blocked_actions: tuple[str, ...] = ()
    packet_target: AuthorityPacketTarget | None = None
    mutation_owner: str = ""
    verification_owner: str = ""
    verification_status: str = "inactive"
    watcher_owner: str = ""
    watcher_status: str = "inactive"
    actor_capabilities: tuple[str, ...] = ()
    actor_authorities: tuple[ActorAuthorityState, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["allowed_actions"] = list(self.allowed_actions)
        payload["blocked_actions"] = list(self.blocked_actions)
        payload["actor_capabilities"] = list(self.actor_capabilities)
        payload["actor_authorities"] = authority_rows_for_output(
            payload.get("actor_authorities", ())
        )
        if self.packet_target is None:
            payload.pop("packet_target", None)
        else:
            payload["packet_target"] = self.packet_target.to_dict()
        return attach_surface_provenance(payload)


def authority_snapshot_from_mapping(value: object) -> AuthoritySnapshot | None:
    """Deserialize an authority snapshot from a JSON-like mapping."""
    if not isinstance(value, Mapping):
        return None
    packet_target = authority_packet_target_from_mapping(value.get("packet_target"))
    return AuthoritySnapshot(
        schema_version=int(value.get("schema_version") or 1),
        contract_id=str(value.get("contract_id") or "AuthoritySnapshot").strip(),
        **surface_provenance_kwargs(value),
        coordination_state=str(value.get("coordination_state") or "ready").strip(),
        root_cause=str(value.get("root_cause") or "").strip(),
        required_action=str(value.get("required_action") or "").strip(),
        next_command=str(value.get("next_command") or "").strip(),
        actor_role=str(value.get("actor_role") or "").strip(),
        actor_identity=str(value.get("actor_identity") or "").strip(),
        safe_to_continue=bool(value.get("safe_to_continue", True)),
        reviewer_mode=str(value.get("reviewer_mode") or "").strip(),
        reviewer_freshness=str(value.get("reviewer_freshness") or "").strip(),
        attention_status=str(value.get("attention_status") or "").strip(),
        observed_control_topology=str(
            value.get("observed_control_topology") or ""
        ).strip(),
        implementation_permission=str(
            value.get("implementation_permission") or ""
        ).strip(),
        current_instruction_revision=str(
            value.get("current_instruction_revision") or ""
        ).strip(),
        implementer_ack_state=str(value.get("implementer_ack_state") or "").strip(),
        resync_required=bool(value.get("resync_required", False)),
        current_slice=str(value.get("current_slice") or "").strip(),
        active_target_path=str(value.get("active_target_path") or "").strip(),
        allowed_actions=_string_items(value.get("allowed_actions")),
        blocked_actions=_string_items(value.get("blocked_actions")),
        packet_target=packet_target,
        mutation_owner=str(value.get("mutation_owner") or "").strip(),
        verification_owner=str(value.get("verification_owner") or "").strip(),
        verification_status=str(value.get("verification_status") or "inactive").strip(),
        watcher_owner=str(value.get("watcher_owner") or "").strip(),
        watcher_status=str(value.get("watcher_status") or "inactive").strip(),
        actor_capabilities=_string_items(value.get("actor_capabilities")),
        actor_authorities=actor_authorities_from_value(value.get("actor_authorities")),
    )


def authority_packet_target_from_mapping(value: object) -> AuthorityPacketTarget | None:
    """Deserialize one authority packet target row."""
    record = agent_attention_record_from_mapping(value)
    if record is None:
        return None
    return authority_packet_target_from_attention_record(record)


def authority_packet_target_from_attention_record(
    record: AgentAttentionRecord,
    *,
    attention_revision: str = "",
) -> AuthorityPacketTarget:
    return AuthorityPacketTarget(
        attention_revision=attention_revision or record.attention_revision,
        agent=record.agent,
        attention_status=record.attention_status,
        wake_reason=record.wake_reason,
        required_command=record.required_command,
        delivery_state=record.delivery_state,
        current_instruction_packet_id=record.current_instruction_packet_id,
        latest_finding_packet_id=record.latest_finding_packet_id,
        pending_actionable_total=len(record.pending_actionable_packet_ids),
        expired_unresolved_total=len(record.expired_unresolved_packet_ids),
    )


def summary_blockers(ctx_dict: Mapping[str, object]) -> tuple[str, ...]:
    """Return the canonical startup blocker labels."""
    blockers: list[str] = []

    authority = _mapping(ctx_dict.get("startup_authority"))
    if authority and not bool(authority.get("ok", False)):
        blockers.append("startup_authority")

    governance = _mapping(ctx_dict.get("governance"))
    push_enforcement = _mapping(governance.get("push_enforcement"))
    if bool(push_enforcement.get("checkpoint_required", False)):
        blockers.append("checkpoint_required")
    elif push_enforcement and not bool(
        push_enforcement.get("safe_to_continue_editing", True)
    ):
        blockers.append("continuation_blocked")
    if requires_commit_before_push(push_enforcement):
        blockers.append("post_checkpoint_dirty_worktree")

    reviewer_gate = _mapping(ctx_dict.get("reviewer_gate"))
    if bool(reviewer_gate.get("implementation_blocked", False)) and not bool(
        reviewer_gate.get("review_gate_allows_push", False)
    ):
        block_reason = str(
            reviewer_gate.get("implementation_block_reason") or ""
        ).strip()
        blockers.append(block_reason or "reviewer_gate")

    coordination = _mapping(ctx_dict.get("coordination"))
    if bool(coordination.get("resync_required", False)):
        blockers.append("coordination_resync_required")

    permission = str(ctx_dict.get("implementation_permission") or "").strip()
    if permission in {"blocked", "suspended"}:
        blockers.append(f"implementation_permission_{permission}")

    return tuple(dict.fromkeys(blockers))


def summary_blockers_csv(ctx_dict: Mapping[str, object]) -> str:
    """Return the startup blocker labels as a CSV string."""
    blockers = summary_blockers(ctx_dict)
    return ",".join(blockers) if blockers else "none"


def reviewer_recovery_command(ctx_dict: Mapping[str, object]) -> str:
    """Return the preferred review-loop recovery command when startup says so."""
    action = str(ctx_dict.get("advisory_action") or "").strip()
    if action != "repair_reviewer_loop":
        return ""
    reviewer_gate = _mapping(ctx_dict.get("reviewer_gate"))
    recovery_command = str(reviewer_gate.get("recovery_command") or "").strip()
    if recovery_command:
        return recovery_command
    if not bool(reviewer_gate.get("implementation_blocked", False)):
        return ""
    if bool(reviewer_gate.get("review_gate_allows_push", False)):
        return ""
    block_reason = str(reviewer_gate.get("implementation_block_reason") or "").strip()
    try:
        from ..review_channel.peer_recovery import STALE_PEER_RECOVERY
    except ImportError:
        return _REVIEW_STATUS_COMMAND
    entry = STALE_PEER_RECOVERY.get(block_reason, {})
    command = str(entry.get("recommended_command") or "").strip()
    return command or _REVIEW_STATUS_COMMAND


def summary_next_command(ctx_dict: Mapping[str, object]) -> str:
    """Return the canonical next command for the current startup payload."""
    blockers = summary_blockers(ctx_dict)
    if not blockers:
        push_decision = _mapping(ctx_dict.get("push_decision"))
        if str(push_decision.get("action") or "").strip() == "run_devctl_push":
            next_step_command = str(
                push_decision.get("next_step_command") or ""
            ).strip()
            if next_step_command:
                return next_step_command
        return _CONTEXT_GRAPH_BOOTSTRAP_COMMAND

    recovery_authority = _mapping(ctx_dict.get("recovery_authority"))
    recovery_action = str(recovery_authority.get("decision_action_id") or "").strip()
    recovery_command = str(recovery_authority.get("command") or "").strip()
    if recovery_action == "cut_checkpoint" and recovery_command:
        return recovery_command

    if "post_checkpoint_dirty_worktree" in blockers:
        return COMMIT_CHECKPOINT_COMMAND

    reviewer_command = reviewer_recovery_command(ctx_dict)
    if reviewer_command:
        return reviewer_command

    coordination = _mapping(ctx_dict.get("coordination"))
    if bool(coordination.get("resync_required", False)):
        return _REVIEW_STATUS_COMMAND
    if any(blocker.startswith("implementation_permission_") for blocker in blockers):
        return _REVIEW_STATUS_COMMAND

    push_decision = _mapping(ctx_dict.get("push_decision"))
    next_step_command = str(push_decision.get("next_step_command") or "").strip()
    if next_step_command:
        return next_step_command
    if str(push_decision.get("action") or "").strip() == "await_checkpoint":
        return f"checkpoint current slice, then rerun {_SUMMARY_RERUN_COMMAND}"
    return f"resolve blockers, then rerun {_SUMMARY_RERUN_COMMAND}"


def _coordination_state(
    inputs: tuple[str, str, str, bool, str, str, str],
) -> str:
    (
        reviewer_mode,
        attention_status,
        implementation_permission,
        resync_required,
        current_instruction_revision,
        implementer_ack_state,
        root_cause,
    ) = inputs
    if resync_required:
        return "resync_required"
    if (
        reviewer_mode == "active_dual_agent"
        and current_instruction_revision
        and implementer_ack_state == "stale"
    ):
        return "handshake_stale"
    if implementation_permission in {"blocked", "suspended"}:
        return "implementation_blocked"
    if attention_status in {
        "reviewer_overdue",
        "reviewer_heartbeat_stale",
        "review_loop_relaunch_required",
        "bridge_contract_error",
        "runtime_missing",
    }:
        return "degraded"
    if reviewer_mode == "single_agent":
        if "dual-agent heartbeat enforcement is suspended" in root_cause:
            return "single_agent_authoritative"
        return "single_agent"
    return "ready"


def _safe_to_continue(
    *,
    coordination_state: str,
    implementation_permission: str,
    allowed_actions: tuple[str, ...],
) -> bool:
    if "implementation.edit" in allowed_actions:
        return True
    if allowed_actions:
        return False
    if implementation_permission in {"blocked", "suspended"}:
        return False
    return coordination_state in {"ready", "single_agent", "single_agent_authoritative"}
