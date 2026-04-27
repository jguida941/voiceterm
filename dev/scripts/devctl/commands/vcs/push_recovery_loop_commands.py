"""Allowlisted command helpers for governed push recovery-loop repair."""

from __future__ import annotations

import os
import shlex
import sys
import time
from pathlib import Path

_REVIEW_CHANNEL_ACTIONS = frozenset(
    {
        "bridge-poll",
        "doctor",
        "ensure",
        "launch",
        "recover",
        "status",
    }
)
_HEADLESS_REQUIRED_ACTIONS = frozenset(
    {"doctor", "ensure", "launch", "recover", "status"}
)


def bounded_recovery_command(command: str) -> tuple[list[str], str]:
    """Return an argv for allowlisted recovery commands, or a block reason."""
    raw = str(command or "").strip()
    if not raw:
        return ([], "missing_next_command")
    try:
        parts = shlex.split(raw)
    except ValueError:
        return ([], "next_command_parse_failed")
    block_reason = _review_channel_block_reason(parts)
    if block_reason:
        return ([], block_reason)

    normalized = list(parts)
    action = option_value(parts, "--action")
    if action in _HEADLESS_REQUIRED_ACTIONS and not option_value(parts, "--terminal"):
        normalized.extend(["--terminal", "none"])
    _bound_follow_options(normalized, action)
    if action == "launch" and "--await-ack-seconds" not in normalized:
        normalized.extend(["--await-ack-seconds", "30"])
    return (normalized, "")


def is_push_execute_command(command: str) -> bool:
    try:
        parts = shlex.split(str(command or ""))
    except ValueError:
        return False
    devctl_index = devctl_index_for(parts)
    if devctl_index is None or devctl_index + 1 >= len(parts):
        return False
    return parts[devctl_index + 1] == "push" and "--execute" in parts


def run_startup_context_summary(
    runner,
    *,
    repo_root: Path,
    deadline: float,
    attempt: int,
) -> dict[str, object]:
    return runner(
        f"push-recovery-startup-context-{attempt + 1}",
        [
            sys.executable,
            "dev/scripts/devctl.py",
            "startup-context",
            "--format",
            "summary",
        ],
        cwd=repo_root,
        env=budget_env(deadline),
    )


def run_bounded_command(
    runner,
    command: list[str],
    *,
    repo_root: Path,
    deadline: float,
    attempt: int,
) -> dict[str, object]:
    action = option_value(command, "--action") or "review-channel"
    return runner(
        f"push-recovery-review-channel-{action}-{attempt + 1}",
        command,
        cwd=repo_root,
        env=budget_env(deadline),
    )


def budget_env(deadline: float) -> dict[str, str]:
    env = dict(os.environ)
    remaining = max(1, int(deadline - time.monotonic()))
    env["VOICETERM_DEVCTL_LIVE_OUTPUT_TIMEOUT_SECONDS"] = str(remaining)
    return env


def option_value(parts: list[str], option: str) -> str:
    try:
        index = parts.index(option)
    except ValueError:
        return ""
    value_index = index + 1
    if value_index >= len(parts):
        return ""
    return parts[value_index]


def devctl_index_for(parts: list[str]) -> int | None:
    for index, part in enumerate(parts):
        if part.endswith("dev/scripts/devctl.py") or part == "devctl.py":
            return index
    return None


def _review_channel_block_reason(parts: list[str]) -> str:
    if not parts:
        return "missing_next_command"
    devctl_index = devctl_index_for(parts)
    if devctl_index is None:
        return "next_command_not_devctl"
    subcommand_index = devctl_index + 1
    if subcommand_index >= len(parts):
        return "next_command_missing_subcommand"
    if parts[subcommand_index] != "review-channel":
        return "next_command_not_review_channel"
    action = option_value(parts, "--action")
    if action not in _REVIEW_CHANNEL_ACTIONS:
        return f"review_channel_action_not_bounded:{action or 'missing'}"
    terminal = option_value(parts, "--terminal")
    if terminal and terminal != "none" and action in _HEADLESS_REQUIRED_ACTIONS:
        return "review_channel_terminal_not_headless"
    return ""


def _bound_follow_options(parts: list[str], action: str) -> None:
    if action != "ensure" or "--follow" not in parts:
        return
    if "--max-follow-snapshots" not in parts:
        parts.extend(["--max-follow-snapshots", "1"])
    if "--follow-interval-seconds" not in parts:
        parts.extend(["--follow-interval-seconds", "1"])
    if "--follow-inactivity-timeout-seconds" not in parts:
        parts.extend(["--follow-inactivity-timeout-seconds", "1"])


__all__ = [
    "bounded_recovery_command",
    "budget_env",
    "devctl_index_for",
    "is_push_execute_command",
    "option_value",
    "run_bounded_command",
    "run_startup_context_summary",
]
