"""Git-status helpers scoped to the feature-proof receipt directory.

Generic ``path_from_git_status_line`` and ``git_commit_exists`` helpers were
extracted to ``dev/scripts/checks/_git_status_helpers.py`` to remove
multi-module duplication. They are re-exported here so existing callers stay
intact while the scope-specific ``git_changed_paths`` body remains the only
behavior owned by this leaf module.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

try:
    from .._git_status_helpers import git_commit_exists, path_from_git_status_line
except ImportError:  # pragma: no cover - direct-script fallback
    from _git_status_helpers import (  # type: ignore[no-redef]
        git_commit_exists,
        path_from_git_status_line,
    )

__all__ = ["git_changed_paths", "git_commit_exists", "path_from_git_status_line"]


def git_changed_paths(repo_root: Path, warnings: list[str]) -> tuple[Path, ...]:
    result = subprocess.run(
        (
            "git",
            "status",
            "--short",
            "--untracked-files=all",
            "--",
            "dev/reports/feature_proof_receipts",
        ),
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        warnings.append(f"git status failed: {result.stderr.strip()}")
        return ()
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        path_text = path_from_git_status_line(line)
        if path_text:
            paths.append(Path(path_text))
    return tuple(paths)
