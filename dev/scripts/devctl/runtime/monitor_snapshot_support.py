"""Support helpers for monitor snapshot construction."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from .control_plane_sources import artifact_paths
from .monitor_snapshot_contracts import MonitorSourceLabel

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .review_state_models import ReviewState


def load_monitor_review_state(
    *,
    repo_root: Path,
    governance: "ProjectGovernance | None",
    review_state: "ReviewState | None",
    review_status_dir: Path | None,
):
    """Resolve the typed review-state authority for one monitor snapshot."""
    if review_state is not None:
        return review_state
    from .review_state_locator import load_current_review_state

    return load_current_review_state(
        repo_root,
        governance=governance,
        review_status_dir=review_status_dir,
        prefer_cached_projection=False,
    )


def count_dirty_files(repo_root: Path) -> int:
    """Count dirty git status lines for worktree monitoring."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(repo_root),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 0
    return sum(1 for line in result.stdout.splitlines() if line.strip())


def build_monitor_source_labels(
    *,
    repo_root: Path,
    review_status_dir: Path | None,
) -> list[MonitorSourceLabel]:
    """Classify authority, telemetry, projection, and diagnostic inputs."""
    paths = artifact_paths(repo_root, review_status_dir=review_status_dir)
    source_defs = (
        ("receipt", "authority", paths["receipt"]),
        ("review_state", "authority", paths["review_state"]),
        ("publisher_heartbeat", "telemetry", paths["publisher_hb"]),
        ("reviewer_supervisor_heartbeat", "telemetry", paths["supervisor_hb"]),
        ("compact_projection", "projection", paths["compact_json"]),
        ("full_projection", "projection", paths["full_json"]),
        ("git_status", "diagnostic", repo_root / ".git"),
    )
    return [
        MonitorSourceLabel(
            source_id=source_id,
            classification=classification,
            path=str(path),
            present=path.exists(),
        )
        for source_id, classification, path in source_defs
    ]


def monitor_output_root(*, repo_root: Path, review_status_dir: Path | None) -> Path:
    """Resolve where the latest monitor bundle should be written."""
    if review_status_dir is not None:
        return review_status_dir if review_status_dir.is_absolute() else repo_root / review_status_dir
    return artifact_paths(repo_root)["review_state"].parent
