"""Control-plane projection of source cleanliness versus managed drift."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance


def control_plane_worktree_clean(
    *,
    git: dict[str, object],
    governance: "ProjectGovernance | None",
) -> bool:
    """Use typed push enforcement when available; otherwise use raw git."""
    push_enforcement = (
        getattr(governance, "push_enforcement", None)
        if governance is not None
        else None
    )
    if push_enforcement is None:
        return bool(git.get("clean", True))
    return bool(push_enforcement.worktree_clean)


def managed_projection_dirty_paths(
    governance: "ProjectGovernance | None",
) -> tuple[str, ...]:
    """Return compatibility-projection dirt from typed push enforcement."""
    push_enforcement = (
        getattr(governance, "push_enforcement", None)
        if governance is not None
        else None
    )
    if push_enforcement is None:
        return ()
    return tuple(push_enforcement.managed_projection_dirty_paths)
