"""Small shared helpers for loading ProjectGovernance safely."""

from __future__ import annotations

from pathlib import Path

from .project_governance import ProjectGovernance


def scan_repo_governance_safely(repo_root: Path) -> ProjectGovernance | None:
    """Load ProjectGovernance for a repo and fail closed on scan errors."""
    try:
        from ..governance.draft import scan_repo_governance
    except ImportError:
        return None
    try:
        return scan_repo_governance(repo_root)
    except (OSError, ValueError):
        return None
