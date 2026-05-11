"""Projection helpers for compact authority snapshot assembly."""

from __future__ import annotations

from typing import NamedTuple

from .authority_snapshot_core import AuthoritySnapshot
from .collaboration_wake_contract import LoopAutonomyState
from .review_state_collaboration_models import (
    actor_authorities_from_value,
    granted_capabilities_for_actor,
)
from .reviewer_mode import ReviewerMode, reviewer_mode_is_active


class CollaborationWakeFields(NamedTuple):
    mutation_wake_mode: str
    verification_wake_mode: str
    watcher_wake_mode: str
    wake_continuity_present: bool
    wake_continuity_ok: bool
    wake_gap_summary: str
    loop_wake_mode: str
    loop_wake_interval_seconds: int
    loop_driver_agent: str
    loop_autonomy_present: bool
    loop_autonomy_ok: bool
    loop_gap_summary: str


def resolve_collaboration_wake_fields(
    collaboration: dict[str, object],
) -> CollaborationWakeFields:
    loop_autonomy = LoopAutonomyState.from_mapping(collaboration) or LoopAutonomyState()
    return CollaborationWakeFields(
        mutation_wake_mode=str(
            collaboration.get("mutation_wake_mode") or "unknown"
        ).strip()
        or "unknown",
        verification_wake_mode=str(
            collaboration.get("verification_wake_mode") or "unknown"
        ).strip()
        or "unknown",
        watcher_wake_mode=str(
            collaboration.get("watcher_wake_mode") or "unknown"
        ).strip()
        or "unknown",
        wake_continuity_present="wake_continuity_ok" in collaboration,
        wake_continuity_ok=bool(collaboration.get("wake_continuity_ok", True)),
        wake_gap_summary=str(collaboration.get("wake_gap_summary") or "").strip(),
        loop_wake_mode=loop_autonomy.loop_wake_mode,
        loop_wake_interval_seconds=loop_autonomy.loop_wake_interval_seconds,
        loop_driver_agent=loop_autonomy.loop_driver_agent,
        loop_autonomy_present="loop_autonomy_ok" in collaboration,
        loop_autonomy_ok=loop_autonomy.loop_autonomy_ok,
        loop_gap_summary=loop_autonomy.loop_gap_summary,
    )


def apply_wake_continuity_gate(
    *,
    reviewer_mode: str,
    coordination_state: str,
    root_cause: str,
    required_action: str,
    wake_fields: CollaborationWakeFields,
) -> tuple[str, str, str]:
    if not reviewer_mode_is_active(reviewer_mode, default=ReviewerMode.SINGLE_AGENT):
        return coordination_state, root_cause, required_action
    if wake_fields.wake_continuity_present and wake_fields.wake_continuity_ok:
        return coordination_state, root_cause, required_action
    updated_state = (
        "resync_required" if coordination_state == "ready" else coordination_state
    )
    updated_root = root_cause or (
        wake_fields.wake_gap_summary
        or "Active dual-agent mode is missing typed wake continuity truth."
    )
    updated_action = required_action or "repair_wake_continuity"
    return updated_state, updated_root, updated_action


def build_snapshot_result(
    *,
    coordination_state: str,
    root_cause: str,
    required_action: str,
    next_command: str,
    actor_role: str,
    actor_identity: str,
    safe_to_continue: bool,
    reviewer_mode: str,
    reviewer_freshness: str,
    attention_status: str,
    observed_control_topology: str,
    implementation_permission: str,
    current_instruction_revision: str,
    implementer_ack_state: str,
    resync_required: bool,
    current_slice: str,
    active_target_path: str,
    allowed_actions: tuple[str, ...],
    blocked_actions: tuple[str, ...],
    packet_target: object,
    collaboration: dict[str, object],
    wake_fields: CollaborationWakeFields,
) -> AuthoritySnapshot:
    actor_authorities = actor_authorities_from_value(
        collaboration.get("actor_authorities")
    )
    actor_capabilities = granted_capabilities_for_actor(
        actor_authorities,
        actor_identity or str(collaboration.get("mutation_owner") or "").strip(),
    )
    return AuthoritySnapshot(
        coordination_state=coordination_state,
        root_cause=root_cause,
        required_action=required_action,
        next_command=next_command,
        actor_role=actor_role,
        actor_identity=actor_identity,
        safe_to_continue=safe_to_continue,
        reviewer_mode=reviewer_mode,
        reviewer_freshness=reviewer_freshness,
        attention_status=attention_status,
        observed_control_topology=observed_control_topology,
        implementation_permission=implementation_permission,
        current_instruction_revision=current_instruction_revision,
        implementer_ack_state=implementer_ack_state,
        resync_required=resync_required,
        current_slice=current_slice,
        active_target_path=active_target_path,
        allowed_actions=allowed_actions,
        blocked_actions=blocked_actions,
        packet_target=packet_target,
        mutation_owner=str(collaboration.get("mutation_owner") or "").strip(),
        verification_owner=str(collaboration.get("verification_owner") or "").strip(),
        verification_status=str(
            collaboration.get("verification_status") or "inactive"
        ).strip(),
        watcher_owner=str(collaboration.get("watcher_owner") or "").strip(),
        watcher_status=str(collaboration.get("watcher_status") or "inactive").strip(),
        actor_capabilities=actor_capabilities,
        actor_authorities=actor_authorities,
        mutation_wake_mode=wake_fields.mutation_wake_mode,
        verification_wake_mode=wake_fields.verification_wake_mode,
        watcher_wake_mode=wake_fields.watcher_wake_mode,
        wake_continuity_ok=(
            wake_fields.wake_continuity_ok
            if wake_fields.wake_continuity_present
            else not reviewer_mode_is_active(
                reviewer_mode,
                default=ReviewerMode.SINGLE_AGENT,
            )
        ),
        wake_gap_summary=wake_fields.wake_gap_summary,
        loop_wake_mode=wake_fields.loop_wake_mode,
        loop_wake_interval_seconds=wake_fields.loop_wake_interval_seconds,
        loop_driver_agent=wake_fields.loop_driver_agent,
        loop_autonomy_ok=wake_fields.loop_autonomy_ok,
        loop_gap_summary=wake_fields.loop_gap_summary,
    )
