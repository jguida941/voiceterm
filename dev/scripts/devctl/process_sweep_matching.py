"""Pure path and command predicates for process-sweep classification."""

from __future__ import annotations

import os
from pathlib import Path

from .process_sweep_config import (
    BACKGROUND_TTY_VALUES,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    REPO_BACKGROUND_COMMAND_RE,
    REPO_ROOT_RESOLVED,
    REPO_SHELL_WRAPPER_RE,
)


def normalize_repo_path(raw_path: str | None, *, allow_relative: bool = False) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        if not allow_relative:
            return None
        if not raw_path.startswith(("./", "../")):
            return None
        path = REPO_ROOT_RESOLVED / path
    try:
        return path.resolve(strict=False)
    except OSError:
        return None


def path_is_under_repo(raw_path: str | None, *, allow_relative: bool = False) -> bool:
    normalized = normalize_repo_path(raw_path, allow_relative=allow_relative)
    if normalized is None:
        return False
    try:
        normalized.relative_to(REPO_ROOT_RESOLVED)
    except ValueError:
        return False
    return True


def command_executable_token(command: str) -> str:
    stripped = command.strip()
    if not stripped:
        return ""
    return stripped.split(None, 1)[0]


def command_executable_basename(command: str) -> str:
    return os.path.basename(command_executable_token(command))


def is_interactive_shell_command(command: str) -> bool:
    """Return True for plain interactive shell sessions like `/bin/zsh -il`."""
    executable_name = command_executable_basename(command)
    if executable_name not in {"bash", "zsh", "sh"}:
        return False

    tokens = command.strip().split()
    if len(tokens) <= 1:
        return True
    for token in tokens[1:]:
        if not token.startswith("-"):
            return False
        flags = token[1:]
        if not flags or any(flag not in {"i", "l"} for flag in flags):
            return False
    return True


def row_looks_backgrounded(row: dict) -> bool:
    return str(row.get("tty", "")).strip() in BACKGROUND_TTY_VALUES


def is_attached_noninteractive_repo_helper(row: dict) -> bool:
    """Return True for attached repo tooling helpers that are not interactive shells/REPLs."""
    if row_looks_backgrounded(row):
        return False
    executable_name = command_executable_basename(row.get("command", ""))
    tokens = str(row.get("command", "")).strip().split()

    if executable_name in {"bash", "zsh", "sh"}:
        command = str(row.get("command", ""))
        return bool(REPO_SHELL_WRAPPER_RE.search(command)) and not is_interactive_shell_command(
            command
        )
    if executable_name.startswith("python"):
        if len(tokens) <= 1:
            return False
        return tokens[1] != "-"
    if executable_name == "node":
        if len(tokens) <= 1:
            return False
        return tokens[1] != "-"
    return executable_name in {
        "npm",
        "npx",
        "pnpm",
        "uv",
        "make",
        "just",
        "screen",
        "SCREEN",
        "tmux",
    } or executable_name.startswith("qemu-system-")


def is_repo_background_candidate(row: dict) -> bool:
    """Return True for stale/orphaned detached helpers still rooted in repo cwd."""
    elapsed = int(row.get("elapsed_seconds", -1))
    if row.get("ppid") != 1 and elapsed < DEFAULT_STALE_MIN_AGE_SECONDS:
        return False

    command = row["command"]
    executable_token = command_executable_token(command)
    executable_name = command_executable_basename(command)
    executable_is_repo_path = path_is_under_repo(executable_token, allow_relative=True)
    cwd_is_repo_path = path_is_under_repo(row.get("cwd"))
    if not executable_is_repo_path and not cwd_is_repo_path:
        return False
    if row.get("ppid") == 1:
        if is_interactive_shell_command(command):
            return False
        if executable_is_repo_path:
            return True
        if not row_looks_backgrounded(row):
            return not bool(REPO_BACKGROUND_COMMAND_RE.match(executable_name))
        if executable_name in {"bash", "zsh", "sh"}:
            return cwd_is_repo_path or bool(REPO_SHELL_WRAPPER_RE.search(command))
        return bool(REPO_BACKGROUND_COMMAND_RE.match(executable_name))
    if not row_looks_backgrounded(row):
        return False
    if executable_is_repo_path:
        return True
    if executable_name in {"bash", "zsh", "sh"}:
        if is_interactive_shell_command(command):
            return False
        return cwd_is_repo_path or bool(REPO_SHELL_WRAPPER_RE.search(command))
    return bool(REPO_BACKGROUND_COMMAND_RE.match(executable_name))
