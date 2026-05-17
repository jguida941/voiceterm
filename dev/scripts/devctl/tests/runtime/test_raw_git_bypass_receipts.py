import json
from pathlib import Path

import pytest

from dev.scripts.devctl.runtime.bypass_lifecycle_models import (
    BypassAuthorityScope,
    BypassEvaluation,
    BypassEvaluationDecision,
    BypassLifecycle,
    BypassLifecycleState,
    BypassReceipt,
    BypassRequest,
)
from dev.scripts.devctl.runtime.governed_exception_store import (
    load_governed_exception_lifecycles,
)
from dev.scripts.devctl.runtime.raw_git_bypass_receipts import (
    RawGitBypassAuthority,
    RawGitBypassReceipt,
    RawGitVerb,
    append_raw_git_bypass_receipt,
    build_raw_git_bypass_receipt,
    raw_git_authority_from_value,
    read_raw_git_bypass_receipts,
)


def test_raw_git_bypass_receipt_round_trips_from_mapping() -> None:
    receipt = build_raw_git_bypass_receipt(
        git_verb=RawGitVerb.COMMIT,
        executed_at_utc="2026-05-14T16:30:00Z",
        executed_by_actor="codex",
        bypass_authority=RawGitBypassAuthority.OPERATOR_WITNESSED,
        commit_sha="abc123",
        affected_paths=("dev/scripts/devctl.py",),
        operator_quote_evidence_ref="packet:rev_pkt_4022",
        skipped_pre_hooks=("pre-commit", "commit-msg"),
        git_args=("--no-verify", "-m", "test"),
    )

    parsed = RawGitBypassReceipt.from_mapping(receipt.to_dict())

    assert parsed == receipt
    assert parsed.contract_id == "RawGitBypassReceipt"
    assert parsed.receipt_id.startswith("raw-git:commit:")


def test_raw_git_bypass_receipt_store_appends_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "dev/state/raw_git_bypass_receipts.jsonl"
    receipt = build_raw_git_bypass_receipt(
        git_verb=RawGitVerb.PUSH,
        executed_at_utc="2026-05-14T16:31:00Z",
        executed_by_actor="codex",
        bypass_authority=RawGitBypassAuthority.OPERATOR_WITNESSED,
        push_range=("base", "head"),
        bypass_lifecycle_id="",
        git_args=("--no-verify",),
    )

    result = append_raw_git_bypass_receipt(path, receipt)

    assert result.record_count == 1
    stored = read_raw_git_bypass_receipts(path)
    assert stored == (result.receipt,)
    assert stored[0].governed_exception_id.startswith("gel:raw-git:push:")
    exception_rows = load_governed_exception_lifecycles(
        tmp_path / "dev/state/governed_exception_lifecycles.jsonl"
    )
    assert exception_rows[0].lifecycle_id == stored[0].governed_exception_id
    assert exception_rows[0].exception is not None
    assert exception_rows[0].exception.action_kind == "vcs.push"


def test_raw_git_bypass_authority_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="unknown_raw_git_bypass_authority"):
        raw_git_authority_from_value("verbal_only")


def test_lifecycle_backed_raw_git_receipt_rejects_fabricated_lifecycle_id(
    tmp_path: Path,
) -> None:
    receipt = build_raw_git_bypass_receipt(
        git_verb=RawGitVerb.COMMIT,
        executed_at_utc="2026-05-14T16:32:00Z",
        executed_by_actor="codex",
        bypass_authority=RawGitBypassAuthority.BYPASS_LIFECYCLE_RECEIPT,
        bypass_lifecycle_id="bypass:fabricated",
        commit_sha="abc123",
        git_args=("--no-verify", "-m", "test"),
    )

    with pytest.raises(ValueError, match="bypass_lifecycle_id not active"):
        append_raw_git_bypass_receipt(
            tmp_path / "dev/state/raw_git_bypass_receipts.jsonl",
            receipt,
            bypass_lifecycle_store_path=tmp_path / "dev/state/bypass_lifecycles.jsonl",
        )


def test_lifecycle_backed_raw_git_receipt_rejects_expired_lifecycle(
    tmp_path: Path,
) -> None:
    lifecycle = _bypass_lifecycle(expires_at_utc="2000-01-01T00:00:00Z")
    lifecycle_path = tmp_path / "dev/state/bypass_lifecycles.jsonl"
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_path.write_text(
        f"{json.dumps(lifecycle.to_dict(), sort_keys=True)}\n",
        encoding="utf-8",
    )
    receipt = build_raw_git_bypass_receipt(
        git_verb=RawGitVerb.COMMIT,
        executed_at_utc="2026-05-14T16:33:00Z",
        executed_by_actor="codex",
        bypass_authority=RawGitBypassAuthority.BYPASS_LIFECYCLE_RECEIPT,
        bypass_lifecycle_id="bypass:active",
        commit_sha="abc123",
        git_args=("--no-verify", "-m", "test"),
    )

    with pytest.raises(ValueError, match="bypass_lifecycle_id not active"):
        append_raw_git_bypass_receipt(
            tmp_path / "dev/state/raw_git_bypass_receipts.jsonl",
            receipt,
            bypass_lifecycle_store_path=lifecycle_path,
        )


def _bypass_lifecycle(*, expires_at_utc: str = "") -> BypassLifecycle:
    request = BypassRequest(
        request_id="active",
        scope=BypassAuthorityScope.EDIT_AND_COMMIT,
        reason="Operator approved lifecycle-backed raw git commit for test coverage.",
        actor="operator",
        requested_at_utc="2026-05-14T16:30:00Z",
    )
    receipt = BypassReceipt(
        receipt_id="bypass:active",
        reason=request.reason,
        operator_signature="operator",
        ai_approval_evidence="packet:test",
        requested_authority_scope=BypassAuthorityScope.EDIT_AND_COMMIT,
        granted_at_utc="2026-05-14T16:30:01Z",
        granted_by_operator_actor_id="operator",
        expires_at_utc=expires_at_utc,
    )
    return BypassLifecycle(
        lifecycle_id="bypass:active",
        state=BypassLifecycleState.ACTIVE,
        request=request,
        evaluation=BypassEvaluation(
            evaluation_id="bypass-eval:active",
            request_id=request.request_id,
            decision=BypassEvaluationDecision.APPROVED,
            evaluated_at_utc="2026-05-14T16:30:01Z",
            evaluator_actor_id="operator",
            reason="operator_approved_bypass_request",
            approved_scope=BypassAuthorityScope.EDIT_AND_COMMIT,
        ),
        receipt=receipt,
    )
