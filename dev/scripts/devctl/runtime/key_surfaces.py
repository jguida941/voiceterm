"""Shared startup key-surface projection helpers."""

from __future__ import annotations

from pathlib import Path

from .governance_scan import scan_repo_governance_safely
from .project_governance import ProjectGovernance


def startup_key_surfaces(governance: ProjectGovernance | None) -> tuple[str, ...]:
    """Return generated navigation surfaces that bootstrap readers should cite."""
    if governance is None:
        return ()
    surfaces: list[str] = []
    for entry in governance.doc_registry.entries:
        if entry.artifact_role != "connectivity_index":
            continue
        if entry.consumer_scope and entry.consumer_scope != "startup_default":
            continue
        if entry.path and entry.path not in surfaces:
            surfaces.append(entry.path)
    return tuple(surfaces)


def load_startup_key_surfaces(repo_root: Path) -> tuple[str, ...]:
    """Load startup key surfaces from the repo's ProjectGovernance registry."""
    return startup_key_surfaces(scan_repo_governance_safely(repo_root))


__all__ = ["load_startup_key_surfaces", "startup_key_surfaces"]
