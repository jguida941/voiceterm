"""Service identity helpers for bridge-backed review-channel projections."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .core import project_id_for_repo

DISCOVERY_FIELDS = (
    "service_id",
    "project_id",
    "repo_root",
    "worktree_root",
    "bridge_path",
    "review_channel_path",
    "status_root",
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
        """Resolve the filesystem paths exposed through service discovery."""
        resolved_repo_root = repo_root.resolve()

        return cls(
            repo_root=str(resolved_repo_root),
            bridge_path=str(bridge_path.resolve()),
            review_channel_path=str(review_channel_path.resolve()),
            status_root=str(output_root.resolve()),
        )


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
