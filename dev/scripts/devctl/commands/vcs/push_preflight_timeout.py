"""Timeout policy helpers for governed push preflight execution."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from ...common import CommandRunPolicy

PUSH_PREFLIGHT_TIMEOUT_SECONDS = 3900


def build_preflight_command_kwargs(
    command_runner: Any,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"cwd": repo_root}
    if command_runner_accepts_policy(command_runner):
        kwargs["policy"] = CommandRunPolicy(
            timeout_seconds=PUSH_PREFLIGHT_TIMEOUT_SECONDS,
        )
    return kwargs


def command_runner_accepts_policy(command_runner: Any) -> bool:
    target = getattr(command_runner, "side_effect", None)
    if callable(target):
        command_runner = target
    try:
        parameters = inspect.signature(command_runner).parameters
    except (TypeError, ValueError):
        return False
    return "policy" in parameters or any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )


__all__ = [
    "PUSH_PREFLIGHT_TIMEOUT_SECONDS",
    "build_preflight_command_kwargs",
    "command_runner_accepts_policy",
]
