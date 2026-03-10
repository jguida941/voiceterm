"""Direct repo-identity and risk-context snapshot for the Operator Console repo package.

Complements ``analytics_snapshot.py`` (which provides dashboard-level metrics
via devctl collectors) with the direct git identity, HEAD SHA, active MP scope,
and changed-path risk classification that the future command center, workflow
modes, and CI visibility layers need.

All functions are PyQt-free and safe to call from any thread.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from time import monotonic

_CACHE_TTL_SECONDS = 10.0
_CACHE_LOCK = Lock()
_CACHE: dict[str, tuple[float, "RepoStateSnapshot"]] = {}

# Changed-path risk buckets — order matters for summary roll-up.
_RISK_HIGH_PATTERNS = (
    re.compile(r"^\.github/workflows/"),
    re.compile(r"(^|/)Cargo\.toml$"),
    re.compile(r"(^|/)Cargo\.lock$"),
    re.compile(r"^scripts/"),
    re.compile(r"^release"),
)
_RISK_MEDIUM_PATTERNS = (
    re.compile(r"^rust/src/"),
    re.compile(r"^app/"),
    re.compile(r"^dev/scripts/"),
)
_RISK_LOW_PATTERNS = (
    re.compile(r"\.(md|txt|rst)$"),
    re.compile(r"^dev/active/"),
    re.compile(r"^dev/adr/"),
    re.compile(r"^dev/guides/"),
    re.compile(r"^dev/deferred/"),
)

# Known path categories for display.
_CATEGORY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ci", re.compile(r"^\.github/")),
    ("rust", re.compile(r"^rust/")),
    ("python-app", re.compile(r"^app/")),
    ("python-tooling", re.compile(r"^dev/scripts/")),
    ("docs", re.compile(r"\.(md|txt|rst)$")),
    ("config", re.compile(r"\.(toml|json|ya?ml|lock)$")),
)


@dataclass(frozen=True)
class RepoStateSnapshot:
    """Direct repo-identity and risk-context for the Operator Console."""

    branch: str | None
    head_sha: str | None
    head_short: str | None
    is_dirty: bool
    dirty_file_count: int
    staged_count: int
    unstaged_count: int
    untracked_count: int
    active_mp_scope: str | None
    changed_path_categories: tuple[str, ...]
    risk_summary: str
    collection_note: str | None = None


def build_repo_state(repo_root: Path) -> RepoStateSnapshot:
    """Return a cached repo-state snapshot for the given repo root."""
    cache_key = str(repo_root.resolve())
    now = monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]

    snapshot = _collect_repo_state(repo_root)
    with _CACHE_LOCK:
        _CACHE[cache_key] = (now, snapshot)
    return snapshot


def invalidate_cache() -> None:
    """Clear the repo-state cache so the next call re-collects."""
    with _CACHE_LOCK:
        _CACHE.clear()


def classify_path_risk(path: str) -> str:
    """Return ``'high'``, ``'medium'``, or ``'low'`` for a single path."""
    for pattern in _RISK_HIGH_PATTERNS:
        if pattern.search(path):
            return "high"
    for pattern in _RISK_MEDIUM_PATTERNS:
        if pattern.search(path):
            return "medium"
    for pattern in _RISK_LOW_PATTERNS:
        if pattern.search(path):
            return "low"
    return "medium"


def classify_path_category(path: str) -> str:
    """Return the broad category for a single path."""
    for category, pattern in _CATEGORY_PATTERNS:
        if pattern.search(path):
            return category
    return "other"


def summarize_risk(per_path_risks: list[str]) -> str:
    """Roll up per-path risks into a single summary level."""
    if not per_path_risks:
        return "low"
    if "high" in per_path_risks:
        return "high"
    if "medium" in per_path_risks:
        return "medium"
    return "low"


def _collect_repo_state(repo_root: Path) -> RepoStateSnapshot:
    """Collect repo identity, dirty state, and risk context directly via git."""
    if not repo_root.exists():
        return _unavailable("repo root does not exist")

    try:
        branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
        head_sha = _git(repo_root, "rev-parse", "HEAD")
    except (subprocess.SubprocessError, OSError) as exc:
        return _unavailable(f"git identity failed: {exc}")

    head_short = head_sha[:8] if head_sha else None

    try:
        porcelain = _git(repo_root, "status", "--porcelain")
    except (subprocess.SubprocessError, OSError):
        porcelain = ""

    staged, unstaged, untracked, paths = _parse_porcelain(porcelain)
    dirty_count = staged + unstaged + untracked

    active_mp_scope = _read_active_mp_scope(repo_root)

    per_path_risks = [classify_path_risk(p) for p in paths]
    categories = sorted(set(classify_path_category(p) for p in paths))
    risk = summarize_risk(per_path_risks)

    return RepoStateSnapshot(
        branch=branch or None,
        head_sha=head_sha or None,
        head_short=head_short,
        is_dirty=dirty_count > 0,
        dirty_file_count=dirty_count,
        staged_count=staged,
        unstaged_count=unstaged,
        untracked_count=untracked,
        active_mp_scope=active_mp_scope,
        changed_path_categories=tuple(categories),
        risk_summary=risk,
    )


def _git(repo_root: Path, *args: str) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        raise subprocess.SubprocessError(
            f"git {' '.join(args)} failed (exit {result.returncode}): "
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def _parse_porcelain(porcelain: str) -> tuple[int, int, int, list[str]]:
    """Parse ``git status --porcelain`` output.

    Returns (staged_count, unstaged_count, untracked_count, all_paths).
    """
    staged = 0
    unstaged = 0
    untracked = 0
    paths: list[str] = []

    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        index_char = line[0]
        worktree_char = line[1]
        path = line[3:].strip()

        # Handle renames: "R  old -> new"
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)

        if index_char == "?":
            untracked += 1
        else:
            if index_char not in (" ", "?", "!"):
                staged += 1
            if worktree_char not in (" ", "?", "!"):
                unstaged += 1

    return staged, unstaged, untracked, paths


def _read_active_mp_scope(repo_root: Path) -> str | None:
    """Extract the strategic focus line from MASTER_PLAN.md."""
    mp_path = repo_root / "dev" / "active" / "MASTER_PLAN.md"
    if not mp_path.exists():
        return None
    try:
        text = mp_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    for line in text.splitlines():
        if line.startswith("- Strategic focus:"):
            scope = line.removeprefix("- Strategic focus:").strip()
            return scope if scope else None
    return None


def _unavailable(note: str) -> RepoStateSnapshot:
    return RepoStateSnapshot(
        branch=None,
        head_sha=None,
        head_short=None,
        is_dirty=False,
        dirty_file_count=0,
        staged_count=0,
        unstaged_count=0,
        untracked_count=0,
        active_mp_scope=None,
        changed_path_categories=(),
        risk_summary="unknown",
        collection_note=note,
    )
