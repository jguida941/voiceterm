"""Shared git helpers for vcs tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

from dev.scripts.devctl.runtime.vcs import git_command_env


def _run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        env=git_command_env(repo_root),
    )
    return (completed.stdout or "").strip()
