"""Operator Console adapter for the shared DashboardSnapshot contract."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.runtime.dashboard_snapshot_authority import (
    build_dashboard_snapshot,
)


def load_dashboard_snapshot(
    warnings: list[str],
    repo_root: Path,
) -> dict[str, object] | None:
    """Load the shared DashboardSnapshot v3 contract for desktop panels."""
    try:
        return build_dashboard_snapshot(
            repo_root=repo_root,
            view="overview",
            role="dashboard",
        )
    except (OSError, ValueError) as exc:
        warnings.append(f"Could not load DashboardSnapshot v3: {exc}")
        return None


__all__ = ["load_dashboard_snapshot"]
