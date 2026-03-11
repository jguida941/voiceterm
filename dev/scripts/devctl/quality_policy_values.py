"""Value coercion helpers for quality-policy resolution."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def coerce_enabled_ids(value: Any, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, list):
        return fallback
    return tuple(str(item).strip() for item in value if str(item).strip()) or fallback


def coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    return default


def coerce_extra_args(value: Any) -> tuple[str, ...] | None:
    return (
        tuple(str(item) for item in value if str(item).strip())
        if isinstance(value, list)
        else None
    )


def coerce_overrides(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    overrides: dict[str, dict[str, Any]] = {}
    for raw_script_id, raw_override in value.items():
        script_id = str(raw_script_id).strip()
        if not script_id or not isinstance(raw_override, dict):
            continue
        override: dict[str, Any] = {}
        step_name = raw_override.get("step_name")
        if isinstance(step_name, str) and step_name.strip():
            override["step_name"] = step_name.strip()
        extra_args = coerce_extra_args(raw_override.get("extra_args"))
        if extra_args is not None:
            override["extra_args"] = extra_args
        if isinstance(raw_override.get("enabled"), bool):
            override["enabled"] = raw_override["enabled"]
        if override:
            overrides[script_id] = override
    return overrides


def coerce_guard_configs(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    configs: dict[str, dict[str, Any]] = {}
    for raw_script_id, raw_config in value.items():
        script_id = str(raw_script_id).strip()
        if not script_id or not isinstance(raw_config, dict):
            continue
        configs[script_id] = deepcopy(raw_config)
    return configs
