"""Typed final-response gate for the `/develop` controller."""

from __future__ import annotations

import shlex
from dataclasses import asdict, dataclass
from collections.abc import Mapping
from pathlib import PurePath
from typing import Any

from .orchestration_models import DevelopmentContinuationRequiredSignal
from ...runtime.agent_loop_operator_override import (
    DEFAULT_OPERATOR_OVERRIDE_REASON,
    EDIT_ONLY_OVERRIDE_SCOPE,
    OPERATOR_OVERRIDE_REQUESTOR,
)

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
        next_required_command=_fallback_next_required_command(
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
        next_required_command=_fallback_next_required_command(
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
    for agent_decision in _prioritized_agent_loop_decisions(decisions):
        required_action = _text(_field(agent_decision, "required_action"))
        should_continue = bool(
            _field(agent_decision, "should_continue_loop")
        )
        if (
            required_action not in _FINAL_BLOCKING_AGENT_ACTIONS
            and not should_continue
        ):
            continue
        active_edit_override = _is_active_edit_only_override(agent_decision)
        action = (
            "continue_to_goal"
            if active_edit_override
            else _final_action_for_agent_loop(required_action, continuation)
        )
        required_packet_kind = continuation.required_packet_kind
        if required_action == "post_continuation_anchor" and not required_packet_kind:
            required_packet_kind = "continuation_anchor"
        next_required_command = _agent_loop_next_required_command(
            agent_decision,
            continuation=continuation,
            required_action=required_action,
            next_slice_id=next_slice_id,
        )
        blocking_packet_id = _agent_loop_blocking_packet_id(
            agent_decision,
            required_action=required_action,
            next_required_command=next_required_command,
        )
        return FinalResponseGateResult(
            allow_final_response=False,
            action=action,
            reason=f"agent_loop:{required_action or 'continue_required'}",
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
                or _final_user_action_for_agent_loop(required_action)
            ),
            continuation_goal=(
                _text(_field(agent_decision, "continuation_goal"))
                or blocking_packet_id
                or continuation.continuation_goal
            ),
            why_not_done=(
                _edit_only_override_why_not_done(agent_decision)
                if active_edit_override
                else ""
            ) or (
                _text(_field(agent_decision, "why_not_done"))
                or continuation.why_not_done
                or "The agent loop still has a typed goal before final response."
            ),
            stop_policy=continuation.stop_policy,
        )
    return None


def _agent_loop_blocking_packet_id(
    agent_decision: Any,
    *,
    required_action: str,
    next_required_command: str,
) -> str:
    command_packet_id = _packet_id_from_command(next_required_command)
    if required_action == "open_packet_body" and command_packet_id:
        return command_packet_id
    return (
        _text(_field(agent_decision, "active_packet_id"))
        or _text(_field(agent_decision, "attention_packet_id"))
        or command_packet_id
    )


def _prioritized_agent_loop_decisions(decisions: tuple[Any, ...]) -> tuple[Any, ...]:
    """Prefer actionable peer packet and mutation-owner repair over local stubs."""
    return tuple(
        sorted(
            decisions,
            key=lambda decision: _agent_loop_decision_priority(decision),
        )
    )


def _agent_loop_decision_priority(agent_decision: Any) -> tuple[int, int]:
    required_action = _text(_field(agent_decision, "required_action"))
    next_command = _text(_field(agent_decision, "next_command"))
    has_packet = bool(
        _text(_field(agent_decision, "active_packet_id"))
        or _text(_field(agent_decision, "attention_packet_id"))
    )
    may_mutate = bool(_field(agent_decision, "may_mutate"))
    if required_action == "open_packet_body":
        return (0, 0)
    if has_packet:
        return (1, 0)
    if (
        may_mutate
        and required_action in {"repair_startup_authority", "cut_checkpoint"}
        and (
            _is_status_probe_command(next_command)
            or not _is_executable_next_command(next_command)
        )
    ):
        return (4, 0)
    if may_mutate and required_action in {
        "repair_startup_authority",
        "cut_checkpoint",
    }:
        return (2, 0)
    if required_action in {"repair_startup_authority", "cut_checkpoint"}:
        return (3, 0)
    if may_mutate:
        return (4, 0)
    return (5, 0)


def _is_status_probe_command(command: str) -> bool:
    return "review-channel --action status" in command


def _is_executable_next_command(command: str) -> bool:
    command_text = _text(command)
    if not command_text:
        return False
    try:
        parts = shlex.split(command_text)
    except ValueError:
        return False
    if not parts:
        return False
    executable = PurePath(parts[0]).name
    if executable in {"devctl", "devctl.py"}:
        return True
    if executable == "python" or executable.startswith("python"):
        return _python_invokes_devctl(parts[1:])
    return executable == "uv" and _uv_invokes_devctl(parts[1:])


def _python_invokes_devctl(args: list[str]) -> bool:
    index = 0
    while index < len(args):
        token = args[index]
        if token == "-m":
            module_index = index + 1
            return module_index < len(args) and args[module_index].endswith("devctl")
        if token.startswith("-"):
            index += 1
            continue
        return PurePath(token).name == "devctl.py"
    return False


def _uv_invokes_devctl(args: list[str]) -> bool:
    if len(args) >= 3 and args[0] == "run":
        executable = PurePath(args[1]).name
        if executable == "python" or executable.startswith("python"):
            return _python_invokes_devctl(args[2:])
        return executable in {"devctl", "devctl.py"}
    return False


def _agent_loop_next_required_command(
    agent_decision: Any,
    *,
    continuation: DevelopmentContinuationRequiredSignal,
    required_action: str,
    next_slice_id: str,
) -> str:
    next_command = _text(_field(agent_decision, "next_command"))
    next_loop_command = _text(_field(agent_decision, "next_loop_command"))
    if _is_active_edit_only_override(agent_decision):
        return ""
    if (
        _should_surface_plan_override(agent_decision, required_action=required_action)
        and next_slice_id
        and (not next_command or next_command == next_loop_command)
    ):
        return _plan_override_command(
            agent_decision,
            next_slice_id=next_slice_id,
        )
    return _fallback_next_required_command(
        next_command or next_loop_command or continuation.next_required_command,
        actor=_text(_field(agent_decision, "actor_id")),
    )


def _fallback_next_required_command(command: str, *, actor: str = "") -> str:
    command_text = _text(command)
    if command_text:
        return command_text
    actor_arg = f" --actor {shlex.quote(actor)}" if actor else ""
    return f"python3 dev/scripts/devctl.py develop next{actor_arg} --format md"


def _packet_id_from_command(command: str) -> str:
    command_text = _text(command)
    if not command_text:
        return ""
    try:
        parts = shlex.split(command_text)
    except ValueError:
        return ""
    for index, part in enumerate(parts):
        if part in {"--packet-id", "--packet"} and index + 1 < len(parts):
            return _text(parts[index + 1])
        for prefix in ("--packet-id=", "--packet="):
            if part.startswith(prefix):
                return _text(part[len(prefix) :])
    return ""


def _should_surface_plan_override(agent_decision: Any, *, required_action: str) -> bool:
    if required_action not in {"resolve_blocker", "repair_startup_authority"}:
        return False
    if _is_active_edit_only_override(agent_decision):
        return False
    if _truthy(_field(agent_decision, "may_mutate")):
        return False
    if _text(_field(agent_decision, "active_packet_id")):
        return False
    if _text(_field(agent_decision, "attention_packet_id")):
        return False
    return bool(_text(_field(agent_decision, "actor_id")))


def _plan_override_command(agent_decision: Any, *, next_slice_id: str) -> str:
    command = [
        "python3",
        "dev/scripts/devctl.py",
        "develop",
        "next",
        "--actor",
        _text(_field(agent_decision, "actor_id")) or "codex",
        "--slice-id",
        next_slice_id,
        "--operator-override",
        "--override-scope",
        EDIT_ONLY_OVERRIDE_SCOPE,
    ]
    reason = (
        _text(_field(agent_decision, "why_not_done"))
        or _text(_field(agent_decision, "top_blocker"))
        or DEFAULT_OPERATOR_OVERRIDE_REASON
    )
    command.extend(
        [
            "--override-reason",
            reason,
            "--override-by",
            OPERATOR_OVERRIDE_REQUESTOR,
            "--format",
            "md",
        ]
    )
    return shlex.join(command)


def _is_active_edit_only_override(agent_decision: Any) -> bool:
    if _truthy(_field(agent_decision, "operator_override_edit_allowed")):
        return True
    if _truthy(_field(agent_decision, "operator_override_active")):
        scope = _text(_field(agent_decision, "operator_override_scope"))
        return not scope or scope == "edit-only"
    override = _field(agent_decision, "operator_override")
    if isinstance(override, Mapping):
        if not _truthy(override.get("active")):
            return False
        if _text(override.get("scope")) and _text(override.get("scope")) != "edit-only":
            return False
        return True
    return _text(_field(agent_decision, "loop_mode")) == "operator_override_edit"


def _edit_only_override_why_not_done(agent_decision: Any) -> str:
    blocked = _field(agent_decision, "blocked_actions")
    blocked_actions = (
        tuple(_text(item) for item in blocked if _text(item))
        if isinstance(blocked, (list, tuple))
        else ()
    )
    if any(
        action in {"vcs.stage", "vcs.commit", "vcs.push"}
        for action in blocked_actions
    ):
        return (
            "Edit-only operator override is active; continue implementation edits "
            "while staging, commit, and push remain blocked."
        )
    return "Edit-only operator override is active; continue implementation edits."


def _final_action_for_agent_loop(
    required_action: str,
    continuation: DevelopmentContinuationRequiredSignal,
) -> str:
    if required_action == "post_continuation_anchor":
        return "post_continuation"
    if required_action in {
        "open_packet_body",
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
        "open_packet_body",
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
