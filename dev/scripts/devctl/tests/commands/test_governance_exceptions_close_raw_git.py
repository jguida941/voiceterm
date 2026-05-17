from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.governance import exceptions
from dev.scripts.devctl.runtime.governed_exception_store import (
    load_governed_exception_lifecycles,
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
