"""Typed git plumbing helpers for ReviewSnapshot delta computation.

These wrap ``git log`` and ``git show --numstat`` into typed records so the
snapshot builder never touches subprocess directly. The helpers are pure —
they read git only, never mutate state, and return dataclasses so downstream
renderers can consume them without string parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .vcs import run_git_capture


_MP_PATTERN = re.compile(r"\bMP-(\d+)\b", re.IGNORECASE)
_CHECKPOINT_PATTERN = re.compile(r"\bF(\d+[a-z]?)\b")
_COMMIT_FIELD_SEP = "\x1f"
_COMMIT_RECORD_SEP = "\x1e"


@dataclass(frozen=True, slots=True)
class RawCommit:
    """One commit in a range with raw git-log fields (no classification yet)."""

    sha: str = ""
    sha_short: str = ""
    subject: str = ""
    author: str = ""
    timestamp_utc: str = ""
    body: str = ""


@dataclass(frozen=True, slots=True)
class RawFileStat:
    """One file-level change from ``git show --numstat``."""

    path: str = ""
    insertions: int = 0
    deletions: int = 0
    change_kind: str = "modified"


def head_sha(repo_root: Path) -> tuple[str, str]:
    """Return ``(full_sha, short_sha)`` for the current HEAD."""
    code, stdout, _ = run_git_capture(["rev-parse", "HEAD"], repo_root=repo_root)
    if code != 0 or not stdout:
        return "", ""
    full = stdout.strip()
    short = full[:12]
    return full, short


def head_subject(repo_root: Path, sha: str = "HEAD") -> str:
    """Return the subject line for the named commit."""
    code, stdout, _ = run_git_capture(
        ["log", "-1", "--format=%s", sha],
        repo_root=repo_root,
    )
    return stdout.strip() if code == 0 else ""


def head_author_and_time(repo_root: Path, sha: str = "HEAD") -> tuple[str, str]:
    """Return ``(author_name, iso_timestamp_utc)`` for the named commit."""
    code, stdout, _ = run_git_capture(
        ["log", "-1", "--format=%an%x1f%aI", sha],
        repo_root=repo_root,
    )
    if code != 0 or not stdout:
        return "", ""
    parts = stdout.strip().split("\x1f", 1)
    author = parts[0] if parts else ""
    iso = parts[1] if len(parts) > 1 else ""
    return author, iso


def tree_hash(repo_root: Path, sha: str = "HEAD") -> str:
    """Return the tree hash for the named commit."""
    code, stdout, _ = run_git_capture(
        ["rev-parse", f"{sha}^{{tree}}"], repo_root=repo_root
    )
    return stdout.strip() if code == 0 else ""


def current_branch(repo_root: Path) -> str:
    """Return the current branch name or ``""`` if detached."""
    code, stdout, _ = run_git_capture(
        ["rev-parse", "--abbrev-ref", "HEAD"], repo_root=repo_root
    )
    if code != 0:
        return ""
    value = stdout.strip()
    return "" if value == "HEAD" else value


def commits_between(
    repo_root: Path,
    *,
    from_sha: str,
    to_sha: str = "HEAD",
    limit: int = 25,
) -> tuple[RawCommit, ...]:
    """Return the commits reachable from ``to_sha`` but not ``from_sha``.

    When ``from_sha`` is empty, the helper falls back to ``HEAD~25..HEAD`` so
    a first-run snapshot still carries a recent delta.
    """
    rev_range = _resolve_rev_range(repo_root, from_sha=from_sha, to_sha=to_sha)
    if not rev_range:
        return ()
    format_parts = [
        "%H",  # full sha
        "%h",  # short sha
        "%s",  # subject
        "%an",  # author name
        "%aI",  # author ISO timestamp
        "%b",  # body
    ]
    log_format = _COMMIT_FIELD_SEP.join(format_parts) + _COMMIT_RECORD_SEP
    code, stdout, _ = run_git_capture(
        [
            "log",
            f"--max-count={limit}",
            f"--format={log_format}",
            rev_range,
        ],
        repo_root=repo_root,
    )
    if code != 0 or not stdout:
        return ()
    return tuple(_parse_commit_records(stdout))


def file_stats_for_commit(
    repo_root: Path,
    *,
    sha: str,
) -> tuple[RawFileStat, ...]:
    """Return typed file stats for one commit via ``git show --numstat``."""
    code, stdout, _ = run_git_capture(
        ["show", "--numstat", "--format=", sha],
        repo_root=repo_root,
    )
    if code != 0 or not stdout:
        return ()
    return tuple(_parse_numstat_rows(stdout))


def file_stats_between(
    repo_root: Path,
    *,
    from_sha: str,
    to_sha: str = "HEAD",
) -> tuple[RawFileStat, ...]:
    """Return aggregated file stats across all commits in the range."""
    rev_range = _resolve_rev_range(repo_root, from_sha=from_sha, to_sha=to_sha)
    if not rev_range:
        return ()
    code, stdout, _ = run_git_capture(
        ["log", "--numstat", "--format=", rev_range],
        repo_root=repo_root,
    )
    if code != 0 or not stdout:
        return ()
    aggregated: dict[str, list[int]] = {}
    for row in _parse_numstat_rows(stdout):
        bucket = aggregated.setdefault(row.path, [0, 0])
        bucket[0] += row.insertions
        bucket[1] += row.deletions
    return tuple(
        RawFileStat(path=path, insertions=ins, deletions=dels, change_kind="modified")
        for path, (ins, dels) in sorted(aggregated.items())
    )


def extract_mp_refs(text: str) -> tuple[str, ...]:
    """Return MP-NNN references from a commit message or plan excerpt."""
    if not text:
        return ()
    seen: list[str] = []
    for match in _MP_PATTERN.finditer(text):
        mp_id = f"MP-{match.group(1)}"
        if mp_id not in seen:
            seen.append(mp_id)
    return tuple(seen)


def extract_checkpoint_markers(text: str) -> tuple[str, ...]:
    """Return checkpoint markers (F21, F21a, ...) from a commit message."""
    if not text:
        return ()
    seen: list[str] = []
    for match in _CHECKPOINT_PATTERN.finditer(text):
        marker = f"F{match.group(1)}"
        if marker not in seen:
            seen.append(marker)
    return tuple(seen)


def first_body_excerpt(body: str, *, max_lines: int = 6) -> str:
    """Return the first ``max_lines`` non-empty lines of a commit body."""
    if not body:
        return ""
    kept: list[str] = []
    for raw in body.splitlines():
        line = raw.rstrip()
        if line:
            kept.append(line)
            if len(kept) >= max_lines:
                break
    return "\n".join(kept)


def _resolve_rev_range(
    repo_root: Path, *, from_sha: str, to_sha: str
) -> str:
    """Return a git rev-range string, falling back to ``HEAD~25..HEAD``."""
    target = (to_sha or "HEAD").strip()
    base = (from_sha or "").strip()
    if base:
        code, _, _ = run_git_capture(
            ["cat-file", "-e", base], repo_root=repo_root
        )
        if code == 0:
            return f"{base}..{target}"
    return f"{target}~25..{target}" if target else ""


def _parse_commit_records(stdout: str) -> list[RawCommit]:
    records: list[RawCommit] = []
    for block in stdout.split(_COMMIT_RECORD_SEP):
        chunk = block.strip("\n")
        if not chunk:
            continue
        fields = chunk.split(_COMMIT_FIELD_SEP)
        if len(fields) < 6:
            continue
        records.append(
            RawCommit(
                sha=fields[0].strip(),
                sha_short=fields[1].strip(),
                subject=fields[2].strip(),
                author=fields[3].strip(),
                timestamp_utc=fields[4].strip(),
                body=fields[5].strip(),
            )
        )
    return records


def _parse_numstat_rows(stdout: str) -> list[RawFileStat]:
    rows: list[RawFileStat] = []
    for line in stdout.splitlines():
        trimmed = line.strip()
        if not trimmed:
            continue
        parts = trimmed.split("\t")
        if len(parts) < 3:
            continue
        ins_raw, del_raw, path = parts[0], parts[1], parts[2]
        insertions = _coerce_numstat_count(ins_raw)
        deletions = _coerce_numstat_count(del_raw)
        rows.append(
            RawFileStat(
                path=path,
                insertions=insertions,
                deletions=deletions,
                change_kind="modified",
            )
        )
    return rows


def _coerce_numstat_count(value: str) -> int:
    """Return ``int(value)`` or ``0`` for git's ``-`` placeholder for binaries."""
    stripped = value.strip()
    if not stripped or stripped == "-":
        return 0
    try:
        return int(stripped)
    except ValueError:
        return 0


__all__ = [
    "RawCommit",
    "RawFileStat",
    "commits_between",
    "current_branch",
    "extract_checkpoint_markers",
    "extract_mp_refs",
    "file_stats_between",
    "file_stats_for_commit",
    "first_body_excerpt",
    "head_author_and_time",
    "head_sha",
    "head_subject",
    "tree_hash",
]
