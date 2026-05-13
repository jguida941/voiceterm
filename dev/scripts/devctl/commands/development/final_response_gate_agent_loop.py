"""Agent-loop helpers for the typed final-response gate."""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from pathlib import PurePath
from typing import Any

from .orchestration_models import DevelopmentContinuationRequiredSignal
from ...runtime.agent_loop_operator_override import (
    DEFAULT_OPERATOR_OVERRIDE_REASON,
    EDIT_ONLY_OVERRIDE_SCOPE,
    OPERATOR_OVERRIDE_REQUESTOR,
)


def agent_loop_blocking_packet_id(
    agent_decision: Any,
    *,
    required_action: str,
    next_required_command: str,
) -> str:
    command_packet_id = packet_id_from_command(next_required_command)
    if required_action == "open_packet_body" and command_packet_id:
        return command_packet_id
    return (
        _text(_field(agent_decision, "active_packet_id"))
        or _text(_field(agent_decision, "attention_packet_id"))
        or command_packet_id
    )


def prioritized_agent_loop_decisions(decisions: tuple[Any, ...]) -> tuple[Any, ...]:
    """Prefer actionable peer packet and mutation-owner repair over local stubs."""
    return tuple(sorted(decisions, key=agent_loop_decision_priority))


def agent_loop_decision_priority(agent_decision: Any) -> tuple[int, int]:
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
            is_status_probe_command(next_command)
            or not is_executable_next_command(next_command)
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


def is_status_probe_command(command: str) -> bool:
    return "review-channel --action status" in command


def is_executable_next_command(command: str) -> bool:
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
        return python_invokes_devctl(parts[1:])
    return executable == "uv" and uv_invokes_devctl(parts[1:])


def python_invokes_devctl(args: list[str]) -> bool:
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


def uv_invokes_devctl(args: list[str]) -> bool:
    if len(args) >= 3 and args[0] == "run":
        executable = PurePath(args[1]).name
        if executable == "python" or executable.startswith("python"):
            return python_invokes_devctl(args[2:])
        return executable in {"devctl", "devctl.py"}
    return False


def agent_loop_next_required_command(
    agent_decision: Any,
    *,
    continuation: DevelopmentContinuationRequiredSignal,
    required_action: str,
    next_slice_id: str,
) -> str:
    next_command = _text(_field(agent_decision, "next_command"))
    next_loop_command = _text(_field(agent_decision, "next_loop_command"))
    if is_active_edit_only_override(agent_decision):
        return ""
    if (
        should_surface_plan_override(agent_decision, required_action=required_action)
        and next_slice_id
        and (not next_command or next_command == next_loop_command)
    ):
        return plan_override_command(agent_decision, next_slice_id=next_slice_id)
    return fallback_next_required_command(
        next_command or next_loop_command or continuation.next_required_command,
        actor=_text(_field(agent_decision, "actor_id")),
    )


def fallback_next_required_command(command: str, *, actor: str = "") -> str:
    command_text = _text(command)
    if command_text:
        return command_text
    actor_arg = f" --actor {shlex.quote(actor)}" if actor else ""
    return f"python3 dev/scripts/devctl.py develop next{actor_arg} --format md"


def packet_id_from_command(command: str) -> str:
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


def should_surface_plan_override(agent_decision: Any, *, required_action: str) -> bool:
    if required_action not in {"resolve_blocker", "repair_startup_authority"}:
        return False
    if is_active_edit_only_override(agent_decision):
        return False
    if _truthy(_field(agent_decision, "may_mutate")):
        return False
    if _text(_field(agent_decision, "active_packet_id")):
        return False
    if _text(_field(agent_decision, "attention_packet_id")):
        return False
    return bool(_text(_field(agent_decision, "actor_id")))


def plan_override_command(agent_decision: Any, *, next_slice_id: str) -> str:
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


def is_active_edit_only_override(agent_decision: Any) -> bool:
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


def edit_only_override_why_not_done(agent_decision: Any) -> str:
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


def final_action_for_agent_loop(
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


def final_user_action_for_agent_loop(required_action: str) -> str:
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


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"1", "true", "yes", "on"}
