"""Git status readers for governed push."""

from __future__ import annotations

from pathlib import Path

from ...collect import collect_git_status
from ...config import REPO_ROOT
from ...runtime.vcs import run_git_capture


def collect_git_status_for_repo(
    repo_root: Path,
    *,
    default_collect_fn=collect_git_status,
) -> dict[str, object]:
    """Return branch and dirty-state info for one repo root."""
    if repo_root == REPO_ROOT:
        return default_collect_fn()

    branch_code, branch, branch_error = run_git_capture(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        repo_root=repo_root,
    )
    if branch_code != 0:
        message = branch_error or f"git rev-parse exited with code {branch_code}"
        return {"error": message}

    status_code, status_output, status_error = run_git_capture(
        ["status", "--porcelain", "--untracked-files=all"],
        repo_root=repo_root,
    )
    if status_code != 0:
        message = status_error or f"git status exited with code {status_code}"
        return {"error": message}

    changes: list[dict[str, str]] = []
    for line in status_output.splitlines():
        if not line:
            continue
        parts = line.split(maxsplit=1)
        status = parts[0].strip()
        path = parts[1] if len(parts) == 2 else ""
        if "->" in path:
            path = path.split("->")[-1].strip()
        changes.append(dict(status=status, path=path))
    return dict(branch=branch, changes=changes)
