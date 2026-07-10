"""Final authority snapshot assembly."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .authority_snapshot_core import AuthoritySnapshot
from .authority_snapshot_provenance import authority_snapshot_provenance_kwargs


@dataclass(frozen=True, slots=True)
class AuthoritySnapshotResultInputs:
    payload: Mapping[str, object]
    command: str
    actor_role: str
    actor_identity: str
    safe_to_continue: bool
    coordination_state: str
    root_cause: str
    required_action: str
    reviewer_mode: str
    mode_projection: object
    reviewer_freshness: str
    attention_status: str
    implementation_permission: str
    current_instruction_revision: str
    implementer_ack_state: str
    resync_required: bool
    coordination_current_slice: str
    current_instruction: str
    active_target: Mapping[str, object]
    allowed_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    packet_target: object
    collaboration: Mapping[str, object]
    actor_capabilities: tuple[str, ...]
    actor_authorities: tuple[object, ...]


def authority_snapshot_from_result(
    inputs: AuthoritySnapshotResultInputs,
) -> AuthoritySnapshot:
    mode_projection = inputs.mode_projection
    return AuthoritySnapshot(
        **authority_snapshot_provenance_kwargs(inputs.payload),
        coordination_state=inputs.coordination_state,
        root_cause=inputs.root_cause,
        required_action=inputs.required_action,
        next_command=inputs.command,
        actor_role=inputs.actor_role,
        actor_identity=inputs.actor_identity,
        safe_to_continue=inputs.safe_to_continue,
        reviewer_mode=inputs.reviewer_mode,
        effective_reviewer_mode=mode_projection.effective_reviewer_mode,
        reviewer_freshness=inputs.reviewer_freshness,
        attention_status=inputs.attention_status,
        interaction_mode=mode_projection.interaction_mode,
        gate_mode=mode_projection.gate_mode,
        declared_active=mode_projection.declared_active,
        effective_active=mode_projection.effective_active,
        observed_control_topology=_observed_topology(inputs),
        implementation_permission=inputs.implementation_permission,
        current_instruction_revision=inputs.current_instruction_revision,
        implementer_ack_state=inputs.implementer_ack_state,
        resync_required=inputs.resync_required,
        current_slice=str(
            inputs.coordination_current_slice or inputs.current_instruction or ""
        ).strip(),
        active_target_path=str(inputs.active_target.get("plan_path") or "").strip(),
        allowed_actions=inputs.allowed_actions,
        blocked_actions=inputs.blocked_actions,
        packet_target=inputs.packet_target,
        mutation_owner=str(inputs.collaboration.get("mutation_owner") or "").strip(),
        verification_owner=str(
            inputs.collaboration.get("verification_owner") or ""
        ).strip(),
        verification_status=str(
            inputs.collaboration.get("verification_status") or "inactive"
        ).strip(),
        watcher_owner=str(inputs.collaboration.get("watcher_owner") or "").strip(),
        watcher_status=str(
            inputs.collaboration.get("watcher_status") or "inactive"
        ).strip(),
        actor_capabilities=inputs.actor_capabilities,
        actor_authorities=inputs.actor_authorities,
    )


def _observed_topology(inputs: AuthoritySnapshotResultInputs) -> str:
    return str(
        inputs.payload.get("observed_control_topology")
        or inputs.collaboration.get("observed_topology")
        or ""
    ).strip()


__all__ = ["AuthoritySnapshotResultInputs", "authority_snapshot_from_result"]
