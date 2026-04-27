"""Startup-context refresh output classification for governed VCS preflight."""

from __future__ import annotations

import json
from collections.abc import Mapping


def startup_context_advisory_from_step(step: Mapping[str, object]) -> tuple[str, str]:
    """Return the advisory action from a valid startup-context payload."""
    output = str(step.get("failure_output") or "").strip()
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
