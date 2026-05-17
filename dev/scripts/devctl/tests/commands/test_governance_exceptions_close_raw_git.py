from __future__ import annotations

import json
from pathlib import Path

import pytest

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.governance import close_raw_git_exceptions
from dev.scripts.devctl.commands.governance import exceptions
from dev.scripts.devctl.runtime.governed_exception_store import (
    load_governed_exception_lifecycles,
)
from dev.scripts.devctl.runtime.governed_transition_typechecker import (
    GovernedTransitionCheck,
    GovernedTransitionError,
    GovernedTransitionErrorCode,
)
from dev.scripts.devctl.runtime.raw_git_bypass_lifecycle_closure import (
    RAW_GIT_COMMIT_ANCHOR_STATUS,
)
from dev.scripts.devctl.runtime.raw_git_bypass_receipts import (
    RawGitBypassAuthority,
    RawGitBypassReceipt,
    RawGitVerb,
    build_raw_git_bypass_receipt,
    build_raw_git_governed_exception_lifecycle,
)

R297_CLOSE_RAW_GIT_CLI_NEGATIVE_CODES = (
    GovernedTransitionErrorCode.STALE_COMMIT_ANCHOR,
    GovernedTransitionErrorCode.MISSING_CLOSURE_PROOF,
    GovernedTransitionErrorCode.MISMATCHED_LIFECYCLE_ID,
    GovernedTransitionErrorCode.ILLEGAL_TRANSITION,
    GovernedTransitionErrorCode.UNKNOWN_OLD_STATUS,
    GovernedTransitionErrorCode.ALREADY_CLOSED_NON_IDEMPOTENT,
    GovernedTransitionErrorCode.BYPASS_NOT_EXPIRED,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded_rows = [json.dumps(row, sort_keys=True) for row in rows]
    newline = "\n" if encoded_rows else ""
    path.write_text("\n".join(encoded_rows) + newline, encoding="utf-8")


def _receipt(commit_sha: str, *, suffix: str) -> RawGitBypassReceipt:
    return build_raw_git_bypass_receipt(
        git_verb=RawGitVerb.COMMIT,
        executed_at_utc=f"2026-05-16T18:0{suffix}:00Z",
        executed_by_actor="codex",
        bypass_authority=RawGitBypassAuthority.OPERATOR_WITNESSED,
        commit_sha=commit_sha,
        operator_quote_evidence_ref="packet:rev_pkt_4239",
        git_args=("-m", f"slice-{suffix}"),
    )


def _run_close_raw_git(
    tmp_path: Path,
    capsys,
    *,
    receipt: RawGitBypassReceipt | None = None,
) -> tuple[int, dict[str, object], Path]:
    lifecycle_store = tmp_path / "governed_exception_lifecycles.jsonl"
    receipt_store = tmp_path / "raw_git_bypass_receipts.jsonl"
    selected_receipt = receipt or _receipt("abc123", suffix="1")
    lifecycle = build_raw_git_governed_exception_lifecycle(selected_receipt)
    _write_jsonl(receipt_store, [selected_receipt.to_dict()])
    _write_jsonl(lifecycle_store, [lifecycle.to_dict()])
    parser = build_parser()
    args = parser.parse_args(
        [
            "exceptions",
            "close-raw-git",
            "--store-path",
            str(lifecycle_store),
            "--receipt-store-path",
            str(receipt_store),
            "--format",
            "json",
        ]
    )

    rc = exceptions.run(args)

    return rc, json.loads(capsys.readouterr().out), lifecycle_store


def _install_transition_failure(
    monkeypatch: pytest.MonkeyPatch,
    expected_code: GovernedTransitionErrorCode,
) -> None:
    def fail_transition(lifecycle, **_kwargs):
        error = GovernedTransitionError(
            code=expected_code,
            message=f"{expected_code.value} fixture",
            lifecycle_id=lifecycle.lifecycle_id,
        )
        check = GovernedTransitionCheck(
            ok=False,
            errors=(error,),
            missing_refs=(),
            illegal_transitions=(),
            stale_proofs=(),
            inputs_scanned=2,
            assertions_evaluated=1,
        )
        return lifecycle, check

    monkeypatch.setattr(
        close_raw_git_exceptions,
        "close_raw_git_bypass_lifecycle",
        fail_transition,
    )


def _assert_cli_propagates_transition_code(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    *,
    expected_code: GovernedTransitionErrorCode,
) -> None:
    _install_transition_failure(monkeypatch, expected_code)

    rc, payload, lifecycle_store = _run_close_raw_git(tmp_path, capsys)

    assert rc == 1
    assert payload["ok"] is False
    assert payload["closed_count"] == 0
    assert payload["skipped_count"] == 1
    assert payload["errors"][0]["code"] == expected_code.value
    skipped = payload["skipped_lifecycles"][0]
    assert skipped["reason"] == "transition_failed"
    assert skipped["errors"][0]["code"] == expected_code.value
    rows = load_governed_exception_lifecycles(lifecycle_store)
    assert rows[0].status == "operator_approved"


def test_exceptions_close_raw_git_negative_path_code_set_matches_r297_scope() -> None:
    assert R297_CLOSE_RAW_GIT_CLI_NEGATIVE_CODES == (
        GovernedTransitionErrorCode.STALE_COMMIT_ANCHOR,
        GovernedTransitionErrorCode.MISSING_CLOSURE_PROOF,
        GovernedTransitionErrorCode.MISMATCHED_LIFECYCLE_ID,
        GovernedTransitionErrorCode.ILLEGAL_TRANSITION,
        GovernedTransitionErrorCode.UNKNOWN_OLD_STATUS,
        GovernedTransitionErrorCode.ALREADY_CLOSED_NON_IDEMPOTENT,
        GovernedTransitionErrorCode.BYPASS_NOT_EXPIRED,
    )


def test_exceptions_close_raw_git_rewrites_open_lifecycles(
    tmp_path: Path,
    capsys,
) -> None:
    lifecycle_store = tmp_path / "governed_exception_lifecycles.jsonl"
    receipt_store = tmp_path / "raw_git_bypass_receipts.jsonl"
    receipts = [_receipt("abc123", suffix="1"), _receipt("def456", suffix="2")]
    lifecycles = [
        build_raw_git_governed_exception_lifecycle(receipt)
        for receipt in receipts
    ]
    _write_jsonl(receipt_store, [receipt.to_dict() for receipt in receipts])
    _write_jsonl(lifecycle_store, [lifecycle.to_dict() for lifecycle in lifecycles])
    parser = build_parser()
    args = parser.parse_args(
        [
            "exceptions",
            "close-raw-git",
            "--store-path",
            str(lifecycle_store),
            "--receipt-store-path",
            str(receipt_store),
            "--backfill",
            "--format",
            "json",
        ]
    )

    rc = exceptions.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["backfill"] is True
    assert payload["closed_count"] == 2
    assert payload["skipped_count"] == 0
    assert payload["pending_after_count"] == 0
    rows = load_governed_exception_lifecycles(lifecycle_store)
    assert {row.status for row in rows} == {RAW_GIT_COMMIT_ANCHOR_STATUS}
    assert all(row.closure_proof is not None for row in rows)
    assert all(row.resolution is not None for row in rows)


def test_exceptions_close_raw_git_dry_run_does_not_rewrite_store(
    tmp_path: Path,
    capsys,
) -> None:
    lifecycle_store = tmp_path / "governed_exception_lifecycles.jsonl"
    receipt_store = tmp_path / "raw_git_bypass_receipts.jsonl"
    receipt = _receipt("abc123", suffix="1")
    lifecycle = build_raw_git_governed_exception_lifecycle(receipt)
    _write_jsonl(receipt_store, [receipt.to_dict()])
    _write_jsonl(lifecycle_store, [lifecycle.to_dict()])
    parser = build_parser()
    args = parser.parse_args(
        [
            "exceptions",
            "close-raw-git",
            "--store-path",
            str(lifecycle_store),
            "--receipt-store-path",
            str(receipt_store),
            "--dry-run",
            "--format",
            "json",
        ]
    )

    rc = exceptions.run(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["closed_count"] == 1
    rows = load_governed_exception_lifecycles(lifecycle_store)
    assert rows[0].status == "operator_approved"


def test_exceptions_close_raw_git_propagates_stale_commit_anchor_code(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_cli_propagates_transition_code(
        tmp_path,
        capsys,
        monkeypatch,
        expected_code=GovernedTransitionErrorCode.STALE_COMMIT_ANCHOR,
    )


def test_exceptions_close_raw_git_propagates_missing_closure_proof_code(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_cli_propagates_transition_code(
        tmp_path,
        capsys,
        monkeypatch,
        expected_code=GovernedTransitionErrorCode.MISSING_CLOSURE_PROOF,
    )


def test_exceptions_close_raw_git_propagates_mismatched_lifecycle_id_code(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_cli_propagates_transition_code(
        tmp_path,
        capsys,
        monkeypatch,
        expected_code=GovernedTransitionErrorCode.MISMATCHED_LIFECYCLE_ID,
    )


def test_exceptions_close_raw_git_propagates_illegal_transition_code(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_cli_propagates_transition_code(
        tmp_path,
        capsys,
        monkeypatch,
        expected_code=GovernedTransitionErrorCode.ILLEGAL_TRANSITION,
    )


def test_exceptions_close_raw_git_propagates_unknown_old_status_code(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_cli_propagates_transition_code(
        tmp_path,
        capsys,
        monkeypatch,
        expected_code=GovernedTransitionErrorCode.UNKNOWN_OLD_STATUS,
    )


def test_exceptions_close_raw_git_propagates_already_closed_non_idempotent_code(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_cli_propagates_transition_code(
        tmp_path,
        capsys,
        monkeypatch,
        expected_code=GovernedTransitionErrorCode.ALREADY_CLOSED_NON_IDEMPOTENT,
    )


def test_exceptions_close_raw_git_propagates_bypass_not_expired_code(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_cli_propagates_transition_code(
        tmp_path,
        capsys,
        monkeypatch,
        expected_code=GovernedTransitionErrorCode.BYPASS_NOT_EXPIRED,
    )


def test_exceptions_close_raw_git_reports_missing_commit_anchor_without_rewrite(
    tmp_path: Path,
    capsys,
) -> None:
    lifecycle_store = tmp_path / "governed_exception_lifecycles.jsonl"
    receipt_store = tmp_path / "raw_git_bypass_receipts.jsonl"
    receipt = _receipt("", suffix="1")
    lifecycle = build_raw_git_governed_exception_lifecycle(receipt)
    _write_jsonl(receipt_store, [receipt.to_dict()])
    _write_jsonl(lifecycle_store, [lifecycle.to_dict()])
    parser = build_parser()
    args = parser.parse_args(
        [
            "exceptions",
            "close-raw-git",
            "--store-path",
            str(lifecycle_store),
            "--receipt-store-path",
            str(receipt_store),
            "--format",
            "json",
        ]
    )

    rc = exceptions.run(args)

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["closed_count"] == 0
    assert payload["skipped_count"] == 1
    assert payload["skipped_lifecycles"] == [
        {
            "lifecycle_id": lifecycle.lifecycle_id,
            "receipt_id": receipt.receipt_id,
            "reason": "transition_input_invalid:missing_commit_anchor",
        }
    ]
    rows = load_governed_exception_lifecycles(lifecycle_store)
    assert rows[0].status == "operator_approved"
