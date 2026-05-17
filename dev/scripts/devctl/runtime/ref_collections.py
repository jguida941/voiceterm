"""Small collection helpers for runtime evidence references."""

from __future__ import annotations

from collections.abc import Iterable

from .value_coercion import coerce_string


def unique_refs(values: Iterable[str]) -> tuple[str, ...]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in values:
        ref = coerce_string(value)
        if not ref or ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return tuple(refs)


__all__ = ["unique_refs"]
