"""Receipt update helpers for bypass lifecycle transitions."""

from __future__ import annotations

from .bypass_lifecycle_models import (
    BypassExpirySource,
    BypassLifecycleState,
    BypassReceipt,
)
from .bypass_lifecycle_registry import DEFAULT_BYPASS_REGISTRY


def revoked_bypass_receipt(
    receipt: BypassReceipt | None,
    *,
    expired_at_utc: str,
    reason: str,
    source: BypassExpirySource,
) -> BypassReceipt | None:
    """Return a revoked receipt for operator revocations."""
    if receipt is None or source is not BypassExpirySource.OPERATOR_REVOKE:
        return receipt

    revoked = BypassReceipt(
        receipt_id=receipt.receipt_id,
        reason=receipt.reason,
        operator_signature=receipt.operator_signature,
        ai_approval_evidence=receipt.ai_approval_evidence,
        requested_authority_scope=receipt.requested_authority_scope,
        granted_at_utc=receipt.granted_at_utc,
        granted_by_operator_actor_id=receipt.granted_by_operator_actor_id,
        state=BypassLifecycleState.REVOKED,
        expires_at_utc=receipt.expires_at_utc,
        revoked_at_utc=expired_at_utc,
        revoked_reason=reason,
    )

    DEFAULT_BYPASS_REGISTRY.register_receipt(revoked)
    return revoked


__all__ = ["revoked_bypass_receipt"]
