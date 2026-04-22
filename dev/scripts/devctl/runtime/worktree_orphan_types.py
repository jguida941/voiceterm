"""Shared constants/helpers for worktree-orphan contract modules."""

from __future__ import annotations

ORPHAN_SOURCE_KINDS = (
    "current_checkout",
    "registered_git_worktree",
    "planned_delegated_worker_worktree",
    "unregistered_sibling_clone",
    "deep_scan_repo",
    "prunable_or_missing_worktree",
    "stash_orphan",
    "worker_root_orphan",
    "prunable_ci_worktree_orphan",
    "latent_state_orphan",
)

ORPHAN_RECONCILIATION_ACTIONS = (
    "adopt_and_commit",
    "adopt_and_stash",
    "export_patch",
    "ignore_with_receipt",
    "prune_missing_unreferenced",
    "archive_after_user_approval",
    "materialize_as_worker",
)

CHECKOUT_INVENTORY_STATES = (
    "managed",
    "unmanaged_shadow",
    "archived_unattested",
)

WORK_PUBLICATION_EVENT_KINDS = (
    "commit_recorded",
    "push_pending",
    "published",
    "archived",
)

ACCEPT_ALL_ORPHAN_SCOPES = ("worktree", "global")


def enum_value(value: str, *, allowed: tuple[str, ...], default: str) -> str:
    """Return value when allowed, else a deterministic default."""
    return value if value in allowed else default


__all__ = [
    "ACCEPT_ALL_ORPHAN_SCOPES",
    "CHECKOUT_INVENTORY_STATES",
    "ORPHAN_RECONCILIATION_ACTIONS",
    "ORPHAN_SOURCE_KINDS",
    "WORK_PUBLICATION_EVENT_KINDS",
    "enum_value",
]
