"""Field-access helpers shared by the governed VCS executor."""

from __future__ import annotations

from collections.abc import Mapping


def field(value: object, key: str, default: object = None) -> object:
    """Return one keyed field from a mapping or attribute object."""
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def mapping(value: object) -> Mapping[str, object]:
    """Return a mapping value or one empty mapping."""
    return value if isinstance(value, Mapping) else {}


def string_value(value: object) -> str:
    """Return one stripped string value."""
    return str(value or "").strip()


def string_field(value: object, key: str) -> str:
    """Return one string field from a mapping or attribute object."""
    return string_value(field(value, key, ""))


def bool_value(value: object, *, default: bool = False) -> bool:
    """Return one parsed boolean value with a configurable default."""
    if value is None:
        return default
    raw = value
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return bool(raw)


def bool_field(value: object, key: str, *, default: bool = False) -> bool:
    """Return one boolean field from a mapping or attribute object."""
    return bool_value(field(value, key, default), default=default)
