"""Typed final-response gate for the `/develop` controller."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from collections.abc import Mapping
from typing import Any

from .orchestration_models import DevelopmentContinuationRequiredSignal

FINAL_RESPONSE_GATE_CONTRACT_ID = "FinalResponseGateResult"
FINAL_RESPONSE_GATE_SCHEMA_VERSION = 1

_FINAL_BLOCKING_AGENT_ACTIONS = frozenset(
    {
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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def enforce_final_response_gate(
    continuation: DevelopmentContinuationRequiredSignal,
    *,
    packet_attention: Any | None = None,
    orchestration: Any | None = None,
) -> FinalResponseGateResult:
    """Return the typed gate result for final-response emission."""
    live_block = _live_final_response_block(
        continuation,
        packet_attention=packet_attention,
        orchestration=orchestration,
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
        next_required_command=continuation.next_required_command,
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
        next_required_command=(
            _text(_field(packet_attention, "required_command"))
            or continuation.next_required_command
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
) -> FinalResponseGateResult | None:
    if orchestration is None:
        return None
    decisions = getattr(orchestration, "agent_loop_decisions", ()) or ()
    for agent_decision in decisions:
        required_action = _text(_field(agent_decision, "required_action"))
        should_continue = bool(
            _field(agent_decision, "should_continue_loop")
        )
        if (
            required_action not in _FINAL_BLOCKING_AGENT_ACTIONS
            and not should_continue
        ):
            continue
        action = _final_action_for_agent_loop(required_action, continuation)
        required_packet_kind = continuation.required_packet_kind
        if required_action == "post_continuation_anchor" and not required_packet_kind:
            required_packet_kind = "continuation_anchor"
        blocking_packet_id = (
            _text(_field(agent_decision, "active_packet_id"))
            or _text(_field(agent_decision, "attention_packet_id"))
        )
        return FinalResponseGateResult(
            allow_final_response=False,
            action=action,
            reason=f"agent_loop:{required_action or 'continue_required'}",
            next_required_command=(
                _text(_field(agent_decision, "next_loop_command"))
                or continuation.next_required_command
            ),
            required_packet_kind=required_packet_kind,
            required_packet_command=continuation.required_packet_command,
            blocking_packet_id=blocking_packet_id,
            source="agent_loop_decision",
            continuation_state="must_continue",
            user_action=(
                _text(_field(agent_decision, "user_action"))
                or _final_user_action_for_agent_loop(required_action)
            ),
            continuation_goal=(
                _text(_field(agent_decision, "continuation_goal"))
                or blocking_packet_id
                or continuation.continuation_goal
            ),
            why_not_done=(
                _text(_field(agent_decision, "why_not_done"))
                or continuation.why_not_done
                or "The agent loop still has a typed goal before final response."
            ),
            stop_policy=continuation.stop_policy,
        )
    return None


def _final_action_for_agent_loop(
    required_action: str,
    continuation: DevelopmentContinuationRequiredSignal,
) -> str:
    if required_action == "post_continuation_anchor":
        return "post_continuation"
    if required_action in {
        "triage_pending_packet",
        "triage_packet",
        "pivot_to_packet",
        "continue_to_goal",
    }:
        return "continue_to_goal"
    return continuation.required_final_response_action or "run_next_command"


def _final_user_action_for_agent_loop(required_action: str) -> str:
    if required_action == "post_continuation_anchor":
        return "Create continuation anchor"
    if required_action == "continue_from_continuation_anchor":
        return "Continue from continuation anchor"
    if required_action in {
        "triage_pending_packet",
        "triage_packet",
        "pivot_to_packet",
        "continue_to_goal",
    }:
        return "Continue to goal"
    return required_action or "Continue loop"


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
