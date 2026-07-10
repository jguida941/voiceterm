"""Next-command fallback helpers for session orientation."""

from __future__ import annotations

from .session_orientation_command_classification import (
    CommandClassification,
    classify_devctl_command,
)
from .session_orientation_models import text


def fallback_next_command(
    payloads: dict[str, dict[str, object]],
    *,
    authority_allows_push: bool,
) -> str:
    """Return the next command from push decisions when authority omits one."""
    command = _first_text(
        payloads,
        ("review_status", "push_decision", "next_step_command"),
        ("startup", "push_decision", "next_step_command"),
    )
    if _is_governed_push_command(command) and not authority_allows_push:
        return ""
    return command


def _is_governed_push_command(command: str) -> bool:
    return classify_devctl_command(command) is CommandClassification.GOVERNED_PUSH


def _first_text(
    payloads: dict[str, dict[str, object]],
    *paths: tuple[str, ...],
) -> str:
    for path in paths:
        resolved = _text_at_path(payloads, path)
        if resolved:
            return resolved
    return ""


def _text_at_path(payloads: dict[str, dict[str, object]], path: tuple[str, ...]) -> str:
    value: object = payloads
    for key in path:
        if not isinstance(value, dict):
            return ""
        value = value.get(key)
    return text(value)


__all__ = ["fallback_next_command"]
