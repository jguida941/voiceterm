"""Commit reference matching helpers for substrate commit checks."""

from __future__ import annotations


def commit_covered(commit_sha: str, covered_commits: tuple[str, ...]) -> bool:
    return any(commit_ref_matches(commit_ref, commit_sha) for commit_ref in covered_commits)


def commit_ref_matches(commit_ref: str, commit_sha: str) -> bool:
    if len(commit_ref) < 7:
        return False
    return commit_sha.startswith(commit_ref) or commit_ref.startswith(commit_sha)
