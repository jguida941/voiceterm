"""Tests for typed lifetime bypass receipts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

UTC = timezone.utc

from dev.scripts.devctl.runtime.governed_exception_validation import (
    validate_governed_exception_lifecycle,
)
from dev.scripts.devctl.runtime.governed_transitions import TransitionStateViolation
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BYPASS_EXCEPTION_CLASS,
    BypassAuthorityScope,
    BypassEvaluationDecision,
    BypassEvaluationInput,
    BypassExpirySource,
    BypassLifecycleState,
    BypassRequest,
    BypassReceipt,
    active_bypass_lifecycle_for_receipt_id,
    bypass_lifecycle_active,
    bypass_receipt_active,
    bypass_receipt_from_mapping,
    evaluate_bypass_request,
    expire_bypass_lifecycle,
    grant_lifetime_bypass,
    is_bypass_active,
    load_bypass_lifecycles_with_errors,
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


def _request(**overrides: object) -> BypassRequest:
    values = {
        "request_id": "mp377-priority-1",
        "scope": BypassAuthorityScope.EDIT_ONLY,
        "reason": "Operator requested scoped BypassLifecycle repair.",
        "actor": "operator",
        "requested_at_utc": "2026-05-12T16:09:27Z",
        "target_role": "implementer",
        "target_session_id": "session-1",
        "target_surface": "review-channel-launch",
        "evidence_refs": ("packet:rev_pkt_3847",),
    }
    values.update(overrides)
    return BypassRequest(**values)


def _evaluation_input(**overrides: object) -> BypassEvaluationInput:
    values = {
        "operator_signature": "operator",
        "ai_approval_evidence": "packet:rev_pkt_3847",
        "evaluated_at_utc": "2026-05-12T16:10:00Z",
    }
    values.update(overrides)
    return BypassEvaluationInput(**values)


def test_bypass_request_round_trips_from_mapping() -> None:
    request = _request()
    parsed = BypassRequest.from_mapping(request.to_dict())

    assert parsed == request
    assert parsed.scope is BypassAuthorityScope.EDIT_ONLY
    assert parsed.state is BypassLifecycleState.REQUESTED
    assert parsed.target_surface == "review-channel-launch"


def test_bypass_receipt_round_trips_from_mapping() -> None:
    receipt = _receipt(expires_at_utc="2030-01-01T00:00:00Z")
    parsed = bypass_receipt_from_mapping(receipt.to_dict())

    assert parsed == receipt
    assert parsed.requested_authority_scope is BypassAuthorityScope.EDIT_ONLY
    assert parsed.state is BypassLifecycleState.RECEIPT_ISSUED


def test_bypass_request_runtime_enforcement_rejects_non_requested_state() -> None:
    with pytest.raises(
        TransitionStateViolation,
        match="bypass.evaluate_request pre_state",
    ):
        evaluate_bypass_request(
            _request(state=BypassLifecycleState.DENIED),
            _evaluation_input(),
        )


def test_bypass_receipt_runtime_enforcement_rejects_non_issued_state() -> None:
    with pytest.raises(
        TransitionStateViolation,
        match="bypass.grant_lifetime_bypass pre_state",
    ):
        grant_lifetime_bypass(_receipt(state=BypassLifecycleState.EXPIRED))


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


def test_bypass_lifecycle_evaluation_issues_governed_exception_receipt() -> None:
    request = _request()

    lifecycle = evaluate_bypass_request(
        request,
        _evaluation_input(
            evaluator_actor_id="codex",
            expires_at_utc="2030-05-12T17:10:00Z",
        ),
    )

    assert lifecycle.contract_id == "BypassLifecycle"
    assert lifecycle.state is BypassLifecycleState.ACTIVE
    assert lifecycle.evaluation.decision is BypassEvaluationDecision.APPROVED
    assert lifecycle.receipt is not None
    assert lifecycle.receipt.receipt_id == "bypass:mp377-priority-1"
    assert lifecycle.governed_exception is not None
    assert (
        lifecycle.evaluation.governed_exception_lifecycle_id
        == lifecycle.governed_exception.lifecycle_id
    )
    assert lifecycle.governed_exception.exception is not None
    assert lifecycle.governed_exception.exception.exception_class == BYPASS_EXCEPTION_CLASS
    assert "GovernedExceptionLifecycle" in lifecycle.evaluation.policy_evidence_refs
    assert validate_governed_exception_lifecycle(lifecycle.governed_exception) == ()
    assert is_bypass_active(lifecycle.receipt.receipt_id, BypassAuthorityScope.EDIT_ONLY)


def test_bypass_lifecycle_denies_request_without_operator_evidence() -> None:
    lifecycle = evaluate_bypass_request(
        _request(),
        _evaluation_input(operator_signature=""),
    )

    assert lifecycle.state is BypassLifecycleState.DENIED
    assert lifecycle.evaluation.decision is BypassEvaluationDecision.DENIED
    assert lifecycle.evaluation.reason == "operator_signature_required"
    assert lifecycle.receipt is None
    assert lifecycle.governed_exception is None


def test_bypass_lifecycle_expiry_rejects_inactive_lifecycle() -> None:
    lifecycle = evaluate_bypass_request(
        _request(request_id="mp377-denied-expiry"),
        _evaluation_input(operator_signature=""),
    )

    with pytest.raises(TransitionStateViolation, match="bypass.expire_lifecycle"):
        expire_bypass_lifecycle(
            lifecycle,
            expired_at_utc="2026-05-12T16:23:00Z",
            reason="cannot expire denied lifecycle",
            source=BypassExpirySource.STOP_ANCHOR,
        )


def test_bypass_lifecycle_expiry_records_stop_anchor_event() -> None:
    lifecycle = evaluate_bypass_request(
        _request(),
        _evaluation_input(),
    )

    expired = expire_bypass_lifecycle(
        lifecycle,
        expired_at_utc="2026-05-12T16:23:00Z",
        reason="rev_pkt_3846 stop_anchor honored",
        source=BypassExpirySource.STOP_ANCHOR,
        evidence_refs=("packet:rev_pkt_3846",),
    )

    assert expired.state is BypassLifecycleState.EXPIRED
    assert expired.expiry is not None
    assert expired.expiry.source is BypassExpirySource.STOP_ANCHOR
    assert expired.expiry.evidence_refs == ("packet:rev_pkt_3846",)
    assert expired.receipt == lifecycle.receipt


def test_bypass_lifecycle_revoke_updates_registered_receipt() -> None:
    lifecycle = evaluate_bypass_request(
        _request(request_id="mp377-revoke"),
        _evaluation_input(),
    )
    assert lifecycle.receipt is not None

    revoked = expire_bypass_lifecycle(
        lifecycle,
        expired_at_utc="2026-05-12T16:20:00Z",
        reason="operator revoked",
        source=BypassExpirySource.OPERATOR_REVOKE,
    )

    assert revoked.state is BypassLifecycleState.REVOKED
    assert revoked.receipt is not None
    assert revoked.receipt.state is BypassLifecycleState.REVOKED
    assert revoked.receipt.revoked_at_utc == "2026-05-12T16:20:00Z"
    assert not is_bypass_active(
        revoked.receipt.receipt_id, BypassAuthorityScope.EDIT_ONLY
    )


def test_active_bypass_lifecycle_loads_from_jsonl_store(tmp_path: Path) -> None:
    lifecycle = evaluate_bypass_request(
        _request(request_id="mp377-store", target_role="implementer"),
        _evaluation_input(),
    )
    assert lifecycle.receipt is not None
    store = tmp_path / "bypass_lifecycles.jsonl"
    store.write_text(json.dumps(lifecycle.to_dict()) + "\n", encoding="utf-8")

    loaded = load_bypass_lifecycles_with_errors(store)
    active = active_bypass_lifecycle_for_receipt_id(
        lifecycle.receipt.receipt_id,
        store_path=store,
        target_role="implementer",
    )

    assert loaded.errors == ()
    assert active is not None
    assert active.lifecycle_id == lifecycle.lifecycle_id
    assert bypass_lifecycle_active(active)
