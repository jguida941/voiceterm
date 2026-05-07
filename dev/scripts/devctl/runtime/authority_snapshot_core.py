"""Core authority snapshot models and summary helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .authority_snapshot_actor_authority import authority_rows_for_output
from .authority_snapshot_parse_support import mapping_or_empty as _mapping
from .authority_snapshot_parse_support import string_items as _string_items
from .authority_snapshot_summary import (
    reviewer_recovery_command,
    summary_blockers,
    summary_blockers_csv,
    summary_next_command,
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
    effective_reviewer_mode: str = ""
    reviewer_freshness: str = ""
    attention_status: str = ""
    interaction_mode: str = "unresolved"
    gate_mode: str = ""
    declared_active: bool = False
    effective_active: bool = False
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
        effective_reviewer_mode=str(
            value.get("effective_reviewer_mode") or ""
        ).strip(),
        reviewer_freshness=str(value.get("reviewer_freshness") or "").strip(),
        attention_status=str(value.get("attention_status") or "").strip(),
        interaction_mode=str(value.get("interaction_mode") or "unresolved").strip(),
        gate_mode=str(value.get("gate_mode") or "").strip(),
        declared_active=bool(value.get("declared_active", False)),
        effective_active=bool(value.get("effective_active", False)),
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
