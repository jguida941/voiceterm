"""Shared git range helpers for guard commands."""

from __future__ import annotations

from pathlib import Path
import subprocess


def git_commit_range(
    *,
    repo_root: Path,
    base_ref: str,
    head_ref: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return commits in ``base_ref..head_ref`` plus non-fatal warnings."""
    warnings: list[str] = []
    if not git_ref_exists(repo_root, base_ref):
        fallback_ref = _fallback_base_ref(repo_root, head_ref=head_ref)
        if not fallback_ref:
            return (), (f"base_ref_unavailable:{base_ref}",)
        warnings.append(f"base_ref_fallback:{base_ref}->{fallback_ref}")
        base_ref = fallback_ref
    result = subprocess.run(
        ("git", "rev-list", "--reverse", f"{base_ref}..{head_ref}"),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        warning = result.stderr.strip() or result.stdout.strip() or "git_rev_list_failed"
        return (), (warning,)
    commits = tuple(line.strip() for line in result.stdout.splitlines() if line.strip())
    return commits, tuple(warnings)


def git_ref_exists(repo_root: Path, ref: str) -> bool:
    """Return whether ``ref`` resolves in ``repo_root``."""
    result = subprocess.run(
        ("git", "rev-parse", "--verify", ref),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _fallback_base_ref(repo_root: Path, *, head_ref: str) -> str:
    """Resolve a portable branch base when a local upstream is unavailable."""
    for candidate in _fallback_base_ref_candidates(repo_root):
        if git_ref_exists(repo_root, candidate) and _has_merge_base(
            repo_root,
            candidate,
            head_ref,
        ):
            return candidate
    return ""


def _fallback_base_ref_candidates(repo_root: Path) -> tuple[str, ...]:
    candidates: list[str] = []
    origin_head = _git_stdout(
        repo_root,
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
    )
    if origin_head:
        candidates.append(origin_head)
    candidates.extend(("origin/main", "origin/master", "main", "master"))
    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return tuple(deduped)


def _has_merge_base(repo_root: Path, base_ref: str, head_ref: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", base_ref, head_ref),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _git_stdout(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip().splitlines()[0].strip() if result.stdout.strip() else ""
