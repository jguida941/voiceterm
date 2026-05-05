"""Shared helper for reading a single string field from a Mapping or object.

Multiple typed-state consumers need to read a single named field from values
that may arrive as either ``Mapping[str, object]`` rows or as @dataclass / typed
objects, normalize ``None`` to ``""``, and return a stripped ``str``. This
helper centralizes that pattern so the same body does not get copy-pasted
across runtime and command modules (caught by check_function_duplication).
"""

from __future__ import annotations

from collections.abc import Mapping


def read_string_field(value: object | None, name: str) -> str:
    """Return ``str(value[name])`` or ``str(getattr(value, name))`` stripped.

    Returns ``""`` when ``value`` is ``None`` or when the resolved field is
    ``None``/missing. Mappings take precedence; falls back to attribute lookup
    for typed/dataclass values.
    """
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return str(value.get(name) or "").strip()
    return str(getattr(value, name, "") or "").strip()


__all__ = ["read_string_field"]
