"""Tests for operator-runnable governance demos."""

from __future__ import annotations

import json

from dev.scripts.devctl import cli


def test_demo_verify_override_reports_edit_only_receipt(capsys) -> None:
    args = cli.build_parser().parse_args(
        ["demo", "verify-override", "--format", "json"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["receipt"]["contract_id"] == "DemoValidationReceipt"
    proof = payload["proof"]
    assert proof["edit_allowed"] is True
    assert proof["stage_blocked"] is True
    assert proof["commit_blocked"] is True
    assert proof["push_blocked"] is True


def test_demo_verify_final_response_gate_denies_open_controller(capsys) -> None:
    args = cli.build_parser().parse_args(
        ["demo", "verify-final-response-gate", "--format", "json"]
    )

    rc = cli.COMMAND_HANDLERS[args.command](args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    gate = payload["proof"]["final_response_gate"]
    assert payload["ok"] is True
    assert gate["allow_final_response"] is False
    assert gate["action"] == "run_next_command"
    assert gate["next_required_command"].endswith("--actor codex --format md")
