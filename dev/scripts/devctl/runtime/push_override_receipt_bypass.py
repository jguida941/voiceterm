"""BypassLifecycle lookup helpers for push override receipts."""

from __future__ import annotations

from pathlib import Path

from .bypass_lifecycle_models import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    BypassLifecycle,
)
from .bypass_lifecycle_registry import active_bypass_lifecycles


def active_push_override_bypass_lifecycles(
    repo_root: Path,
) -> tuple[BypassLifecycle, ...]:
    """Return active lifecycle rows that can authorize override publication."""
    store_path = repo_root / DEFAULT_BYPASS_LIFECYCLE_STORE_REL
    if not store_path.exists():
        return ()
    return active_bypass_lifecycles(
        store_path=store_path,
        required_scope=BypassAuthorityScope.EDIT_COMMIT_AND_PUSH,
    )


def matching_active_push_override_bypass_lifecycle(
    *,
    bypass_lifecycle_id: str,
    bypass_receipt_id: str,
    active_lifecycles: tuple[BypassLifecycle, ...],
) -> BypassLifecycle | None:
    """Find the active lifecycle named by a PushOverrideReceipt."""
    if not bypass_lifecycle_id or not bypass_receipt_id:
        return None
    for lifecycle in reversed(active_lifecycles):
        if lifecycle.lifecycle_id != bypass_lifecycle_id:
            continue
        lifecycle_receipt = lifecycle.receipt
        if lifecycle_receipt is None:
            continue
        if lifecycle_receipt.receipt_id != bypass_receipt_id:
            continue
        return lifecycle
    return None


__all__ = [
    "active_push_override_bypass_lifecycles",
    "matching_active_push_override_bypass_lifecycle",
]
