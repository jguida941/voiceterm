"""Shared scan-mode helpers for portable quality guard orchestration."""

from __future__ import annotations

from dataclasses import dataclass

ADOPTION_BASE_REF = "__DEVCTL_EMPTY_TREE_BASE__"
WORKTREE_HEAD_REF = "__DEVCTL_WORKTREE_HEAD__"


@dataclass(frozen=True, slots=True)
class ResolvedScanMode:
    """Normalized scan-mode payload used by check/probe orchestration."""

    mode: str
    since_ref: str | None
    head_ref: str


def is_adoption_base_ref(ref: str | None) -> bool:
    """Return whether one ref token means full-repo onboarding scan."""
    return ref == ADOPTION_BASE_REF


def is_worktree_head_ref(ref: str | None) -> bool:
    """Return whether one ref token means worktree-backed current content."""
    return ref == WORKTREE_HEAD_REF


def is_adoption_scan(*, since_ref: str | None, head_ref: str | None = None) -> bool:
    """Return whether the normalized refs represent onboarding/full-scan mode."""
    return is_adoption_base_ref(since_ref)


def resolve_scan_mode(
    *,
    since_ref: str | None,
    head_ref: str = "HEAD",
    adoption_scan: bool = False,
) -> ResolvedScanMode:
    """Resolve the requested check/probe scan mode into effective refs."""
    if adoption_scan and since_ref:
        raise ValueError("--adoption-scan cannot be combined with --since-ref")
    if adoption_scan:
        return ResolvedScanMode(
            mode="adoption-scan",
            since_ref=ADOPTION_BASE_REF,
            head_ref=WORKTREE_HEAD_REF,
        )
    if since_ref:
        return ResolvedScanMode(
            mode="commit-range",
            since_ref=since_ref,
            head_ref=head_ref,
        )
    return ResolvedScanMode(
        mode="working-tree",
        since_ref=None,
        head_ref=head_ref,
    )
