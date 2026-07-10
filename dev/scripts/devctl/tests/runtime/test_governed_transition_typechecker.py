from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

from dev.scripts.devctl.runtime.governed_exception_lifecycle import (
    GovernedExceptionLifecycle,
)
from dev.scripts.devctl.runtime.governed_exception_receipts import (
    ClosureProof,
    ResolutionReceipt,
)
from dev.scripts.devctl.runtime.governed_transition_typechecker import (
    BYPASS_EXPIRY_EVENT,
    COMMIT_ANCHOR_CLOSURE_EVENT,
    ACK_TAGGED_RESOLUTION_EVENT,
    GovernedTransitionCheck,
    GovernedTransitionErrorCode,
    GovernedTransitionInput,
    check_governed_exception_transition,
)

UTC = timezone.utc
LIFECYCLE_ID = "gel:bypass:bypass:mp378:typechecker"


def _before(**overrides: object) -> GovernedExceptionLifecycle:
    return GovernedExceptionLifecycle(
        lifecycle_id=_text(overrides, "lifecycle_id", LIFECYCLE_ID),
        status=_text(overrides, "status", "operator_approved"),
        created_at_utc=_text(
            overrides,
            "created_at_utc",
            "2026-05-16T12:00:00Z",
        ),
        updated_at_utc=_text(
            overrides,
            "updated_at_utc",
            "2026-05-16T12:00:00Z",
        ),
    )


def _after(**overrides: object) -> GovernedExceptionLifecycle:
    closure = _closure_proof()
    resolution = _resolution_receipt(closure_proof_id=closure.closure_proof_id)
    resolution_value = _optional_resolution(
        overrides.get("resolution", resolution),
    )
    closure_value = _optional_closure(overrides.get("closure_proof", closure))
    return GovernedExceptionLifecycle(
        lifecycle_id=_text(overrides, "lifecycle_id", LIFECYCLE_ID),
        status=_text(overrides, "status", "closed"),
        resolution=resolution_value,
        closure_proof=closure_value,
        resolution_receipt_id=_text(
            overrides,
            "resolution_receipt_id",
            resolution.resolution_id,
        ),
        created_at_utc=_text(
            overrides,
            "created_at_utc",
            "2026-05-16T12:00:00Z",
        ),
        updated_at_utc=_text(
            overrides,
            "updated_at_utc",
            "2026-05-16T12:05:00Z",
        ),
    )


def _closure_proof(**overrides: object) -> ClosureProof:
    return ClosureProof(
        closure_proof_id=_text(
            overrides,
            "closure_proof_id",
            "closure-proof:mp378:typechecker",
        ),
        exception_lifecycle_id=_text(
            overrides,
            "exception_lifecycle_id",
            LIFECYCLE_ID,
        ),
        normal_command=_text(
            overrides,
            "normal_command",
            "python3 dev/scripts/devctl.py test-python --suite devctl",
        ),
        validation_receipt_id=_text(
            overrides,
            "validation_receipt_id",
            "validation_receipt:mp378:typechecker",
        ),
        proof_artifacts=_string_tuple(
            overrides.get(
                "proof_artifacts",
                ("commit:abc123", "commit_receipt:mp378:typechecker"),
            )
        ),
    )


def _resolution_receipt(**overrides: object) -> ResolutionReceipt:
    return ResolutionReceipt(
        resolution_id=_text(overrides, "resolution_id", "resolution:mp378:typechecker"),
        exception_lifecycle_id=_text(
            overrides,
            "exception_lifecycle_id",
            LIFECYCLE_ID,
        ),
        finding_id=_text(overrides, "finding_id", "finding:mp378:typechecker"),
        status=_text(overrides, "status", "closed"),
        root_cause_class=_text(overrides, "root_cause_class", "test_fixture"),
        root_cause_summary=_text(overrides, "root_cause_summary", "fixture resolution"),
        fixed_by_commit=_text(overrides, "fixed_by_commit", "abc123"),
        validation_receipt_id=_text(
            overrides,
            "validation_receipt_id",
            "validation_receipt:mp378:typechecker",
        ),
        closure_proof_id=_text(
            overrides,
            "closure_proof_id",
            "closure-proof:mp378:typechecker",
        ),
        closed_at_utc=_text(overrides, "closed_at_utc", "2026-05-16T12:05:00Z"),
    )


def _evidence_index() -> dict[str, object]:
    return {
        "validation_receipt:mp378:typechecker": {},
        "commit:abc123": {},
        "commit_receipt:mp378:typechecker": {},
    }


def _assert_nontrivial(check: GovernedTransitionCheck) -> None:
    assert check.inputs_scanned > 0
    assert check.assertions_evaluated > 0


def _codes(check: GovernedTransitionCheck) -> set[GovernedTransitionErrorCode]:
    return {error.code for error in check.errors}


def _check(**overrides: object) -> GovernedTransitionCheck:
    return check_governed_exception_transition(
        GovernedTransitionInput(
            before=overrides.get("before", _before()),
            after=overrides.get("after", _after()),
            event_kind=_text(overrides, "event_kind", COMMIT_ANCHOR_CLOSURE_EVENT),
            evidence_index=_optional_evidence_index(
                overrides.get("evidence_index", _evidence_index())
            ),
            closure_proof=overrides.get("closure_proof"),
            bypass_lifecycle=overrides.get("bypass_lifecycle"),
            bypass_expiry=overrides.get("bypass_expiry"),
            now_utc=_optional_datetime(overrides.get("now_utc")),
        )
    )


def _text(values: Mapping[str, object], name: str, default: str) -> str:
    return str(values.get(name, default)).strip()


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        return ()
    return tuple(str(item) for item in value)


def _optional_closure(value: object) -> ClosureProof | None:
    if value is None or isinstance(value, ClosureProof):
        return value
    raise AssertionError(f"expected ClosureProof or None, got {type(value).__name__}")


def _optional_resolution(value: object) -> ResolutionReceipt | None:
    if value is None or isinstance(value, ResolutionReceipt):
        return value
    raise AssertionError(f"expected ResolutionReceipt or None, got {type(value).__name__}")


def _optional_evidence_index(value: object) -> Mapping[str, object] | None:
    if value is None or isinstance(value, Mapping):
        return value
    raise AssertionError(f"expected evidence mapping or None, got {type(value).__name__}")


def _optional_datetime(value: object) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    raise AssertionError(f"expected datetime or None, got {type(value).__name__}")


def test_valid_operator_approved_to_closed_via_commit_anchor_transition_passes() -> None:
    check = _check()

    _assert_nontrivial(check)
    assert check.ok is True
    assert check.errors == ()


def test_unknown_old_status_returns_typed_error() -> None:
    check = _check(
        before=_before(status="banana"),
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.UNKNOWN_OLD_STATUS in _codes(check)


def test_unknown_new_status_returns_typed_error() -> None:
    check = _check(
        after=_after(status="random_state_not_in_legal_set"),
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.UNKNOWN_NEW_STATUS in _codes(check)


def test_illegal_transition_operator_approved_to_resolved_for_commit_event() -> None:
    check = _check(
        before=_before(status="operator_approved"),
        after=_after(status="resolved"),
        event_kind=COMMIT_ANCHOR_CLOSURE_EVENT,
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.ILLEGAL_TRANSITION in _codes(check)
    assert check.illegal_transitions[0].new_status == "resolved"


def test_missing_closure_proof_when_closing() -> None:
    check = _check(
        after=_after(closure_proof=None),
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.MISSING_CLOSURE_PROOF in _codes(check)


def test_missing_resolution_when_closing() -> None:
    check = _check(
        after=_after(resolution=None, resolution_receipt_id=""),
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.MISSING_RESOLUTION in _codes(check)


def test_missing_composed_ref_returns_typed_error() -> None:
    closure = _closure_proof(
        validation_receipt_id="validation_receipt:missing",
        proof_artifacts=("commit:abc123", "commit_receipt:missing"),
    )
    check = _check(
        after=_after(closure_proof=closure),
        evidence_index={"commit:abc123": {}},
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.MISSING_COMPOSED_REF in _codes(check)
    assert "validation_receipt:missing" in check.missing_refs
    assert "commit_receipt:missing" in check.missing_refs


def test_mismatched_lifecycle_id_returns_typed_error() -> None:
    closure = _closure_proof(exception_lifecycle_id="gel:bypass:bypass:different")
    check = _check(
        after=_after(closure_proof=closure),
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.MISMATCHED_LIFECYCLE_ID in _codes(check)


def test_stale_commit_anchor_returns_typed_error() -> None:
    fake_sha = "deadbeef00000000000000000000000000000000"
    closure = _closure_proof(proof_artifacts=(f"commit:{fake_sha}",))
    check = _check(
        after=_after(closure_proof=closure),
        evidence_index={"validation_receipt:mp378:typechecker": {}},
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.STALE_COMMIT_ANCHOR in _codes(check)
    assert check.stale_proofs[0].ref == fake_sha


def test_bypass_not_expired_returns_typed_error() -> None:
    now_utc = datetime(2026, 5, 16, 12, 5, tzinfo=UTC)
    check = _check(
        event_kind=BYPASS_EXPIRY_EVENT,
        bypass_lifecycle={
            "state": "bypass_active",
            "governed_exception": {"lifecycle_id": LIFECYCLE_ID},
        },
        bypass_expiry={
            "expires_at_utc": (now_utc + timedelta(days=1)).isoformat(),
        },
        now_utc=now_utc,
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.BYPASS_NOT_EXPIRED in _codes(check)


def test_bypass_not_linked_to_exception_returns_typed_error() -> None:
    check = _check(
        event_kind=BYPASS_EXPIRY_EVENT,
        bypass_lifecycle={
            "state": "bypass_expired",
            "governed_exception": {"lifecycle_id": "gel:bypass:bypass:different"},
        },
        bypass_expiry={"expired_at_utc": "2026-05-16T12:05:00Z"},
        now_utc=datetime(2026, 5, 16, 12, 5, tzinfo=UTC),
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.BYPASS_NOT_LINKED_TO_EXCEPTION in _codes(check)


def test_already_closed_non_idempotent_returns_typed_error() -> None:
    check = _check(
        before=_before(status="closed"),
        after=_after(status="resolved"),
        event_kind=ACK_TAGGED_RESOLUTION_EVENT,
    )

    _assert_nontrivial(check)
    assert check.ok is False
    assert GovernedTransitionErrorCode.ALREADY_CLOSED_NON_IDEMPOTENT in _codes(check)
