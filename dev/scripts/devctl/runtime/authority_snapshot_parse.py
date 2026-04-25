"""Parsing helpers for the authority snapshot contract."""

from __future__ import annotations

from collections.abc import Mapping

from .authority_snapshot_core import AuthorityPacketTarget, AuthoritySnapshot
from .authority_snapshot_parse_support import string_items as _string_items
from .collaboration_wake_contract import LoopAutonomyState
from .review_state_collaboration_models import actor_authorities_from_value
from .review_state_packet_models import agent_attention_record_from_mapping


def authority_snapshot_from_mapping(value: object) -> AuthoritySnapshot | None:
    """Deserialize an authority snapshot from a JSON-like mapping."""
    if not isinstance(value, Mapping):
        return None
    packet_target = authority_packet_target_from_mapping(value.get("packet_target"))
    loop_autonomy = LoopAutonomyState.from_mapping(value) or LoopAutonomyState()
    return AuthoritySnapshot(
        schema_version=int(value.get("schema_version") or 1),
        contract_id=str(value.get("contract_id") or "AuthoritySnapshot").strip(),
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
        mutation_wake_mode=str(value.get("mutation_wake_mode") or "unknown").strip()
        or "unknown",
        verification_wake_mode=str(
            value.get("verification_wake_mode") or "unknown"
        ).strip()
        or "unknown",
        watcher_wake_mode=str(value.get("watcher_wake_mode") or "unknown").strip()
        or "unknown",
        wake_continuity_ok=bool(value.get("wake_continuity_ok", True)),
        wake_gap_summary=str(value.get("wake_gap_summary") or "").strip(),
        loop_wake_mode=loop_autonomy.loop_wake_mode,
        loop_wake_interval_seconds=loop_autonomy.loop_wake_interval_seconds,
        loop_driver_agent=loop_autonomy.loop_driver_agent,
        loop_autonomy_ok=loop_autonomy.loop_autonomy_ok,
        loop_gap_summary=loop_autonomy.loop_gap_summary,
    )


def authority_packet_target_from_mapping(value: object) -> AuthorityPacketTarget | None:
    """Deserialize one authority packet target row."""
    record = agent_attention_record_from_mapping(value)
    if record is None:
        return None
    return AuthorityPacketTarget(
        attention_revision=record.attention_revision,
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
