"""Tests for typed lifetime bypass receipts."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from dev.scripts.devctl.runtime.governed_exception_validation import (
    validate_governed_exception_lifecycle,
)
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BYPASS_EXCEPTION_CLASS,
    BypassAuthorityScope,
    BypassReceipt,
    bypass_receipt_active,
    bypass_receipt_from_mapping,
    grant_lifetime_bypass,
    is_bypass_active,
)


def _receipt(**overrides: object) -> BypassReceipt:
    values = {
        "receipt_id": "bypass:mp377:test",
        "reason": (
            "Operator authorized a scoped bypass while typed governance "
            "contracts are being repaired."
        ),
        "operator_signature": "operator",
        "ai_approval_evidence": "rev_pkt_3689",
        "requested_authority_scope": BypassAuthorityScope.EDIT_ONLY,
        "granted_at_utc": "2026-05-11T19:00:00Z",
        "granted_by_operator_actor_id": "operator",
    }
    values.update(overrides)
    return BypassReceipt(**values)


def test_bypass_receipt_round_trips_from_mapping() -> None:
    receipt = _receipt(expires_at_utc="2030-01-01T00:00:00Z")
    parsed = bypass_receipt_from_mapping(receipt.to_dict())

    assert parsed == receipt
    assert parsed.requested_authority_scope is BypassAuthorityScope.EDIT_ONLY


def test_bypass_receipt_rejects_unknown_scope() -> None:
    payload = _receipt().to_dict()
    payload["requested_authority_scope"] = "raw_shell"

    with pytest.raises(ValueError, match="unknown_bypass_authority_scope"):
        bypass_receipt_from_mapping(payload)


def test_scope_enforcement_requires_requested_scope_or_wider() -> None:
    receipt = _receipt(requested_authority_scope=BypassAuthorityScope.EDIT_ONLY)
    grant_lifetime_bypass(receipt)

    assert is_bypass_active(receipt.receipt_id, BypassAuthorityScope.EDIT_ONLY)
    assert is_bypass_active(receipt.receipt_id, BypassAuthorityScope.AGENT_SPAWN_ONLY)
    assert not is_bypass_active(
        receipt.receipt_id, BypassAuthorityScope.EDIT_AND_COMMIT
    )


def test_commit_and_push_scope_grants_lower_scopes() -> None:
    receipt = _receipt(
        receipt_id="bypass:mp377:push",
        requested_authority_scope=BypassAuthorityScope.EDIT_COMMIT_AND_PUSH,
    )
    grant_lifetime_bypass(receipt)

    assert is_bypass_active(receipt.receipt_id, BypassAuthorityScope.AGENT_SPAWN_ONLY)
    assert is_bypass_active(receipt.receipt_id, BypassAuthorityScope.EDIT_ONLY)
    assert is_bypass_active(receipt.receipt_id, BypassAuthorityScope.EDIT_AND_COMMIT)
    assert is_bypass_active(
        receipt.receipt_id, BypassAuthorityScope.EDIT_COMMIT_AND_PUSH
    )


def test_lifetime_receipt_has_no_expiry() -> None:
    receipt = _receipt()

    assert bypass_receipt_active(
        receipt,
        now_utc=datetime(2099, 1, 1, tzinfo=UTC),
    )


def test_time_bound_receipt_expires_fail_closed() -> None:
    receipt = _receipt(expires_at_utc="2026-05-11T20:00:00Z")

    assert bypass_receipt_active(
        receipt,
        now_utc=datetime(2026, 5, 11, 19, 30, tzinfo=UTC),
    )
    assert not bypass_receipt_active(
        receipt,
        now_utc=datetime(2026, 5, 11, 20, 0, tzinfo=UTC),
    )


def test_revoked_receipt_is_inactive() -> None:
    receipt = _receipt(revoked_at_utc="2026-05-11T19:30:00Z")
    grant_lifetime_bypass(receipt)

    assert not is_bypass_active(receipt.receipt_id, BypassAuthorityScope.EDIT_ONLY)


def test_lifetime_bypass_composes_with_governed_exception_lifecycle() -> None:
    receipt = _receipt()

    lifecycle = grant_lifetime_bypass(receipt)

    assert lifecycle.lifecycle_id == "gel:bypass:bypass:mp377:test"
    assert lifecycle.exception is not None
    assert lifecycle.exception.exception_class == BYPASS_EXCEPTION_CLASS
    assert lifecycle.exception.action_kind == "runtime.mutate"
    assert f"bypass_receipt:{receipt.receipt_id}" in lifecycle.authority_evidence_refs
    assert validate_governed_exception_lifecycle(lifecycle) == ()
