"""Shell-command classification for pytest runtime-policy checks."""

from __future__ import annotations

import shlex
from pathlib import Path

_RUN_WRAPPERS = {"uv", "poetry", "pipenv", "hatch"}
_RUN_WRAPPER_OPTIONS_WITH_VALUE = {
    "--config",
    "--env",
    "--extra",
    "--group",
    "--index-url",
    "--no-extra",
    "--no-group",
    "--no-with",
    "--python",
    "--with",
    "-C",
    "-E",
    "-P",
    "-p",
}
_SHELL_SEPARATORS = {"|", "&&", "||", ";"}


def is_unbounded_pytest_command(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    if "dev/scripts/devctl.py test-python" in command:
        return False
    command_starts = _command_start_indexes(parts)
    for index, part in enumerate(parts):
        if _is_pytest_binary(parts, index, command_starts):
            return True
        if _is_pytest_module(parts, index, command_starts):
            return True
    return False


def _is_pytest_binary(
    parts: list[str],
    index: int,
    command_starts: set[int],
) -> bool:
    if Path(parts[index]).name not in {"pytest", "py.test"}:
        return False
    return index in command_starts


def _is_pytest_module(
    parts: list[str],
    index: int,
    command_starts: set[int],
) -> bool:
    return (
        parts[index] == "-m"
        and index + 1 < len(parts)
        and parts[index + 1] == "pytest"
        and index > 0
        and _is_python_binary(parts[index - 1])
        and index - 1 in command_starts
    )


def _command_start_indexes(parts: list[str]) -> set[int]:
    starts: set[int] = set()
    index = 0
    while index < len(parts):
        segment_end = _next_separator_index(parts, index)
        start = _segment_command_start(parts, index, segment_end)
        if start is not None:
            starts.add(start)
            wrapper_start = _run_wrapper_command_start(parts, start, segment_end)
            if wrapper_start is not None:
                starts.add(wrapper_start)
        index = segment_end + 1
    return starts


def _next_separator_index(parts: list[str], start: int) -> int:
    for index in range(start, len(parts)):
        if parts[index] in _SHELL_SEPARATORS:
            return index
    return len(parts)


def _segment_command_start(
    parts: list[str],
    start: int,
    end: int,
) -> int | None:
    cursor = start
    while cursor < end and _is_assignment(parts[cursor]):
        cursor += 1
    if cursor < end and Path(parts[cursor]).name == "env":
        cursor = _skip_env_prefix(parts, cursor, end)
    while cursor < end and Path(parts[cursor]).name == "timeout":
        cursor = _skip_timeout_prefix(parts, cursor, end)
    return cursor if cursor < end else None


def _skip_env_prefix(parts: list[str], start: int, end: int) -> int:
    cursor = start + 1
    while cursor < end and (
        _is_assignment(parts[cursor]) or parts[cursor].startswith("-")
    ):
        cursor += 1
    return cursor


def _skip_timeout_prefix(parts: list[str], start: int, end: int) -> int:
    cursor = start + 1
    while cursor < end and parts[cursor].startswith("-"):
        cursor += 1
    if cursor < end:
        cursor += 1
    return cursor


def _run_wrapper_command_start(
    parts: list[str],
    start: int,
    end: int,
) -> int | None:
    if Path(parts[start]).name not in _RUN_WRAPPERS:
        return None
    if start + 2 >= end or parts[start + 1] != "run":
        return None
    cursor = start + 2
    while cursor < end and parts[cursor].startswith("-"):
        option = parts[cursor]
        cursor += 1
        if option in _RUN_WRAPPER_OPTIONS_WITH_VALUE and cursor < end:
            cursor += 1
    return cursor if cursor < end else None


def _is_assignment(part: str) -> bool:
    name, separator, _value = part.partition("=")
    return bool(
        separator and name and all(ch == "_" or ch.isalnum() for ch in name)
    )


def _is_python_binary(part: str) -> bool:
    return Path(part).name.startswith("python")
