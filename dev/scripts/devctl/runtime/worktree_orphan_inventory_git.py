"""Public git probe seam for worktree-orphan inventory scans."""

from __future__ import annotations

from .worktree_orphan_inventory_git_checkout import CheckoutProbe, probe_checkout
from .worktree_orphan_inventory_git_refs import branch_exists
from .worktree_orphan_inventory_git_siblings import (
    looks_like_git_checkout,
    same_parent_candidates,
)

__all__ = [
    "CheckoutProbe",
    "branch_exists",
    "looks_like_git_checkout",
    "probe_checkout",
    "same_parent_candidates",
]
