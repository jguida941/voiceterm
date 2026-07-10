"""Tests for the devctl command-result contract probe."""

from __future__ import annotations

from dev.scripts.checks.review_probes.probe_command_result_contract import (
    CommandJsonObservation,
    command_result_contract_hints,
)


def test_command_result_contract_hints_pass_for_complete_envelope() -> None:
    hints = command_result_contract_hints(
        (
            CommandJsonObservation(
                label="good-command",
                argv=("python3", "dev/scripts/devctl.py", "good-command"),
                exit_code=0,
                payload={
                    "command": "good-command",
                    "ok": True,
                    "exit_ok": True,
                    "exit_code": 0,
                    "status": "ok",
                    "errors": [],
                },
            ),
        )
    )

    assert hints == []


def test_command_result_contract_hints_flag_missing_fields() -> None:
    hints = command_result_contract_hints(
        (
            CommandJsonObservation(
                label="path-audit",
                argv=("python3", "dev/scripts/devctl.py", "path-audit"),
                exit_code=0,
                payload={"command": "path-audit", "ok": True},
            ),
        )
    )

    assert len(hints) == 1
    assert hints[0].symbol == "path-audit"
    assert "missing_fields=exit_ok,exit_code,status,errors" in hints[0].signals


def test_command_result_contract_hints_flag_wrong_types() -> None:
    hints = command_result_contract_hints(
        (
            CommandJsonObservation(
                label="bad-types",
                argv=("python3", "dev/scripts/devctl.py", "bad-types"),
                exit_code=0,
                payload={
                    "command": "bad-types",
                    "ok": "true",
                    "exit_ok": True,
                    "exit_code": True,
                    "status": ["ok"],
                    "errors": "none",
                },
            ),
        )
    )

    assert len(hints) == 1
    assert "wrong_field_types=ok,exit_code,status,errors" in hints[0].signals


def test_command_result_contract_hints_flag_parse_failure() -> None:
    hints = command_result_contract_hints(
        (
            CommandJsonObservation(
                label="html-output",
                argv=("python3", "dev/scripts/devctl.py", "html-output"),
                exit_code=1,
                payload={},
                parse_error="Expecting value at line 1 column 1",
            ),
        )
    )

    assert len(hints) == 1
    assert "process_exit_code=1" in hints[0].signals
    assert "json_parse_error=Expecting value at line 1 column 1" in hints[0].signals
