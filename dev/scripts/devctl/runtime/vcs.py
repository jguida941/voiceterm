"""Shared git/vcs helpers used by repo-owned command surfaces."""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..config import REPO_ROOT

INDEX_LOCK_RETRY_DELAYS = (0.1, 0.2, 0.4, 0.8)
_INDEX_WRITING_GIT_COMMANDS = {
    "add",
    "checkout",
    "commit",
    "mv",
    "reset",
    "restore",
    "rm",
    "stash",
    "write-tree",
}

def git_command_env(
    repo_root: Path,
    *,
    extra_env: Mapping[str, str] | None = None,
) -> dict[str, str] | None:
    """Return git env overrides for repo-owned nested git commands."""
    del repo_root
    if not extra_env:
        return None

    env = os.environ.copy()
    env.update(extra_env)
    return env


def run_git_capture(
    args: Sequence[str],
    *,
    repo_root: Path = REPO_ROOT,
    extra_env: Mapping[str, str] | None = None,
) -> tuple[int, str, str]:
    """Run a git command and return ``(returncode, stdout, stderr)``."""
    attempts = 1 + (len(INDEX_LOCK_RETRY_DELAYS) if _uses_git_index(args) else 0)
    last_result: tuple[int, str, str] = (127, "", "git command did not run")
    for attempt in range(attempts):
        last_result = _run_git_capture_once(
            args,
            repo_root=repo_root,
            extra_env=extra_env,
        )
        code, _stdout, stderr = last_result
        if code == 0 or not git_index_lock_busy(stderr):
            return last_result
        if attempt < len(INDEX_LOCK_RETRY_DELAYS):
            time.sleep(INDEX_LOCK_RETRY_DELAYS[attempt])
    return last_result


def _run_git_capture_once(
    args: Sequence[str],
    *,
    repo_root: Path = REPO_ROOT,
    extra_env: Mapping[str, str] | None = None,
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
            env=git_command_env(repo_root, extra_env=extra_env),
        )
    except OSError as exc:
        return 127, "", str(exc)
    return (
        completed.returncode,
        (completed.stdout or "").strip(),
        (completed.stderr or "").strip(),
    )


def _uses_git_index(args: Sequence[str]) -> bool:
    command = next((str(part).strip() for part in args if str(part).strip()), "")
    return command in _INDEX_WRITING_GIT_COMMANDS


def git_index_write_blocked(stderr: str) -> bool:
    text = str(stderr or "")
    return "index.lock" in text and "Operation not permitted" in text


def git_index_lock_busy(stderr: str) -> bool:
    text = str(stderr or "")
    if "index.lock" not in text:
        return False
    if git_index_write_blocked(text):
        return False
    return (
        "File exists" in text
        or "Another git process" in text
        or "Unable to create" in text
    )


def classify_git_index_error(stderr: str, *, default: str) -> str:
    if git_index_write_blocked(stderr):
        return "git_index_write_blocked"
    if git_index_lock_busy(stderr):
        return "git_index_lock_busy"
    return default


def remote_exists(remote: str, *, repo_root: Path = REPO_ROOT) -> bool:
    """Return ``True`` when a named remote is configured locally."""
    code, _, _ = run_git_capture(["remote", "get-url", remote], repo_root=repo_root)
    return code == 0


def branch_exists(branch: str, *, repo_root: Path = REPO_ROOT) -> bool:
    """Return ``True`` when a local branch exists."""
    code, _, _ = run_git_capture(
        ["rev-parse", "--verify", "--quiet", branch],
        repo_root=repo_root,
    )
    return code == 0


def remote_branch_exists(
    remote: str,
    branch: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> bool:
    """Return ``True`` when ``refs/remotes/<remote>/<branch>`` exists."""
    code, _, _ = run_git_capture(
        ["show-ref", "--verify", "--quiet", f"refs/remotes/{remote}/{branch}"],
        repo_root=repo_root,
    )
    return code == 0


def branch_divergence(
    remote: str,
    branch: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, int | str | None]:
    """Return ahead/behind counts for ``branch`` against ``remote/branch``."""
    code, output, error = run_git_capture(
        ["rev-list", "--left-right", "--count", f"{remote}/{branch}...{branch}"],
        repo_root=repo_root,
    )
    if code != 0:
        message = error or output or f"git rev-list exited with code {code}"
        return {"behind": None, "ahead": None, "error": message}

    parts = output.split()
    if len(parts) != 2:
        return {
            "behind": None,
            "ahead": None,
            "error": f"Unexpected divergence output: {output!r}",
        }

    try:
        behind = int(parts[0])
        ahead = int(parts[1])
    except ValueError:
        return {
            "behind": None,
            "ahead": None,
            "error": f"Unable to parse divergence output: {output!r}",
        }
    return {"behind": behind, "ahead": ahead, "error": None}
