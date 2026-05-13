"""Typed final-response gate for the `/develop` controller."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from .final_response_gate_agent_loop import (
    agent_loop_blocking_packet_id,
    agent_loop_next_required_command,
    edit_only_override_why_not_done,
    fallback_next_required_command,
    final_action_for_agent_loop,
    final_user_action_for_agent_loop,
    is_active_edit_only_override,
    prioritized_agent_loop_decisions,
)
from .orchestration_models import DevelopmentContinuationRequiredSignal
from ...runtime.typed_gate_failure import TypedGateFailure

FINAL_RESPONSE_GATE_CONTRACT_ID = "FinalResponseGateResult"
FINAL_RESPONSE_GATE_SCHEMA_VERSION = 1

_FINAL_BLOCKING_AGENT_ACTIONS = frozenset(
    {
        "open_packet_body",
        "post_continuation_anchor",
        "continue_from_continuation_anchor",
        "triage_pending_packet",
        "triage_packet",
        "run_next_command",
        "pivot_to_packet",
        "continue_to_goal",
    }
)


@dataclass(frozen=True, slots=True)
class FinalResponseGateResult:
    """Decision for whether an agent may emit a final response."""

    schema_version: int = FINAL_RESPONSE_GATE_SCHEMA_VERSION
    contract_id: str = FINAL_RESPONSE_GATE_CONTRACT_ID
    allow_final_response: bool = True
    action: str = "allow_final_response"
    reason: str = "typed_controller_closed"
    next_required_command: str = ""
    required_packet_kind: str = ""
    required_packet_command: str = ""
    blocking_packet_id: str = ""
    source: str = "continuation_signal"
    continuation_state: str = "may_stop"
    user_action: str = "Final response allowed"
    continuation_goal: str = ""
    why_not_done: str = ""
    stop_policy: str = "stop_only_when_typed_controller_closed"
    gate_failure: TypedGateFailure | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def enforce_final_response_gate(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    packet_attention: Any | None = None,
    orchestration: Any | None = None,
    next_slice_id: str = "",
) -> FinalResponseGateResult:
    """Return the typed gate result for final-response emission."""
    live_block = _live_final_response_block(
        continuation,
        packet_attention=packet_attention,
        orchestration=orchestration,
        next_slice_id=next_slice_id,
    )
    if live_block is not None:
        return live_block
    if continuation.final_response_allowed:
        return FinalResponseGateResult()
    return FinalResponseGateResult(
        allow_final_response=False,
        action=(
            continuation.required_final_response_action
            or "run_next_command"
        ),
        reason=continuation.reasons[0] if continuation.reasons else "continuation_required",
        next_required_command=fallback_next_required_command(
            continuation.next_required_command
        ),
        required_packet_kind=continuation.required_packet_kind,
        required_packet_command=continuation.required_packet_command,
        continuation_state=continuation.user_continue_state,
        user_action=continuation.user_action,
        continuation_goal=continuation.continuation_goal,
        why_not_done=continuation.why_not_done,
        stop_policy=continuation.stop_policy,
    )


def _live_final_response_block(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    packet_attention: Any | None,
    orchestration: Any | None,
    next_slice_id: str = "",
) -> FinalResponseGateResult | None:
    packet_block = _packet_attention_final_response_block(
        continuation,
        packet_attention=packet_attention,
    )
    if packet_block is not None:
        return packet_block
    return _agent_loop_final_response_block(
        continuation,
        orchestration=orchestration,
        next_slice_id=next_slice_id,
    )


def _packet_attention_final_response_block(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    packet_attention: Any | None,
) -> FinalResponseGateResult | None:
    if packet_attention is None:
        return None
    attention_required = bool(_field(packet_attention, "attention_required"))
    pending_packet_count = _int(_field(packet_attention, "pending_packet_count"))
    wake_required = _truthy(_field(packet_attention, "wake_required"))
    pivot_required = _truthy(_field(packet_attention, "pivot_required"))
    if not (
        attention_required
        or pending_packet_count > 0
        or wake_required
        or pivot_required
    ):
        return None
    wake_reason = _text(_field(packet_attention, "wake_reason"))
    attention_reason = _text(_field(packet_attention, "attention_reason"))
    reason = wake_reason or attention_reason or "packet_attention_required"
    return FinalResponseGateResult(
        allow_final_response=False,
        action="continue_to_goal",
        reason=f"packet_attention:{reason}",
        next_required_command=fallback_next_required_command(
            _text(_field(packet_attention, "required_command"))
            or continuation.next_required_command,
            actor=_text(_field(packet_attention, "agent")),
        ),
        required_packet_kind=continuation.required_packet_kind,
        required_packet_command=continuation.required_packet_command,
        blocking_packet_id=_text(
            _field(packet_attention, "latest_attention_packet_id")
        ),
        source="packet_attention",
        continuation_state="must_continue",
        user_action="Continue to goal",
        continuation_goal=_text(
            _field(packet_attention, "latest_attention_packet_id")
        ),
        why_not_done=(
            "A scoped packet requires attention before a final response is allowed."
        ),
        stop_policy=continuation.stop_policy,
    )


def _agent_loop_final_response_block(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    orchestration: Any | None,
    next_slice_id: str = "",
) -> FinalResponseGateResult | None:
    if orchestration is None:
        return None
    decisions = tuple(getattr(orchestration, "agent_loop_decisions", ()) or ())
    for agent_decision in prioritized_agent_loop_decisions(decisions):
        required_action = _text(_field(agent_decision, "required_action"))
        should_continue = bool(
            _field(agent_decision, "should_continue_loop")
        )
        if (
            required_action not in _FINAL_BLOCKING_AGENT_ACTIONS
            and not should_continue
        ):
            continue
        active_edit_override = is_active_edit_only_override(agent_decision)
        action = (
            "continue_to_goal"
            if active_edit_override
            else final_action_for_agent_loop(required_action, continuation)
        )
        required_packet_kind = continuation.required_packet_kind
        if required_action == "post_continuation_anchor" and not required_packet_kind:
            required_packet_kind = "continuation_anchor"
        next_required_command = agent_loop_next_required_command(
            agent_decision,
            continuation=continuation,
            required_action=required_action,
            next_slice_id=next_slice_id,
        )
        blocking_packet_id = agent_loop_blocking_packet_id(
            agent_decision,
            required_action=required_action,
            next_required_command=next_required_command,
        )
        reason = f"agent_loop:{required_action or 'continue_required'}"
        return FinalResponseGateResult(
            allow_final_response=False,
            action=action,
            reason=reason,
            next_required_command=next_required_command,
            required_packet_kind=required_packet_kind,
            required_packet_command=continuation.required_packet_command,
            blocking_packet_id=blocking_packet_id,
            source="agent_loop_decision",
            continuation_state="must_continue",
            user_action=(
                "Continue scoped implementation edits"
                if active_edit_override
                else ""
            ) or (
                _text(_field(agent_decision, "user_action"))
                or final_user_action_for_agent_loop(required_action)
            ),
            continuation_goal=(
                _text(_field(agent_decision, "continuation_goal"))
                or blocking_packet_id
                or continuation.continuation_goal
            ),
            why_not_done=(
                edit_only_override_why_not_done(agent_decision)
                if active_edit_override
                else ""
            ) or (
                _text(_field(agent_decision, "why_not_done"))
                or continuation.why_not_done
                or "The agent loop still has a typed goal before final response."
            ),
            stop_policy=continuation.stop_policy,
            gate_failure=_gate_failure_for_agent_loop(
                agent_decision,
                required_action=required_action,
                reason=reason,
                next_required_command=next_required_command,
            ),
        )
    return None


def _gate_failure_for_agent_loop(
    agent_decision: Any,
    *,
    required_action: str,
    reason: str,
    next_required_command: str,
) -> TypedGateFailure:
    existing = _field(agent_decision, "gate_failure")
    if isinstance(existing, Mapping):
        gate_id = _text(existing.get("gate_id")) or f"agent_loop.{required_action}"
        violation_reason = _text(existing.get("violation_reason")) or reason
        contract_path = _text(existing.get("contract_definition_path"))
        receipt_kind = _text(existing.get("bypass_receipt_kind")) or "BypassReceipt"
        lifecycle_class = (
            _text(existing.get("exception_lifecycle_class"))
            or "GovernedExceptionLifecycle"
        )
    else:
        gate_id = f"agent_loop.{required_action or 'continue_required'}"
        violation_reason = reason
        contract_path = "dev/scripts/devctl/commands/development/final_response_gate.py:95"
        receipt_kind = "BypassReceipt"
        lifecycle_class = "GovernedExceptionLifecycle"
    return TypedGateFailure(
        gate_id=gate_id,
        violation_reason=violation_reason,
        bypass_invocation=(
            next_required_command
            if "--operator-override" in next_required_command
            else ""
        ),
        bypass_receipt_kind=receipt_kind,
        contract_definition_path=contract_path,
        exception_lifecycle_class=lifecycle_class,
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _field(value: Any, key: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(key)
    return getattr(value, key, None)


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"1", "true", "yes", "on"}


__all__ = [
    "FINAL_RESPONSE_GATE_CONTRACT_ID",
    "FINAL_RESPONSE_GATE_SCHEMA_VERSION",
    "FinalResponseGateResult",
    "enforce_final_response_gate",
]
