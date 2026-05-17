"""Shared action helpers for ``devctl develop``."""

from __future__ import annotations

from typing import Any


def resolve_action(args: Any, *, default: str = "status") -> str:
    """Resolve positional and flag-style develop actions consistently."""
    return str(
        getattr(args, "action_flag", None)
        or getattr(args, "action", None)
        or default
    )


__all__ = ["resolve_action"]
