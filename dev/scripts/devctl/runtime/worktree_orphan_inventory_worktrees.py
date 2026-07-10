"""Git worktree-list parsing for orphan inventory scans."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple

from .value_coercion import coerce_string
from .vcs import run_git_capture


class WorktreeRecord(NamedTuple):
    """Internal git-worktree-list row."""

    path: Path
    head_sha: str = ""
    branch: str = ""
    prunable: bool = False
    bare: bool = False
    detached: bool = False
    reason: str = ""


def git_worktree_records(repo_root: Path) -> tuple[WorktreeRecord, ...]:
    """Parse `git worktree list --porcelain` into typed internal rows."""
    code, output, _ = run_git_capture(
        ["worktree", "list", "--porcelain"],
        repo_root=repo_root,
    )
    if code != 0 or not output:
        return ()

    records: list[WorktreeRecord] = []
    current: dict[str, object] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            _append_record(records, current)
            current = {}
            continue
        _apply_worktree_line(current, line)

    _append_record(records, current)
    return tuple(records)


def is_temp_path(path: Path) -> bool:
    text = str(path.resolve(strict=False))
    return text.startswith("/tmp/") or text.startswith("/private/tmp/")


def _append_record(
    records: list[WorktreeRecord],
    current: Mapping[str, object],
) -> None:
    record = worktree_record_from_mapping(current)
    if record is not None:
        records.append(record)


def _apply_worktree_line(current: dict[str, object], line: str) -> None:
    key, _, value = line.partition(" ")
    if key in {"bare", "detached", "prunable"}:
        current[key] = True
        if key == "prunable" and value:
            current["reason"] = value
        return
    current[key] = value


def worktree_record_from_mapping(
    value: Mapping[str, object],
) -> WorktreeRecord | None:
    path = coerce_string(value.get("worktree"))
    if not path:
        return None

    branch = coerce_string(value.get("branch"))
    if branch.startswith("refs/heads/"):
        branch = branch.removeprefix("refs/heads/")

    return WorktreeRecord(
        path=Path(path).expanduser(),
        head_sha=coerce_string(value.get("HEAD")),
        branch=branch,
        prunable=bool(value.get("prunable")),
        bare=bool(value.get("bare")),
        detached=bool(value.get("detached")),
        reason=coerce_string(value.get("reason")),
    )


__all__ = ["WorktreeRecord", "git_worktree_records", "is_temp_path"]
