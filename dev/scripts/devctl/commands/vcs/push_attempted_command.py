"""Attempted-command rendering for governed push controller checks."""

from __future__ import annotations

from typing import Any


def push_attempted_argv(args: Any) -> list[str]:
    argv = ["push"]
    if bool(getattr(args, "execute", False)):
        argv.append("--execute")
    remote = str(getattr(args, "remote", "") or "").strip()
    if remote:
        argv.extend(["--remote", remote])
    quality_policy = str(getattr(args, "quality_policy", "") or "").strip()
    if quality_policy:
        argv.extend(["--quality-policy", quality_policy])
    if bool(getattr(args, "skip_preflight", False)):
        argv.append("--skip-preflight")
    if bool(getattr(args, "skip_post_push", False)):
        argv.append("--skip-post-push")
    return argv


def push_attempted_command(args: Any) -> str:
    return " ".join(("python3", "dev/scripts/devctl.py", *push_attempted_argv(args)))


__all__ = ["push_attempted_argv", "push_attempted_command"]
