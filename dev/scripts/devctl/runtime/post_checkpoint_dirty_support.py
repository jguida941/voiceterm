"""Shared helpers for post-checkpoint dirty-worktree authority."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

COMMIT_CHECKPOINT_COMMAND = (
    'python3 dev/scripts/devctl.py commit -m "<descriptive message>"'
)

if TYPE_CHECKING:
    from .project_governance_push import PushEnforcement


def requires_commit_before_push(
    push: "PushEnforcement | Mapping[str, object]",
) -> bool:
    """Return True when a local checkpoint exists and the worktree is dirty again."""
    ahead = _push_value(push, "ahead_of_upstream_commits")
    return (
        bool(_push_value(push, "worktree_dirty"))
        and isinstance(ahead, int)
        and ahead > 0
        and str(_push_value(push, "recommended_action") or "").strip()
        == "commit_before_push"
    )


def _push_value(
    push: "PushEnforcement | Mapping[str, object]",
    field: str,
) -> object:
    if isinstance(push, Mapping):
        return push.get(field)
    return getattr(push, field, None)


__all__ = ["COMMIT_CHECKPOINT_COMMAND", "requires_commit_before_push"]
