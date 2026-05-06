"""CLI tests for the governed exceptions command."""

from __future__ import annotations

import json

import pytest

from dev.scripts.devctl import cli


def test_exceptions_parser_and_handler_registered() -> None:
    args = cli.build_parser().parse_args(["exceptions", "pending", "--format", "json"])
    assert args.command == "exceptions"
    assert args.action == "pending"
    assert "exceptions" in cli.COMMAND_HANDLERS
    assert "exceptions" in cli.READ_ONLY_COMMANDS


def test_exceptions_request_is_not_slice_one_public_surface() -> None:
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["exceptions", "request", "--format", "json"])


def test_exceptions_pending_missing_store_returns_empty(capsys, tmp_path) -> None:
    args = cli.build_parser().parse_args(
        [
            "exceptions",
            "pending",
            "--store-path",
            str(tmp_path / "missing.jsonl"),
            "--format",
            "json",
        ]
    )

    assert cli.COMMAND_HANDLERS["exceptions"](args) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is True
    assert payload["pending_count"] == 0
    assert payload["lifecycles"] == []
    assert payload["errors"] == []


def test_exceptions_pending_reports_malformed_store(capsys, tmp_path) -> None:
    store = tmp_path / "lifecycles.jsonl"
    store.write_text("{bad-json\n", encoding="utf-8")
    args = cli.build_parser().parse_args(
        [
            "exceptions",
            "pending",
            "--store-path",
            str(store),
            "--format",
            "json",
        ]
    )

    assert cli.COMMAND_HANDLERS["exceptions"](args) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is False
    assert payload["pending_count"] == 0
    assert payload["errors"]


def test_exceptions_validate_reports_invalid_fixture(capsys, tmp_path) -> None:
    fixture = tmp_path / "receipt.json"
    fixture.write_text(
        json.dumps(
            {
                "contract_id": "ExceptionReceipt",
                "receipt_id": "exception:test",
                "action_kind": "vcs.push",
                "phase": "preflight",
                "guard_id": "review_snapshot_refresh",
                "exception_class": "review_snapshot_refresh_failure",
                "operator_reason": "bypass",
                "head": "",
            }
        ),
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        ["exceptions", "validate", str(fixture), "--format", "json"]
    )

    assert cli.COMMAND_HANDLERS["exceptions"](args) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is False
    assert "line 1: missing_head" in payload["errors"]
    assert "line 1: missing_or_generic_reason" in payload["errors"]


def test_exceptions_validate_does_not_misclassify_other_receipts(
    capsys,
    tmp_path,
) -> None:
    fixture = tmp_path / "manual_bypass.json"
    fixture.write_text(
        json.dumps(
            {
                "contract_id": "ManualBypassImportReceipt",
                "receipt_id": "manual:test",
                "action_kind": "vcs.push",
                "operator_reason": "Manual import records historical evidence only.",
                "head": "58246e50",
            }
        ),
        encoding="utf-8",
    )
    args = cli.build_parser().parse_args(
        ["exceptions", "validate", str(fixture), "--format", "json"]
    )

    assert cli.COMMAND_HANDLERS["exceptions"](args) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is False
    assert "line 1: unsupported_contract:ManualBypassImportReceipt" in payload["errors"]
