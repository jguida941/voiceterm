"""Field extraction utilities for governance-import-findings."""

from __future__ import annotations

from typing import Any


def override_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def first_text(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def first_location_text(item: dict[str, Any], *keys: str) -> str | None:
    location = item.get("location")
    if not isinstance(location, dict):
        return None
    return first_text(location, *keys)


def first_int(item: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = item.get(key)
        if value is None or value == "":
            continue
        return parse_int(value, field_name=key)
    return None


def first_location_int(item: dict[str, Any], *keys: str) -> int | None:
    location = item.get("location")
    if not isinstance(location, dict):
        return None
    return first_int(location, *keys)


def parse_int(value: object, *, field_name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer: {value!r}") from exc
    if result <= 0:
        raise ValueError(f"{field_name} must be positive: {value!r}")
    return result
