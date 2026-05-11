"""Orchestration and continuation contracts for `/develop` reports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DevelopmentOrchestrationSignal:
    """One action-worthy signal consumed from an existing typed surface."""

    source: str
    signal_id: str
    status: str
    summary: str
    source_surface: str = ""
    severity: str = ""
    recommended_action: str = ""
    closure_check_command: str = ""
    source_command: str = ""
    suggested_command: str = ""
    source_path: str = ""


@dataclass(frozen=True, slots=True)
class DevelopmentAgentLoopInput:
    """Compact AgentLoopDecision row consumed by `/develop`."""

    actor_id: str
    actor_role: str
    session_id: str
    lifecycle_state: str
    required_action: str
    loop_mode: str
    should_continue_loop: bool
    safe_to_continue: bool
    may_mutate: bool
    proof_state: str
    pending_packet_count: int = 0
    top_blocker: str = ""
    next_loop_command: str = ""
    missing_proofs: tuple[str, ...] = ()
    active_packet_id: str = ""
    attention_packet_id: str = ""
    user_action: str = ""
    continuation_goal: str = ""
    why_not_done: str = ""
    user_continue_state: str = ""
    new_peer_input: bool = False
    switch_to_packet_goal: bool = False
    continue_before_final: bool = False


@dataclass(frozen=True, slots=True)
class DevelopmentOrchestrationSnapshot:
    """Existing orchestration signals visible to the develop controller."""

    authority_policy: str = "consume_existing_agent_loop_and_system_picture"
    source_surfaces: tuple[str, ...] = ("agent-loop", "system-picture")
    status: str = "current"
    signal_count: int = 0
    stale_projection_count: int = 0
    missing_projection_count: int = 0
    action_required_count: int = 0
    agent_loop_decisions: tuple[DevelopmentAgentLoopInput, ...] = ()
    signals: tuple[DevelopmentOrchestrationSignal, ...] = ()
    summary: str = "No orchestration signals require attention."


@dataclass(frozen=True, slots=True)
class DevelopmentWatcherLease:
    """Typed watcher ownership/status for the active `/develop` lane."""

    lease_id: str = ""
    watcher_id: str = ""
    watched_actor: str = ""
    watched_surfaces: tuple[str, ...] = ()
    status: str = "missing"
    last_seen_event_id: str = ""
    stale_after_seconds: int = 300
    stale_seconds: int = 0
    next_report_command: str = ""
    source_path: str = ""
    summary: str = ""


@dataclass(frozen=True, slots=True)
class DevelopmentContinuationRequiredSignal:
    """Stop/continue decision derived from typed controller state."""

    continuation_required: bool = True
    status: str = "controller_state_missing"
    final_response_allowed: bool = False
    final_response_gate_allowed: bool = False
    user_continue_state: str = "must_continue"
    user_action: str = "Compute typed continuation state"
    continuation_goal: str = "typed controller goal"
    why_not_done: str = "Typed controller closure has not been computed."
    required_final_response_action: str = "run_next_command"
    required_packet_kind: str = ""
    required_packet_command: str = ""
    reasons: tuple[str, ...] = ("continuation_signal_missing",)
    next_required_command: str = ""
    stop_policy: str = "stop_only_when_typed_controller_closed"
    summary: str = "Typed controller closure has not been computed."


__all__ = [
    "DevelopmentAgentLoopInput",
    "DevelopmentContinuationRequiredSignal",
    "DevelopmentOrchestrationSignal",
    "DevelopmentOrchestrationSnapshot",
    "DevelopmentWatcherLease",
]
