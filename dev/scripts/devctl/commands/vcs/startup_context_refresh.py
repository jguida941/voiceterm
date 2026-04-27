"""Startup-context refresh output classification for governed VCS preflight."""

from __future__ import annotations

import json
from collections.abc import Mapping

RECOVERABLE_STARTUP_REFRESH_ATTENTION_STATUSES = frozenset(
    {"runtime_missing", "review_loop_relaunch_required"}
)
RECOVERABLE_STARTUP_REFRESH_ACTIONS = frozenset(
    {"relaunch_allowed", "observe_only"}
)


def startup_context_advisory_from_step(step: Mapping[str, object]) -> tuple[str, str]:
    """Return the advisory action from a valid startup-context payload."""
    output = _step_output(step)
    if not output:
        return "", ""
    payload = _parse_startup_context_output(output)
    if payload is None:
        return "", ""
    action = str(
        payload.get("action") or payload.get("advisory_action") or ""
    ).strip()
    advisory_action = str(payload.get("advisory_action") or action).strip()
    if not action or (advisory_action and advisory_action != action):
        return "", ""
    reason = str(
        payload.get("reason") or payload.get("advisory_reason") or ""
    ).strip()
    return action, reason


def startup_context_recovery_hint_from_step(
    step: Mapping[str, object],
) -> dict[str, str]:
    """Return bounded recovery fields from a failed startup-context refresh."""
    output = _step_output(step)
    if not output:
        return {}
    payload = _parse_startup_context_output(output)
    if payload is None:
        return {}
    attention_status = _text(payload.get("attention_status"))
    attention = payload.get("attention")
    if not attention_status and isinstance(attention, Mapping):
        attention_status = _text(attention.get("status"))
    recovery_action = _text(payload.get("recovery_action"))
    recovery_authority = payload.get("recovery_authority")
    if not recovery_action and isinstance(recovery_authority, Mapping):
        recovery_action = _text(recovery_authority.get("recovery_action"))
    hint: dict[str, str] = {}
    hint["attention_status"] = attention_status
    hint["recovery_action"] = recovery_action
    hint["implementation_permission"] = _text(payload.get("implementation_permission"))
    hint["action"] = _text(payload.get("action") or payload.get("advisory_action"))
    hint["reason"] = _text(payload.get("reason") or payload.get("advisory_reason"))
    hint["next"] = _text(
        payload.get("next")
        or payload.get("next_step_command")
        or payload.get("push_next_step_command")
    )
    return hint


def startup_context_refresh_has_bounded_recovery(
    step: Mapping[str, object],
) -> bool:
    """Return True when failed startup-context output authorizes bounded repair."""
    hint = startup_context_recovery_hint_from_step(step)
    return (
        hint.get("attention_status")
        in RECOVERABLE_STARTUP_REFRESH_ATTENTION_STATUSES
        and hint.get("recovery_action") in RECOVERABLE_STARTUP_REFRESH_ACTIONS
    )


def _parse_startup_context_output(output: str) -> dict[str, object] | None:
    """Parse startup-context JSON or its compact summary key/value projection."""
    payload = _parse_startup_context_json(output)
    if payload is not None:
        return payload
    return _parse_startup_context_summary(output)


def _parse_startup_context_json(output: str) -> dict[str, object] | None:
    stripped = output.strip()
    if not stripped:
        return None
    candidates = [stripped]
    start = stripped.find("{")
    end = stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except ValueError:
            continue
        if not isinstance(payload, dict):
            continue
        if str(payload.get("contract_id") or "").strip() != "StartupContext":
            continue
        return payload
    return None


def _parse_startup_context_summary(output: str) -> dict[str, object] | None:
    payload: dict[str, object] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            payload[key] = value.strip()
    if "action" not in payload or "reason" not in payload:
        return None
    summary_markers = {
        "implementation_permission",
        "observed_control_topology",
        "attention_revision",
        "interaction_mode",
    }
    if not any(marker in payload for marker in summary_markers):
        return None
    return payload


def _text(value: object) -> str:
    return str(value or "").strip()


def _step_output(step: Mapping[str, object]) -> str:
    return str(
        step.get("failure_output")
        or step.get("output")
        or step.get("stdout")
        or step.get("error")
        or ""
    ).strip()
