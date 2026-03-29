"""Parent-path helpers for governed-markdown policy scans."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath


def parent_dir(relative_path: str) -> str:
    if not relative_path:
        return ""
    parent = PurePosixPath(relative_path).parent.as_posix()
    return "" if parent == "." else parent


def common_parent_dir(*relative_paths: str) -> str:
    parents = [parent_dir(path) for path in relative_paths if parent_dir(path)]
    if not parents:
        return ""
    common = parents[0]
    for candidate in parents[1:]:
        common = os.path.commonpath([common, candidate])
    return "" if common == "." else common


def policy_dir_root(
    repo_root: Path,
    resolved_policy_path: str | Path | None,
) -> str:
    if not resolved_policy_path:
        return ""
    policy_file = Path(resolved_policy_path)
    if not policy_file.is_absolute():
        policy_file = repo_root / policy_file
    try:
        return policy_file.parent.relative_to(repo_root).as_posix()
    except ValueError:
        return ""


__all__ = ["common_parent_dir", "parent_dir", "policy_dir_root"]
