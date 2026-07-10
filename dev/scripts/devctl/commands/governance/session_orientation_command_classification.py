"""Typed command classification for session-orientation next commands."""

from __future__ import annotations

import shlex
from enum import Enum
from pathlib import PurePath


class CommandClassification(str, Enum):
    """Stable command classes used by session-orientation reducers."""

    GOVERNED_PUSH = "governed_push"
    UNKNOWN = "unknown"


def classify_devctl_command(command: str) -> CommandClassification:
    """Classify a shell command without substring matching."""
    tokens = _tokens(command)
    if not tokens:
        return CommandClassification.UNKNOWN
    executable_index = _first_executable_index(tokens)
    if executable_index is None:
        return CommandClassification.UNKNOWN
    executable = _basename(tokens[executable_index])
    if executable in {"devctl", "devctl.py"}:
        return _classify_devctl_argv(tokens, executable_index + 1)
    if _is_python_executable(executable):
        devctl_index = _python_devctl_script_index(tokens, executable_index + 1)
        if devctl_index is not None:
            return _classify_devctl_argv(tokens, devctl_index + 1)
    return CommandClassification.UNKNOWN


def _tokens(command: str) -> list[str]:
    try:
        return shlex.split(str(command or ""))
    except ValueError:
        return []


def _first_executable_index(tokens: list[str]) -> int | None:
    for index, token in enumerate(tokens):
        if _is_env_assignment(token):
            continue
        return index
    return None


def _is_env_assignment(token: str) -> bool:
    name, separator, _value = token.partition("=")
    return bool(separator and name and name.replace("_", "").isalnum())


def _classify_devctl_argv(
    tokens: list[str],
    action_index: int,
) -> CommandClassification:
    if action_index < len(tokens) and tokens[action_index] == "push":
        return CommandClassification.GOVERNED_PUSH
    return CommandClassification.UNKNOWN


def _python_devctl_script_index(
    tokens: list[str],
    start_index: int,
) -> int | None:
    index = start_index
    while index < len(tokens):
        token = tokens[index]
        if token == "-m":
            module_index = index + 1
            if module_index < len(tokens) and tokens[module_index].endswith("devctl"):
                return module_index
            return None
        if token.startswith("-"):
            index += 1
            continue
        if _basename(token) == "devctl.py":
            return index
        return None
    return None


def _basename(token: str) -> str:
    return PurePath(token).name


def _is_python_executable(executable: str) -> bool:
    return executable == "python" or executable.startswith("python")


__all__ = ["CommandClassification", "classify_devctl_command"]
