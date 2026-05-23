"""Git-status helpers for the receipt-store consumer guard.

The generic ``path_from_git_status_line`` helper was extracted to
``dev/scripts/checks/_git_status_helpers.py`` (shared with the
``receipt_schema_validation`` and ``check_contract_consumer_coverage_sweep``
guards). It is re-exported here so the leaf module's public API stays
backward compatible.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

try:
    from .._git_status_helpers import path_from_git_status_line
except ImportError:  # pragma: no cover - direct-script fallback
    from _git_status_helpers import path_from_git_status_line  # type: ignore[no-redef]

__all__ = ["git_changed_paths", "path_from_git_status_line"]


def git_changed_paths(repo_root: Path, warnings: list[str]) -> tuple[Path, ...]:
    result = subprocess.run(
        ("git", "status", "--short", "--untracked-files=all", "--", "dev/state", "dev/reports"),
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
