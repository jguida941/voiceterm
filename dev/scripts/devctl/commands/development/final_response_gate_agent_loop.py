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
from ...runtime.value_coercion import coerce_bool


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
    # v4.45.5 (rev_pkt_4743): shared coerce_bool for may_mutate so projection
    # values like ``"false"`` are not ranked as mutation-capable.
    may_mutate = coerce_bool(_field(agent_decision, "may_mutate"))
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
    """Return True only when the next command is a safe, non-governed
    devctl invocation.

    v4.42 (rev_pkt_4714 Finding 1): codex caught this function returning
    True for ``python3 dev/scripts/devctl.py push --execute`` — a governed
    mutation that the final-response gate MUST NOT auto-execute. The fix
    delegates to ``classify_command_mutation`` so any non-``none`` risk
    class is rejected, while preserving the devctl-family check for read-
    only commands.
    """
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
    is_devctl_family = (
        executable in {"devctl", "devctl.py"}
        or (executable == "python" or executable.startswith("python"))
        and python_invokes_devctl(parts[1:])
        or (executable == "uv" and uv_invokes_devctl(parts[1:]))
    )
    if not is_devctl_family:
        return False
    # v4.42: reject governed mutations even within the devctl family.
    from ...runtime.command_envelope_classification import classify_command_mutation  # noqa: PLC0415
    _, risk = classify_command_mutation(command_text)
    return risk == "none"


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
    # v4.45.2 (rev_pkt_4737 / rev_pkt_4738): drop ``next_loop_command`` from
    # the fallback chain. After v4.45, ``AgentLoopDecision.next_command`` is
    # the canonical source for the actor's next executable command —
    # populated when ``can_run_next_command=True``, empty when the actor is
    # blocked. Falling back to ``next_loop_command`` here re-emitted the
    # same agent-loop invocation as ``next_required_command`` even when the
    # actor was blocked, producing an end-to-end read-only self-loop
    # downstream (codex's rev_pkt_4737 dogfood reproduction). The blocker
    # owner/target/reason/repair_command fields stay populated on the
    # AgentLoopDecision so consumers can surface the typed unrunnable
    # blocker without re-issuing the loop command.
    #
    # v4.45.3 (rev_pkt_4739 Hooke #2): when the decision is blocked
    # (can_run_next_command=False) AND next_command is empty AND
    # continuation also has no executable command, return empty directly
    # instead of letting ``fallback_next_required_command`` synthesize a
    # default ``develop next`` invocation. The blocked typed handoff
    # carries the actor's instructions via the blocker_* fields; the
    # fabricated ``develop next`` would itself be a no-progress hop the
    # actor cannot meaningfully complete in the blocked state.
    # v4.45.4 (rev_pkt_4742): use shared runtime.coerce_bool so projection
    # rows carrying ``"false"`` / ``"0"`` parse correctly. Raw ``bool()``
    # treated those as True and silently re-enabled the develop-next
    # fallback for blocked actors that codex's verbatim repro captured.
    can_run = coerce_bool(_field(agent_decision, "can_run_next_command"))
    upstream_command = next_command or continuation.next_required_command
    if not upstream_command and not can_run:
        return ""
    return fallback_next_required_command(
        upstream_command,
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
    if required_action not in {
        "resolve_blocker",
        "repair_startup_authority",
        "wait_for_scoped_packet",
    }:
        return False
    if is_active_edit_only_override(agent_decision):
        return False
    if coerce_bool(_field(agent_decision, "may_mutate")):
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
    if coerce_bool(_field(agent_decision, "operator_override_edit_allowed")):
        return True
    if coerce_bool(_field(agent_decision, "operator_override_active")):
        scope = _text(_field(agent_decision, "operator_override_scope"))
        return not scope or scope == "edit-only"
    override = _field(agent_decision, "operator_override")
    if isinstance(override, Mapping):
        if not coerce_bool(override.get("active")):
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


# v4.45.5 (rev_pkt_4743): local ``_truthy`` retired in favor of shared
# ``runtime.value_coercion.coerce_bool``. The two diverged on ``"y"``
# (truthy treated as False; coerce_bool treats as True) — that mismatch
# was unintentional and the shared normalizer is now the single
# canonical boolean coercion in this surface.
