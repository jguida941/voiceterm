from __future__ import annotations

from dataclasses import replace

from dev.scripts.devctl.runtime.governed_exception_validation import (
    validate_governed_exception_lifecycle,
)
from dev.scripts.devctl.runtime.governed_transition_typechecker import (
    COMMIT_ANCHOR_CLOSURE_EVENT,
    GovernedTransitionErrorCode,
    GovernedTransitionInput,
    check_governed_exception_transition,
)
from dev.scripts.devctl.runtime.raw_git_bypass_lifecycle_closure import (
    RAW_GIT_COMMIT_ANCHOR_STATUS,
    close_raw_git_bypass_lifecycle,
    raw_git_receipt_id_for_lifecycle,
)
from dev.scripts.devctl.runtime.raw_git_bypass_receipts import (
    RawGitBypassAuthority,
    RawGitBypassReceipt,
    RawGitVerb,
    build_raw_git_bypass_receipt,
    build_raw_git_governed_exception_lifecycle,
)


def _receipt(commit_sha: str = "abc123") -> RawGitBypassReceipt:
    return build_raw_git_bypass_receipt(
        git_verb=RawGitVerb.COMMIT,
        executed_at_utc="2026-05-16T18:00:00Z",
        executed_by_actor="codex",
        bypass_authority=RawGitBypassAuthority.OPERATOR_WITNESSED,
        commit_sha=commit_sha,
        operator_quote_evidence_ref="packet:rev_pkt_4239",
        git_args=("-m", "slice"),
    )


def _closed_lifecycle():
    receipt = _receipt()
    lifecycle = build_raw_git_governed_exception_lifecycle(receipt)
    closed, check = close_raw_git_bypass_lifecycle(
        lifecycle,
        receipt=receipt,
        closed_at_utc="2026-05-16T18:10:00Z",
        normal_command="python3 dev/scripts/devctl.py exceptions close-raw-git --backfill",
    )
    assert check.ok is True
    return lifecycle, closed, receipt


def _evidence_for_closed(closed) -> dict[str, object]:
    assert closed.closure_proof is not None
    assert closed.resolution is not None
    refs = tuple(
        dict.fromkeys(
            (
                closed.closure_proof.validation_receipt_id,
                *closed.closure_proof.proof_artifacts,
                f"commit:{closed.resolution.fixed_by_commit}",
                closed.resolution.fixed_by_commit,
            )
        )
    )
    return {
        "refs": refs,
        "commit_shas": (closed.resolution.fixed_by_commit,),
        **{ref: {"kind": "test_evidence"} for ref in refs},
    }


def _check_codes(before, after, *, evidence_index=None) -> set[GovernedTransitionErrorCode]:
    check = check_governed_exception_transition(
        GovernedTransitionInput(
            before=before,
            after=after,
            event_kind=COMMIT_ANCHOR_CLOSURE_EVENT,
            evidence_index=(
                _evidence_for_closed(after) if evidence_index is None else evidence_index
            ),
            closure_proof=after.closure_proof,
        )
    )
    assert check.ok is False
    assert check.assertions_evaluated > 0
    return {error.code for error in check.errors}


def test_raw_git_lifecycle_closes_with_commit_anchor_proof() -> None:
    receipt = _receipt()
    lifecycle = build_raw_git_governed_exception_lifecycle(receipt)

    closed, check = close_raw_git_bypass_lifecycle(
        lifecycle,
        receipt=receipt,
        closed_at_utc="2026-05-16T18:10:00Z",
        normal_command="python3 dev/scripts/devctl.py exceptions close-raw-git --backfill",
    )

    assert check.ok is True
    assert check.assertions_evaluated > 0
    assert closed.status == RAW_GIT_COMMIT_ANCHOR_STATUS
    assert closed.resolution is not None
    assert closed.resolution.fixed_by_commit == receipt.commit_sha
    assert closed.closure_proof is not None
    assert f"commit:{receipt.commit_sha}" in closed.closure_proof.proof_artifacts
    assert raw_git_receipt_id_for_lifecycle(lifecycle) == receipt.receipt_id
    assert validate_governed_exception_lifecycle(closed) == ()


def test_raw_git_lifecycle_rejects_stale_commit_anchor_evidence() -> None:
    receipt = _receipt()
    lifecycle = build_raw_git_governed_exception_lifecycle(receipt)

    closed, check = close_raw_git_bypass_lifecycle(
        lifecycle,
        receipt=receipt,
        closed_at_utc="2026-05-16T18:10:00Z",
        normal_command="python3 dev/scripts/devctl.py exceptions close-raw-git --backfill",
        evidence_index={},
    )

    codes = {error.code for error in check.errors}
    assert closed.status == RAW_GIT_COMMIT_ANCHOR_STATUS
    assert check.ok is False
    assert codes == {
        GovernedTransitionErrorCode.MISSING_COMPOSED_REF,
        GovernedTransitionErrorCode.STALE_COMMIT_ANCHOR,
    }


def test_raw_git_lifecycle_rejects_missing_closure_proof() -> None:
    lifecycle, closed, _receipt = _closed_lifecycle()
    missing_proof = replace(closed, closure_proof=None)

    codes = _check_codes(lifecycle, missing_proof, evidence_index={})

    assert codes == {GovernedTransitionErrorCode.MISSING_CLOSURE_PROOF}


def test_raw_git_lifecycle_rejects_mismatched_lifecycle_id() -> None:
    lifecycle, closed, _receipt = _closed_lifecycle()
    assert closed.closure_proof is not None
    mismatched_proof = replace(
        closed.closure_proof,
        exception_lifecycle_id="gel:some-other-lifecycle",
    )
    mismatched = replace(closed, closure_proof=mismatched_proof)

    codes = _check_codes(lifecycle, mismatched)

    assert codes == {GovernedTransitionErrorCode.MISMATCHED_LIFECYCLE_ID}


def test_raw_git_lifecycle_rejects_illegal_transition() -> None:
    lifecycle, closed, _receipt = _closed_lifecycle()
    classified = replace(lifecycle, status="classified")

    codes = _check_codes(classified, closed)

    assert codes == {GovernedTransitionErrorCode.ILLEGAL_TRANSITION}


def test_raw_git_lifecycle_rejects_unknown_old_status() -> None:
    lifecycle, closed, _receipt = _closed_lifecycle()
    unknown_old = replace(lifecycle, status="not_a_lifecycle_status")

    codes = _check_codes(unknown_old, closed)

    assert codes == {
        GovernedTransitionErrorCode.UNKNOWN_OLD_STATUS,
        GovernedTransitionErrorCode.ILLEGAL_TRANSITION,
    }


def test_raw_git_lifecycle_rejects_unknown_new_status() -> None:
    lifecycle, closed, _receipt = _closed_lifecycle()
    unknown_new = replace(closed, status="not_a_lifecycle_status")

    codes = _check_codes(lifecycle, unknown_new)

    assert codes == {
        GovernedTransitionErrorCode.UNKNOWN_NEW_STATUS,
        GovernedTransitionErrorCode.ILLEGAL_TRANSITION,
    }


def test_raw_git_lifecycle_rejects_already_closed_non_idempotent_move() -> None:
    _lifecycle, closed, _receipt = _closed_lifecycle()
    moved_closed = replace(closed, status="closed_via_bypass_expiry")

    codes = _check_codes(closed, moved_closed)

    assert codes == {
        GovernedTransitionErrorCode.ILLEGAL_TRANSITION,
        GovernedTransitionErrorCode.ALREADY_CLOSED_NON_IDEMPOTENT,
    }
