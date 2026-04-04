"""Shell command splitting, policy injection, and interpreter normalization."""

import re
import shlex
import sys
from pathlib import Path

from .common_io_resolve import resolve_repo_owned_pytest_target, resolve_repo_python_target
from .config import REPO_ROOT

_ENV_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
_POLICY_AWARE_SUBCOMMANDS = frozenset(
    {
        "check",
        "check-router",
        "docs-check",
        "probe-report",
        "push",
        "quality-policy",
        "render-surfaces",
        "report",
        "status",
        "triage",
    }
)


def split_shell_prefix(command: str) -> tuple[list[str], list[str]] | None:
    """Split a shell command into env assignments and argv tokens."""
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    env_prefix: list[str] = []
    while parts and _ENV_ASSIGNMENT_RE.fullmatch(parts[0]):
        env_prefix.append(parts.pop(0))
    return env_prefix, parts


def inject_quality_policy_command(
    command: str,
    quality_policy_path: str | None,
) -> str:
    """Append a quality-policy override to policy-aware repo commands."""
    if not quality_policy_path:
        return command
    split = split_shell_prefix(command)
    if split is None:
        return command
    env_prefix, parts = split
    if len(parts) < 2 or parts[1] != "dev/scripts/devctl.py":
        return command
    command_args = parts[2:]
    if not command_args or command_args[0] not in _POLICY_AWARE_SUBCOMMANDS:
        return command
    if "--quality-policy" in command_args:
        return command
    command_args.extend(["--quality-policy", quality_policy_path])
    rebuilt = shlex.join([parts[0], parts[1], *command_args])
    return " ".join([*env_prefix, rebuilt]) if env_prefix else rebuilt


def normalize_repo_python_shell_command(command: str) -> str:
    """Force repo-owned Python shell commands onto the current interpreter."""
    split = split_shell_prefix(command)
    if split is None:
        return command
    env_prefix, parts = split
    if len(parts) < 2:
        return command
    if parts[0] not in {"python3", "python3.11", sys.executable}:
        return command
    target = parts[1]
    if target.endswith(".py"):
        resolved = resolve_repo_python_target(target, cwd=REPO_ROOT)
        if resolved is None:
            return command
    elif target == "-m":
        resolved = resolve_repo_owned_pytest_target(parts, cwd=REPO_ROOT)
        if resolved is None:
            return command
    else:
        return command
    parts[0] = sys.executable or "python3"
    rebuilt = shlex.join(parts)
    return " ".join([*env_prefix, rebuilt]) if env_prefix else rebuilt
