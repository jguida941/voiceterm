"""HMAC binding for push override receipts."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import replace

from .bypass_lifecycle_models import BypassLifecycle
from .remote_commit_pipeline_models import PushAuthorizationRecord

PUSH_OVERRIDE_RECEIPT_HMAC_CONTRACT_ID = "PushOverrideReceiptHMACContract"


def push_override_receipt_authorization_with_reason(
    authorization: PushAuthorizationRecord,
    *,
    override_reason: str,
) -> PushAuthorizationRecord:
    """Return an authorization whose override reason matches the receipt body."""
    if authorization.override_reason == override_reason:
        return authorization
    return replace(authorization, override_reason=override_reason)


def push_override_receipt_hmac_signature(
    *,
    authorization: PushAuthorizationRecord,
    override_id: str,
    bypass_lifecycle: BypassLifecycle,
) -> str:
    """Return the canonical PushOverrideReceipt HMAC hex digest."""
    receipt = bypass_lifecycle.receipt
    receipt_id = receipt.receipt_id if receipt is not None else ""
    receipt_scope = receipt.requested_authority_scope.value if receipt else ""
    granted_at_utc = receipt.granted_at_utc if receipt is not None else ""
    granted_by = receipt.granted_by_operator_actor_id if receipt is not None else ""
    payload = "\n".join(
        (
            "contract=PushOverrideReceipt",
            f"hmac_contract={PUSH_OVERRIDE_RECEIPT_HMAC_CONTRACT_ID}",
            f"override_id={override_id}",
            f"bypass_lifecycle_id={bypass_lifecycle.lifecycle_id}",
            f"bypass_receipt_id={receipt_id}",
            f"bypass_scope={receipt_scope}",
            f"bypass_granted_at_utc={granted_at_utc}",
            f"bypass_granted_by={granted_by}",
            f"authorized_head_sha={authorization.authorized_head_sha}",
            f"approval_mode={authorization.approval_mode}",
            f"review_verdict={authorization.review_verdict}",
            f"approved_by={authorization.approved_by}",
            f"approved_at_utc={authorization.approved_at_utc}",
            f"pipeline_id={authorization.pipeline_id}",
            f"generation_id={authorization.generation_id}",
            f"decision_packet_id={authorization.decision_packet_id}",
            f"request_packet_id={authorization.request_packet_id}",
            "override_reason_sha256="
            + hashlib.sha256(
                authorization.override_reason.strip().encode("utf-8")
            ).hexdigest(),
        )
    )
    key = push_override_receipt_hmac_key(bypass_lifecycle)
    return hmac.new(
        key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def push_override_receipt_signature_matches(
    *,
    authorization: PushAuthorizationRecord,
    override_id: str,
    signature: str,
    bypass_lifecycle: BypassLifecycle,
) -> bool:
    expected = "sha256:" + push_override_receipt_hmac_signature(
        authorization=authorization,
        override_id=override_id,
        bypass_lifecycle=bypass_lifecycle,
    )
    return hmac.compare_digest(signature, expected)


def push_override_receipt_hmac_key(bypass_lifecycle: BypassLifecycle) -> str:
    """Derive the receipt key from active typed bypass lifecycle authority."""
    receipt = bypass_lifecycle.receipt
    return "\n".join(
        value
        for value in (
            bypass_lifecycle.lifecycle_id,
            bypass_lifecycle.request.request_id,
            bypass_lifecycle.evaluation.evaluation_id,
            receipt.receipt_id if receipt is not None else "",
            receipt.operator_signature if receipt is not None else "",
            receipt.ai_approval_evidence if receipt is not None else "",
            receipt.reason if receipt is not None else "",
            receipt.granted_at_utc if receipt is not None else "",
        )
        if value
    )


__all__ = [
    "PUSH_OVERRIDE_RECEIPT_HMAC_CONTRACT_ID",
    "push_override_receipt_authorization_with_reason",
    "push_override_receipt_hmac_key",
    "push_override_receipt_hmac_signature",
    "push_override_receipt_signature_matches",
]
