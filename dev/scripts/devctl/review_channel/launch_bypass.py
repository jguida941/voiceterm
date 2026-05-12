"""Bypass lifecycle resolution for review-channel launches."""

from __future__ import annotations

from ..runtime.lifetime_bypass_mode import (
    DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
    BypassAuthorityScope,
    active_bypass_lifecycle_for_receipt_id,
)
from .launch_records import LaunchSessionRequest


def resolve_launch_bypass_lifecycle(
    *,
    request: LaunchSessionRequest,
    resolved_approval_mode: str,
) -> object | None:
    if request.bypass_lifecycle is not None:
        return request.bypass_lifecycle
    if resolved_approval_mode != "trusted":
        return None
    if not request.bypass_receipt_id:
        return None
    return active_bypass_lifecycle_for_receipt_id(
        request.bypass_receipt_id,
        store_path=request.repo_root / DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        required_scope=BypassAuthorityScope.EDIT_ONLY,
    )


__all__ = ["resolve_launch_bypass_lifecycle"]
