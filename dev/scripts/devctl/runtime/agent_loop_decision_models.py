"""Typed model for per-agent loop decisions."""

from __future__ import annotations

from dataclasses import dataclass, field

from .agent_loop_operator_override import AgentLoopOperatorOverride
from .typed_gate_failure import TypedGateFailure, typed_gate_failure_dict


@dataclass(frozen=True, slots=True)
class AgentLoopDecision:
    """One machine-readable answer for an agent loop tick."""

    contract_id: str = "AgentLoopDecision"
    schema_version: int = 1
    actor_id: str = ""
    actor_role: str = ""
    session_id: str = ""
    effective_actor_role: str = ""
    effective_workstream_id: str = ""
    effective_authority_source: str = ""
    loop_state: str = "blocked"
    required_action: str = "provide_actor_identity"
    lifecycle_state: str = "blocked"
    decision: str = "run_next_command"
    reason_code: str = "actor_identity_required"
    loop_mode: str = "manual_intervention_required"
    loop_driver_agent: str = ""
    wake_source: str = "agent_runtime_clock"
    loop_intent: str = "auto"
    target_kind: str = ""
    target_ref: str = ""
    recommended_cadence_seconds: int = 0
    can_run_next_command: bool = False
    dogfood_record_allowed: bool = False
    advance_allowed: bool = False
    proof_state: str = "missing"
    required_proofs: tuple[str, ...] = ()
    satisfied_proofs: tuple[str, ...] = ()
    missing_proofs: tuple[str, ...] = ()
    policy_reason: str = ""
    next_loop_command: str = ""
    should_continue_loop: bool = False
    safe_to_continue: bool = False
    may_mutate: bool = False
    reason: str = ""
    next_command: str = ""
    next_action: str = ""
    top_blocker: str = ""
    user_action: str = ""
    continuation_goal: str = ""
    why_not_done: str = ""
    user_continue_state: str = ""
    new_peer_input: bool = False
    switch_to_packet_goal: bool = False
    continue_before_final: bool = False
    active_packet_id: str = ""
    attention_packet_id: str = ""
    executing_packet_id: str = ""
    legacy_unscoped_packet_id: str = ""
    plan_target_ref: str = ""
    current_instruction_revision: str = ""
    wake_required: bool = False
    pivot_required: bool = False
    pending_packet_count: int = 0
    latest_inbox_event_id: str = ""
    last_observed_event_id: str = ""
    body_open_required: bool = False
    body_open_packet_id: str = ""
    semantic_ingestion_required: bool = False
    semantic_ingestion_packet_id: str = ""
    semantic_ingestion_reason: str = ""
    allowed_actions: tuple[str, ...] = ()
    blocked_actions: tuple[str, ...] = ()
    granted_capabilities: tuple[str, ...] = ()
    operator_override: AgentLoopOperatorOverride = field(
        default_factory=AgentLoopOperatorOverride
    )
    gate_failure: TypedGateFailure | None = None
    source_latest_event_id: str = ""
    source_snapshot_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "session_id": self.session_id,
            "effective_actor_role": self.effective_actor_role,
            "effective_workstream_id": self.effective_workstream_id,
            "effective_authority_source": self.effective_authority_source,
            "loop_state": self.loop_state,
            "required_action": self.required_action,
            "lifecycle_state": self.lifecycle_state,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "loop_mode": self.loop_mode,
            "loop_driver_agent": self.loop_driver_agent,
            "wake_source": self.wake_source,
            "loop_intent": self.loop_intent,
            "target_kind": self.target_kind,
            "target_ref": self.target_ref,
            "recommended_cadence_seconds": self.recommended_cadence_seconds,
            "can_run_next_command": self.can_run_next_command,
            "dogfood_record_allowed": self.dogfood_record_allowed,
            "advance_allowed": self.advance_allowed,
            "proof_state": self.proof_state,
            "required_proofs": list(self.required_proofs),
            "satisfied_proofs": list(self.satisfied_proofs),
            "missing_proofs": list(self.missing_proofs),
            "policy_reason": self.policy_reason,
            "next_loop_command": self.next_loop_command,
            "should_continue_loop": self.should_continue_loop,
            "safe_to_continue": self.safe_to_continue,
            "may_mutate": self.may_mutate,
            "reason": self.reason,
            "next_command": self.next_command,
            "next_action": self.next_action,
            "top_blocker": self.top_blocker,
            "user_action": self.user_action,
            "continuation_goal": self.continuation_goal,
            "why_not_done": self.why_not_done,
            "user_continue_state": self.user_continue_state,
            "new_peer_input": self.new_peer_input,
            "switch_to_packet_goal": self.switch_to_packet_goal,
            "continue_before_final": self.continue_before_final,
            "active_packet_id": self.active_packet_id,
            "attention_packet_id": self.attention_packet_id,
            "executing_packet_id": self.executing_packet_id,
            "legacy_unscoped_packet_id": self.legacy_unscoped_packet_id,
            "plan_target_ref": self.plan_target_ref,
            "current_instruction_revision": self.current_instruction_revision,
            "wake_required": self.wake_required,
            "pivot_required": self.pivot_required,
            "pending_packet_count": self.pending_packet_count,
            "latest_inbox_event_id": self.latest_inbox_event_id,
            "last_observed_event_id": self.last_observed_event_id,
            "body_open_required": self.body_open_required,
            "body_open_packet_id": self.body_open_packet_id,
            "semantic_ingestion_required": self.semantic_ingestion_required,
            "semantic_ingestion_packet_id": self.semantic_ingestion_packet_id,
            "semantic_ingestion_reason": self.semantic_ingestion_reason,
            "allowed_actions": list(self.allowed_actions),
            "blocked_actions": list(self.blocked_actions),
            "granted_capabilities": list(self.granted_capabilities),
            "operator_override": self.operator_override.to_dict(),
            "gate_failure": typed_gate_failure_dict(self.gate_failure),
            "source_latest_event_id": self.source_latest_event_id,
            "source_snapshot_id": self.source_snapshot_id,
        }


__all__ = ["AgentLoopDecision"]
