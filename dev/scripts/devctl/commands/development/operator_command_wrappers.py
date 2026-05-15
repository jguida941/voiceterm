"""Operator-friendly wrappers for long runnable commands."""

from __future__ import annotations

import hashlib
import shlex
from collections.abc import Iterable

from .models import OperatorCommandWrapper

MAX_OPERATOR_COMMAND_INLINE_LENGTH = 100
WRAPPED_COMMAND_LINE_LENGTH = 78


def build_operator_command_wrappers(
    command_sources: Iterable[tuple[str, str]],
    *,
    threshold: int = MAX_OPERATOR_COMMAND_INLINE_LENGTH,
) -> tuple[OperatorCommandWrapper, ...]:
    """Return typed wrappers for commands too long to scan or copy safely."""
    wrappers: list[OperatorCommandWrapper] = []
    seen_commands: set[str] = set()
    for source, command in command_sources:
        command_text = str(command or "").strip()
        if len(command_text) <= threshold or command_text in seen_commands:
            continue
        seen_commands.add(command_text)
        wrappers.append(
            OperatorCommandWrapper(
                wrapper_id=_wrapper_id(command_text),
                source=str(source or "").strip() or "unknown",
                original_command=command_text,
                wrapped_command=_wrap_shell_command(command_text),
                command_length=len(command_text),
                threshold=threshold,
                reason="operator_command_exceeds_inline_threshold",
            )
        )
    return tuple(wrappers)


def _wrapper_id(command: str) -> str:
    digest = hashlib.sha256(command.encode("utf-8")).hexdigest()[:12]
    return f"opcmd-{digest}"


def _wrap_shell_command(command: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        return command
    if not parts:
        return command

    lines: list[str] = []
    current = ""
    for part in parts:
        token = shlex.quote(part)
        if not current:
            current = token
            continue
        candidate = f"{current} {token}"
        if len(candidate) <= WRAPPED_COMMAND_LINE_LENGTH:
            current = candidate
            continue
        lines.append(f"{current} \\")
        current = f"  {token}"
    lines.append(current)
    return "\n".join(lines)


__all__ = [
    "MAX_OPERATOR_COMMAND_INLINE_LENGTH",
    "build_operator_command_wrappers",
]
