"""Startup-context payload helpers for governed push recovery-loop repair."""

from __future__ import annotations

import json

from .push_recovery_loop_commands import bounded_recovery_command

_BOUNDED_ATTENTION_STATUSES = frozenset(
    {
        "runtime_missing",
        "review_loop_relaunch_required",
    }
)
_BOUNDED_RECOVERY_ACTIONS = frozenset(
    {
        "observe_only",
        "relaunch_allowed",
    }
)


def startup_context_step_needs_recovery(step) -> bool:
    """Return true when a startup-context failure should be deferred to repair."""
    return payload_allows_bounded_recovery(startup_context_payload_from_step(step))


def startup_context_payload_from_step(step) -> dict[str, object]:
    """Extract StartupContext summary fields from a command-runner step."""
    if not isinstance(step, dict):
        return {}
    value = _payload_from_mapping(step)
    if value:
        return value
    text = "\n".join(
        str(step.get(key) or "")
        for key in ("failure_output", "stdout", "stderr", "output", "message")
        if str(step.get(key) or "").strip()
    )
    for payload in _json_payloads_from_text(text):
        value = _payload_from_mapping(payload)
        if value:
            return value
    return _payload_from_summary(text)


def payload_allows_bounded_recovery(payload: dict[str, object]) -> bool:
    if not payload:
        return False
    action = field_value(payload, "advisory_action") or field_value(payload, "action")
    attention_status = field_value(payload, "attention_status")
    recovery_action = _recovery_action(payload)
    bounded_command, _ = bounded_recovery_command(startup_next_command(payload))
    return (
        action == "repair_reviewer_loop"
        and bool(bounded_command)
        and attention_status in _BOUNDED_ATTENTION_STATUSES
        and recovery_action in _BOUNDED_RECOVERY_ACTIONS
    )


def startup_next_command(payload: dict[str, object]) -> str:
    command = field_value(payload, "next_command") or field_value(payload, "next")
    if command:
        return command
    action_routing = payload.get("action_routing")
    if isinstance(action_routing, dict):
        return field_value(action_routing, "next_command")
    authority = payload.get("authority_snapshot")
    if isinstance(authority, dict):
        return field_value(authority, "next_command")
    return ""


def field_value(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        return value.strip().strip("`'\"")
    if value is None:
        return ""
    return str(value).strip().strip("`'\"")


def compact_startup_payload(payload: dict[str, object]) -> dict[str, object]:
    keys = (
        "action",
        "advisory_action",
        "reason",
        "advisory_reason",
        "attention_status",
        "implementation_permission",
        "observed_control_topology",
        "recovery_action",
        "recovery_basis",
        "next_command",
        "next",
    )
    return {key: payload[key] for key in keys if key in payload}


def step_record(step: dict[str, object], *, payload: dict[str, object]) -> dict[str, object]:
    record = compact_step(step)
    if payload:
        record["startup_context"] = compact_startup_payload(payload)
    return record


def compact_step(step: object) -> dict[str, object]:
    if not isinstance(step, dict):
        return {}
    result: dict[str, object] = {}
    result["name"] = str(step.get("name") or "")
    result["returncode"] = returncode(step)
    if step.get("cmd"):
        result["cmd"] = list(step.get("cmd") or ())
    if step.get("duration_s") is not None:
        result["duration_s"] = step.get("duration_s")
    if step.get("failure_output"):
        result["failure_output"] = str(step.get("failure_output"))[:500]
    return result


def returncode(step: dict[str, object]) -> int:
    try:
        return int(step.get("returncode", 1))
    except (TypeError, ValueError):
        return 1


def _payload_from_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {}
    if str(value.get("contract_id") or "").strip() == "StartupContext":
        return dict(value)
    summary = value.get("summary")
    if isinstance(summary, dict):
        return _normalize_payload(dict(summary))
    payload = value.get("payload")
    if isinstance(payload, dict):
        return _payload_from_mapping(payload)
    return {}


def _json_payloads_from_text(text: str) -> tuple[object, ...]:
    candidates: list[str] = []
    stripped = text.strip()
    if stripped:
        candidates.append(stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    payloads: list[object] = []
    for candidate in candidates:
        try:
            payloads.append(json.loads(candidate))
        except json.JSONDecodeError:
            pass
    return tuple(payloads)


def _payload_from_summary(text: str) -> dict[str, object]:
    payload: dict[str, object] = {}
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            line = line[2:].strip()
        if not line:
            continue
        separator = "=" if "=" in line else ":" if ":" in line else ""
        if not separator:
            continue
        key, value = line.split(separator, 1)
        key = key.strip().strip("`")
        if key:
            payload[key] = value.strip().strip("`")
    return _normalize_payload(payload)


def _normalize_payload(payload: dict[str, object]) -> dict[str, object]:
    if "next_command" not in payload and "next" in payload:
        payload["next_command"] = payload["next"]
    attention = payload.get("attention")
    if isinstance(attention, dict) and "attention_status" not in payload:
        payload["attention_status"] = attention.get("status", "")
    authority = payload.get("authority_snapshot")
    if isinstance(authority, dict) and "next_command" not in payload:
        payload["next_command"] = authority.get("next_command", "")
    return payload


def _recovery_action(payload: dict[str, object]) -> str:
    recovery_action = field_value(payload, "recovery_action")
    if recovery_action:
        return recovery_action
    recovery_authority = payload.get("recovery_authority")
    if isinstance(recovery_authority, dict):
        return field_value(recovery_authority, "recovery_action")
    return ""


__all__ = [
    "compact_startup_payload",
    "compact_step",
    "field_value",
    "payload_allows_bounded_recovery",
    "returncode",
    "startup_context_payload_from_step",
    "startup_context_step_needs_recovery",
    "startup_next_command",
    "step_record",
]
