"""Shared construction helpers for session-resume context objects."""

from __future__ import annotations

from dataclasses import fields, replace
from typing import TypeVar

T = TypeVar("T")


def replace_context_values(
    context: T | None,
    values: dict[str, object],
    *,
    context_type: type[T],
    label: str,
) -> T:
    """Return a context object with checked keyword overrides applied."""
    if context is None:
        return context_type(**values)
    if not values:
        return context
    names = {field.name for field in fields(context)}
    unknown = sorted(set(values) - names)
    if unknown:
        joined = ", ".join(unknown)
        raise TypeError(f"unknown {label} field(s): {joined}")
    return replace(context, **values)


__all__ = ["replace_context_values"]
