"""Service identity helpers for bridge-backed review-channel projections."""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

DISCOVERY_FIELDS = (
    "service_id",
    "project_id",
    "repo_root",
    "worktree_root",
    "bridge_path",
    "review_channel_path",
    "status_root",
)

REMOTE_IDENTITY_RE = re.compile(
    r"""^(?:(?:https?|ssh)://)?(?:[^@/]+@)?(?P<host>[^/:]+)(?::|/)(?P<path>.+)$"""
)


@dataclass(frozen=True)
class ServiceIdentity:
    """Repo/worktree-scoped discovery payload for bridge-backed consumers."""

    service_id: str
    project_id: str
    repo_root: str
    worktree_root: str
    bridge_path: str
    review_channel_path: str
    status_root: str
    discovery_fields: tuple[str, ...] = DISCOVERY_FIELDS

    @classmethod
    def from_paths(
        cls,
        *,
        project_id: str,
        resolved_paths: "ResolvedServicePaths",
    ) -> "ServiceIdentity":
        """Build the service identity from one resolved path bundle."""
        return cls(
            service_id=f"review-channel:{project_id}",
            project_id=project_id,
            repo_root=resolved_paths.repo_root,
            worktree_root=resolved_paths.repo_root,
            bridge_path=resolved_paths.bridge_path,
            review_channel_path=resolved_paths.review_channel_path,
            status_root=resolved_paths.status_root,
        )


@dataclass(frozen=True)
class ResolvedServicePaths:
    """Resolved path strings used by the service identity payload."""

    repo_root: str
    bridge_path: str
    review_channel_path: str
    status_root: str

    @classmethod
    def from_inputs(
        cls,
        *,
        repo_root: Path,
        bridge_path: Path,
        review_channel_path: Path,
        output_root: Path,
    ) -> "ResolvedServicePaths":
        """Resolve the filesystem paths exposed through service discovery.

        Paths are stored repo-relative where possible so the identity payload
        is portable across machines and worktrees. ``repo_root`` itself stays
        absolute as the anchor for consumer filesystem access.
        """
        resolved_repo_root = repo_root.resolve()

        return cls(
            repo_root=str(resolved_repo_root),
            bridge_path=_repo_relative(bridge_path, resolved_repo_root),
            review_channel_path=_repo_relative(review_channel_path, resolved_repo_root),
            status_root=_repo_relative(output_root, resolved_repo_root),
        )


def _repo_relative(path: Path, repo_root: Path) -> str:
    """Return a repo-relative string if path is inside repo_root, else absolute."""
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path.resolve())


def project_id_for_repo(repo_root: Path) -> str:
    """Build a portable stable repo/worktree identity hash for one checkout."""
    digest = hashlib.sha256(
        repo_identity_for_repo(repo_root).encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest}"


def repo_identity_for_repo(repo_root: Path) -> str:
    """Return a portable repo identity seed for one checkout.

    Prefers the normalized origin remote URL for stable cross-machine identity.
    Falls back to a collision-resistant hash of the resolved absolute path when
    no remote is configured (local-only or copied repos).
    """
    remote = _origin_remote_url(repo_root)
    if remote:
        normalized_remote = _normalize_remote_identity(remote)
        if normalized_remote:
            return normalized_remote
    # Portable fallback: use the last two path segments for human-readable
    # identity that is stable across machines with the same checkout layout.
    # Two sibling repos with the same directory name under different parents
    # still get distinct identities (e.g. work/myapp vs forks/myapp).
    parts = repo_root.resolve().parts[-2:]
    if parts:
        return f"local:{'/'.join(parts)}"
    return f"local:{repo_root.resolve().name or 'unknown'}"


def _origin_remote_url(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    remote = (result.stdout or "").strip()
    return remote or None


def _normalize_remote_identity(remote: str) -> str | None:
    text = remote.strip()
    if not text:
        return None
    text = text.removesuffix(".git")
    match = REMOTE_IDENTITY_RE.match(text)
    if match is not None:
        host = match.group("host").strip()
        path = match.group("path").strip("/")
        if host and path:
            return f"{host}/{path}"
    if "/" in text and " " not in text:
        return text
    return None


def build_service_identity(
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    output_root: Path,
) -> dict[str, object]:
    """Build the repo/worktree-scoped service identity for bridge consumers."""
    resolved_paths = ResolvedServicePaths.from_inputs(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=output_root,
    )

    project_id = project_id_for_repo(repo_root)
    identity = ServiceIdentity.from_paths(
        project_id=project_id,
        resolved_paths=resolved_paths,
    )

    return asdict(identity)
