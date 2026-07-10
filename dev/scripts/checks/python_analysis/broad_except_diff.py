"""Diff helpers for the Python broad-except guard."""

from __future__ import annotations

import re
from pathlib import Path

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


def parse_added_line_numbers(diff_text: str) -> set[int]:
    added_lines: set[int] = set()
    for line in diff_text.splitlines():
        match = HUNK_RE.match(line)
        if match is None:
            continue
        start = int(match.group("start"))
        count = int(match.group("count") or "1")
        if count <= 0:
            continue
        added_lines.update(range(start, start + count))
    return added_lines


def diff_added_lines(
    *,
    guard,
    repo_root: Path,
    path: Path,
    since_ref: str | None,
    head_ref: str,
    is_adoption_scan_fn,
) -> set[int]:
    if is_adoption_scan_fn(since_ref=since_ref, head_ref=head_ref):
        lines = guard.read_text_from_worktree(
            path if path.is_absolute() else repo_root / path
        )
        if lines is None:
            return set()
        return set(range(1, len(lines.splitlines()) + 1))
    relative = (
        path.relative_to(repo_root).as_posix() if path.is_absolute() else path.as_posix()
    )
    if since_ref:
        cmd = ["git", "diff", "--unified=0", since_ref, head_ref, "--", relative]
    else:
        cmd = ["git", "diff", "--unified=0", "HEAD", "--", relative]
    result = guard.run_git(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"failed to diff {relative}")
    return parse_added_line_numbers(result.stdout)
