"""Git checkout identity probes for orphan inventory scans."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from .worktree_orphan_inventory_git_common import (
    checkout_fingerprint,
    git_output,
    repo_identity,
)
from .worktree_orphan_inventory_git_refs import unpublished_commits
from .worktree_orphan_inventory_git_status import status_paths


class CheckoutProbe(NamedTuple):
    """Internal checkout probe result used by the inventory scanner."""

    path: Path
    git_dir: str
    origin_url: str
    branch: str
    head_sha: str
    repo_identity: str
    checkout_fingerprint: str
    dirty_paths: tuple[str, ...] = ()
    untracked_paths: tuple[str, ...] = ()
    unpublished_commit_shas: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class CheckoutIdentity(NamedTuple):
    """Git identity values for one checkout."""

    git_dir: str
    origin_url: str
    branch: str
    head_sha: str


def probe_checkout(path: Path) -> CheckoutProbe:
    """Read checkout identity, status, and unpublished commit state."""
    identity = checkout_identity(path)
    dirty_paths, untracked_paths = status_paths(path)

    return CheckoutProbe(
        path=path.resolve(strict=False),
        git_dir=identity.git_dir,
        origin_url=identity.origin_url,
        branch=normalized_branch(identity.branch),
        head_sha=identity.head_sha,
        repo_identity=repo_identity(identity.origin_url or str(path)),
        checkout_fingerprint=checkout_fingerprint(path),
        dirty_paths=dirty_paths,
        untracked_paths=untracked_paths,
        unpublished_commit_shas=unpublished_commits(path, branch=identity.branch),
        errors=checkout_errors(path, identity),
    )


def checkout_identity(path: Path) -> CheckoutIdentity:
    return CheckoutIdentity(
        git_dir=git_output(path, ["rev-parse", "--git-dir"]),
        origin_url=git_output(path, ["remote", "get-url", "origin"]),
        branch=git_output(path, ["rev-parse", "--abbrev-ref", "HEAD"]),
        head_sha=git_output(path, ["rev-parse", "HEAD"]),
    )


def normalized_branch(branch: str) -> str:
    return "" if branch == "HEAD" else branch


def checkout_errors(path: Path, identity: CheckoutIdentity) -> tuple[str, ...]:
    if identity.head_sha:
        return ()

    return (f"unable to resolve HEAD for {path}",)


__all__ = ["CheckoutProbe", "probe_checkout"]
