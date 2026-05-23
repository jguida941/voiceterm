"""Shared git-status line helpers for check guards.

These functions previously lived in three places:

- ``check_contract_consumer_coverage_sweep.py`` (private ``_path_from_git_status_line``)
- ``receipt_schema_validation/git_status.py`` (``path_from_git_status_line`` + ``git_commit_exists``)
- ``receipt_store_consumer/git_status.py`` (``path_from_git_status_line``)

Each copy had byte-identical behavior. Consolidating them here removes the
duplication while keeping the existing leaf modules importing this surface
so downstream callers (and test ``import`` lines) are unchanged.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def path_from_git_status_line(line: str) -> str:
    """Extract the working-tree path from a ``git status --short`` line."""

    if not line.strip() or len(line) < 4:
        return ""
    path_text = line[3:].strip()
    if " -> " in path_text:
        path_text = path_text.split(" -> ", 1)[1].strip()
    return path_text


def git_commit_exists(repo_root: Path, sha: str) -> bool:
    """Return True when ``sha`` resolves to a reachable commit in ``repo_root``."""

    text = sha.strip()
    if not text:
        return False
    result = subprocess.run(
        ("git", "cat-file", "-e", f"{text}^{{commit}}"),
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0
