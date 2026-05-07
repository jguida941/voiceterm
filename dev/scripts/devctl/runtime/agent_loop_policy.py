"""Loop policy projection for per-agent turn decisions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from .agent_loop_operator_override import AgentLoopOperatorOverride
from .agent_loop_policy_checkpoint import (
    governed_checkpoint_policy_kwargs,
    operator_override_edit_policy_kwargs,
)
from .agent_loop_policy_proof import AgentLoopProofGate, proof_gate_for_turn
from .checkpoint_repair_authority import GOVERNED_CHECKPOINT_COMMIT


_MUTATION_ACTIONS = frozenset(
    {
        "cut_checkpoint",
        GOVERNED_CHECKPOINT_COMMIT,
        "repair_startup_authority",
    }
)
_EDIT_ONLY_BLOCKED_COMMANDS = frozenset(
    {
        GOVERNED_CHECKPOINT_COMMIT,
        "repair_startup_authority",
    }
)
_OBSERVER_ROLES = frozenset({"dashboard", "observer", "operator"})


class _LoopContext(Protocol):
    review_state: Mapping[str, object]
    actor: str
    role: str
    session: str
    master_plan: Mapping[str, object]
    may_mutate: bool
    clock: Mapping[str, object]
    current_instruction_revision: str
    loop_intent: str
    requested_plan_ref: str
    requested_packet_id: str
    operator_override: AgentLoopOperatorOverride


@dataclass(frozen=True, slots=True)
class AgentLoopPolicy:
    """Machine-readable loop timing and command policy for one actor tick."""

    loop_mode: str = "manual_intervention_required"
    loop_driver_agent: str = ""
    wake_source: str = "agent_runtime_clock"
    loop_intent: str = "auto"
    recommended_cadence_seconds: int = 0
    can_run_next_command: bool = False
    dogfood_record_allowed: bool = False
    proof_gate: AgentLoopProofGate = field(default_factory=AgentLoopProofGate)
    policy_reason: str = ""
    next_loop_command: str = ""

    @property
    def target_kind(self) -> str:
        return self.proof_gate.target_kind

    @property
    def target_ref(self) -> str:
        return self.proof_gate.target_ref

    @property
    def advance_allowed(self) -> bool:
        return self.proof_gate.advance_allowed

    @property
    def proof_state(self) -> str:
        return self.proof_gate.proof_state

    @property
    def required_proofs(self) -> tuple[str, ...]:
        return self.proof_gate.required_proofs

    @property
    def satisfied_proofs(self) -> tuple[str, ...]:
        return self.proof_gate.satisfied_proofs

    @property
    def missing_proofs(self) -> tuple[str, ...]:
        return self.proof_gate.missing_proofs


def policy_for_turn(
    *,
    ctx: _LoopContext,
    loop_state: str,
    required_action: str,
    decision_code: str,
    safe_to_continue: bool,
    should_continue_loop: bool,
    active_packet_id: str,
    plan_target_ref: str,
) -> AgentLoopPolicy:
    """Return how the actor loop should schedule and execute this turn."""
    command = scoped_loop_command(ctx)
    driver = str(ctx.actor or "").strip()
    cadence = cadence_for_role(ctx.role, ctx.clock)
    proof = proof_gate_for_turn(
        ctx=ctx,
        loop_state=loop_state,
        required_action=required_action,
        active_packet_id=active_packet_id,
        plan_target_ref=plan_target_ref,
    )

    if decision_code == "stop_no_work" or required_action == "stop_no_work":
        policy = _stopped_policy(ctx, driver, cadence, proof, command)
    elif not should_continue_loop:
        policy = AgentLoopPolicy(
            loop_mode="blocked_wait",
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=cadence,
            proof_gate=proof,
            policy_reason="missing_required_loop_identity",
            next_loop_command=command,
        )
    elif (
        ctx.operator_override.edit_allowed
        and required_action in _EDIT_ONLY_BLOCKED_COMMANDS
    ):
        policy = AgentLoopPolicy(
            **operator_override_edit_policy_kwargs(
                ctx, driver, cadence, proof, command, required_action
            )
        )
    elif required_action in _MUTATION_ACTIONS and not ctx.may_mutate:
        policy = AgentLoopPolicy(
            loop_mode="observer_wait",
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=observer_cadence(ctx.role, cadence),
            can_run_next_command=False,
            dogfood_record_allowed=False,
            proof_gate=proof,
            policy_reason=f"{required_action}_requires_mutation_authority",
            next_loop_command=command,
        )
    elif required_action == "repair_startup_authority" and ctx.may_mutate:
        policy = AgentLoopPolicy(
            loop_mode="startup_repair",
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=max(15, min(cadence, 60)),
            can_run_next_command=True,
            dogfood_record_allowed=True,
            proof_gate=proof,
            policy_reason="startup_repair_authorized_by_actor_capabilities",
            next_loop_command=command,
        )
    elif required_action == GOVERNED_CHECKPOINT_COMMIT and ctx.may_mutate:
        policy = AgentLoopPolicy(
            **governed_checkpoint_policy_kwargs(ctx, driver, cadence, proof, command)
        )
    elif required_action == "triage_pending_packet":
        policy = AgentLoopPolicy(
            loop_mode="pivot_to_packet",
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=max(5, min(cadence, 30)),
            can_run_next_command=False,
            dogfood_record_allowed=True,
            proof_gate=proof,
            policy_reason="packet_attention_triage_preempts_blocked_mutation",
            next_loop_command=command,
        )
    elif decision_code in {"pivot_to_packet", "continue_current_execution"}:
        policy = AgentLoopPolicy(
            loop_mode=decision_code,
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=max(5, min(cadence, 30)),
            can_run_next_command=True,
            dogfood_record_allowed=True,
            proof_gate=proof,
            policy_reason="scoped_packet_requires_actor_work",
            next_loop_command=command,
        )
    elif required_action == "resume_or_recover_session":
        policy = AgentLoopPolicy(
            loop_mode="recover_or_relaunch",
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=max(30, min(cadence, 120)),
            can_run_next_command=ctx.may_mutate,
            dogfood_record_allowed=True,
            proof_gate=proof,
            policy_reason="session_outcome_requires_recovery_decision",
            next_loop_command=command,
        )
    elif loop_state == "blocked":
        policy = AgentLoopPolicy(
            loop_mode="run_or_report_blocker",
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=max(30, min(cadence, 120)),
            can_run_next_command=safe_to_continue and ctx.may_mutate,
            dogfood_record_allowed=ctx.may_mutate,
            proof_gate=proof,
            policy_reason="blocker_requires_authorized_owner",
            next_loop_command=command,
        )
    elif loop_state in {"observe", "wait"}:
        policy = AgentLoopPolicy(
            loop_mode="typed_event_wait",
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=observer_cadence(ctx.role, cadence),
            can_run_next_command=False,
            dogfood_record_allowed=False,
            proof_gate=proof,
            policy_reason="no_claimable_scoped_work_for_actor",
            next_loop_command=command,
        )
    else:
        policy = AgentLoopPolicy(
            loop_mode="typed_event_wait",
            loop_driver_agent=driver,
            loop_intent=ctx.loop_intent,
            recommended_cadence_seconds=cadence,
            can_run_next_command=False,
            proof_gate=proof,
            policy_reason="default_typed_loop_policy",
            next_loop_command=command,
        )
    return policy


def _stopped_policy(
    ctx: _LoopContext,
    driver: str,
    cadence: int,
    proof: AgentLoopProofGate,
    command: str,
) -> AgentLoopPolicy:
    loop_mode = "stopped" if proof.advance_allowed else "await_round_proof"
    stop_cadence = 0 if proof.advance_allowed else max(30, min(cadence, 120))
    return AgentLoopPolicy(
        loop_mode=loop_mode,
        loop_driver_agent=driver,
        loop_intent=ctx.loop_intent,
        recommended_cadence_seconds=stop_cadence,
        can_run_next_command=False,
        dogfood_record_allowed=False,
        proof_gate=proof,
        policy_reason=proof.reason or "completed_handoff_has_no_new_scoped_work",
        next_loop_command=command,
    )


def cadence_for_role(role: str, clock: object) -> int:
    base = _clock_cadence(clock) or 30
    normalized = str(role or "").strip().lower()
    if normalized in {"implementer", "coder"}:
        return max(15, min(base, 60))
    if normalized == "reviewer":
        return max(30, min(base, 120))
    if normalized in _OBSERVER_ROLES:
        return max(300, min(base * 20, 900))
    return max(60, min(base * 4, 300))


def observer_cadence(role: str, cadence: int) -> int:
    if str(role or "").strip().lower() in _OBSERVER_ROLES:
        return max(300, cadence)
    return cadence


def scoped_loop_command(ctx: _LoopContext) -> str:
    parts = [
        "python3",
        "dev/scripts/devctl.py",
        "agent-loop",
        "--format",
        "json",
        "--actor",
        _shell_word(ctx.actor or "claude"),
        "--role",
        _shell_word(ctx.role or "dashboard"),
    ]
    if ctx.session:
        parts.extend(("--session-id", _shell_word(ctx.session)))
    if ctx.loop_intent and ctx.loop_intent != "auto":
        parts.extend(("--mode", _shell_word(ctx.loop_intent)))
    if ctx.requested_plan_ref:
        parts.extend(("--plan", _shell_word(ctx.requested_plan_ref)))
    if ctx.requested_packet_id:
        parts.extend(("--packet", _shell_word(ctx.requested_packet_id)))
    if ctx.operator_override.requested:
        parts.append("--operator-override")
        if ctx.operator_override.scope:
            parts.extend(("--override-scope", _shell_word(ctx.operator_override.scope)))
        if ctx.operator_override.reason:
            parts.extend(("--override-reason", _shell_word(ctx.operator_override.reason)))
        if ctx.operator_override.requested_by:
            parts.extend(("--override-by", _shell_word(ctx.operator_override.requested_by)))
    return " ".join(parts)


def _clock_cadence(clock: object) -> int:
    if not isinstance(clock, Mapping):
        return 0
    try:
        return int(clock.get("cadence_seconds") or 0)
    except (TypeError, ValueError):
        return 0


def _shell_word(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "''"
    if all(ch.isalnum() or ch in "._:-/" for ch in text):
        return text
    return "'" + text.replace("'", "'\"'\"'") + "'"


__all__ = ["AgentLoopPolicy", "AgentLoopProofGate", "policy_for_turn"]
