"""Refresh/freshness helpers for live review-state consumers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..repo_packs import active_path_config, active_path_config_is_overridden
from ..repo_packs.review_cache import projection_dependency_paths

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance


def refresh_bridge_backed_review_state_payload(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None",
    review_status_dir: Path | None = None,
) -> dict[str, object] | None:
    """Refresh and load the typed review-state payload from live bridge inputs."""
    bridge_path = _governed_existing_path(
        repo_root,
        governance=governance,
        relative_path=(
            str(governance.bridge_config.bridge_path or "").strip()
            if governance is not None
            else ""
        ),
    )
    review_channel_path = _governed_existing_path(
        repo_root,
        governance=governance,
        relative_path=(
            str(governance.bridge_config.review_channel_path or "").strip()
            if governance is not None
            else ""
        ),
    )
    output_root = review_status_output_root(
        repo_root,
        governance=governance,
        review_status_dir=review_status_dir,
    )
    if bridge_path is None or review_channel_path is None or output_root is None:
        return None
    try:
        from ..review_channel.state import refresh_status_snapshot
    except ImportError:
        return None
    try:
        snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=output_root,
        )
    except (OSError, ValueError):
        return None
    return _load_payload_from_path(Path(snapshot.projection_paths.review_state_path))


def review_status_output_root(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None",
    review_status_dir: Path | None = None,
) -> Path | None:
    """Return the review-status output root for the current authority path."""
    if review_status_dir is not None:
        return (
            review_status_dir
            if review_status_dir.is_absolute()
            else (repo_root / review_status_dir)
        )
    if governance is not None:
        review_root = str(governance.artifact_roots.review_root or "").strip()
        if review_root:
            return repo_root / review_root
    if active_path_config_is_overridden():
        return repo_root / active_path_config().review_status_dir_rel
    return None


def projection_freshness_paths(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None",
) -> tuple[Path, ...]:
    """Return source paths that invalidate a cached review-state projection."""
    bridge_path = _governed_existing_path(
        repo_root,
        governance=governance,
        relative_path=(
            str(governance.bridge_config.bridge_path or "").strip()
            if governance is not None
            else ""
        ),
    )
    review_channel_path = _governed_existing_path(
        repo_root,
        governance=governance,
        relative_path=(
            str(governance.bridge_config.review_channel_path or "").strip()
            if governance is not None
            else ""
        ),
    )
    if bridge_path is None or review_channel_path is None:
        return ()
    return projection_dependency_paths(
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
    )


def _governed_existing_path(
    repo_root: Path,
    *,
    governance: "ProjectGovernance | None",
    relative_path: str,
) -> Path | None:
    if governance is None:
        return None
    candidate = relative_path.strip()
    if not candidate:
        return None
    path = repo_root / candidate
    return path if path.is_file() else None


def _load_payload_from_path(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dict(payload) if isinstance(payload, dict) else None
