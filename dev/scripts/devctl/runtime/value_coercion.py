"""Shared runtime coercion helpers for contract parsers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def coerce_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def coerce_mapping_items(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    items: list[Mapping[str, object]] = []
    for row in value:
        mapping = coerce_mapping(row)
        if mapping:
            items.append(mapping)
    return tuple(items)


def coerce_string(value: object) -> str:
    return str(value).strip() if value is not None else ""


def coerce_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def coerce_string_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    items: list[str] = []
    for row in value:
        text = coerce_string(row)
        if text:
            items.append(text)
    return tuple(items)
