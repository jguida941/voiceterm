"""Low-level path helpers for managed receipt commits."""

from __future__ import annotations

from pathlib import Path

from ..config import REPO_ROOT
from ..governance.repo_policy import load_repo_governance_section


def tracked_render_surface_relpaths(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> tuple[str, ...]:
    """Return tracked, non-local repo-pack render-surface paths."""
    try:
        section, _, _ = load_repo_governance_section(
            "surface_generation",
            repo_root=repo_root,
            policy_path=policy_path,
        )
    except (OSError, ValueError):
        return ()
    surfaces = section.get("surfaces")
    if not isinstance(surfaces, list):
        return ()
    paths = [
        str(entry.get("output_path") or "").strip()
        for entry in surfaces
        if isinstance(entry, dict)
        and bool(entry.get("tracked", False))
        and not bool(entry.get("local_only", False))
    ]
    return tuple(dict.fromkeys(path for path in paths if path))


__all__ = ["tracked_render_surface_relpaths"]
