from __future__ import annotations

from dev.scripts.devctl.runtime.governed_exception_validation import (
    validate_governed_exception_lifecycle,
)
from dev.scripts.devctl.runtime.governed_transition_typechecker import (
    GovernedTransitionErrorCode,
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
    assert GovernedTransitionErrorCode.MISSING_COMPOSED_REF in codes
    assert GovernedTransitionErrorCode.STALE_COMMIT_ANCHOR in codes
