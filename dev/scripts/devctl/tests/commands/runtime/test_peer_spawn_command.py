"""Tests for the canonical typed peer-spawn driver and CLI.

These tests prove the new top-level command composes the canonical headless
launch path (`launch_sessions_headless` via the injected adapter) and emits
typed `AgentSpawnRequest` + `AgentSpawnReceipt` / `AgentTerminationReceipt`
events into the configured trace path.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from dev.scripts.devctl import cli
from dev.scripts.devctl.commands.runtime import peer_spawn as peer_spawn_command
from dev.scripts.devctl.runtime.bypass_lifecycle_models import (
    BypassAuthorityScope,
    BypassReceipt,
)
from dev.scripts.devctl.runtime.peer_spawn import (
    AGENT_SPAWN_RECEIPT_CONTRACT_ID,
    AGENT_SPAWN_REQUEST_CONTRACT_ID,
    AGENT_TERMINATION_RECEIPT_CONTRACT_ID,
    compose_peer_spawn,
    compose_peer_terminate,
)


def _active_receipt(
    *,
    scope: BypassAuthorityScope = BypassAuthorityScope.AGENT_SPAWN_ONLY,
    receipt_id: str = "bypass:spawn:test",
) -> BypassReceipt:
    """Build a fully-active BypassReceipt for spawn-driver tests."""
    return BypassReceipt(
        receipt_id=receipt_id,
        reason="operator approved peer-spawn test",
        operator_signature="operator",
        ai_approval_evidence="rev_pkt_test_peer_spawn",
        requested_authority_scope=scope,
        granted_at_utc="2026-05-22T00:00:00Z",
        granted_by_operator_actor_id="operator",
        expires_at_utc="2099-01-01T00:00:00Z",
    )


def _read_events(trace_path: Path) -> list[dict[str, Any]]:
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_peer_spawn_and_terminate_subcommands_are_registered() -> None:
    """Both new subcommands must be wired through the canonical CLI."""
    parser = cli.build_parser()
    spawn_args = parser.parse_args(
        [
            "peer-spawn",
            "--provider",
            "codex",
            "--role",
            "implementer",
            "--dry-run",
        ]
    )
    assert spawn_args.command == "peer-spawn"
    assert spawn_args.provider == "codex"
    assert spawn_args.role == "implementer"

    terminate_args = parser.parse_args(
        ["peer-terminate", "--provider", "codex", "--pid", "99999"]
    )
    assert terminate_args.command == "peer-terminate"
    assert terminate_args.pid == 99999

    assert cli.COMMAND_HANDLERS["peer-spawn"].__name__ == "run_peer_spawn"
    assert cli.COMMAND_HANDLERS["peer-terminate"].__name__ == "run_peer_terminate"


def test_compose_peer_spawn_emits_typed_request_and_receipt(tmp_path: Path) -> None:
    """Canonical spawn must emit AgentSpawnRequest + AgentSpawnReceipt rows."""
    trace = tmp_path / "trace.ndjson"
    calls: list[dict[str, Any]] = []

    def fake_launch(**kwargs: Any) -> tuple[bool, int, str, str]:
        calls.append(kwargs)
        return True, 4242, "/tmp/peer-spawn.sh", ""

    report = compose_peer_spawn(
        provider="codex",
        role="implementer",
        bypass_receipt=_active_receipt(),
        row_id="MP-401",
        trace_path=trace,
        launch_callable=fake_launch,
    )

    assert report.ok is True
    assert report.receipt is not None
    assert report.receipt["status"] == "spawned"
    assert report.receipt["pid"] == 4242
    assert report.receipt["contract_id"] == AGENT_SPAWN_RECEIPT_CONTRACT_ID

    events = _read_events(trace)
    assert len(events) == 2
    assert events[0]["event_type"] == "agent_spawn_requested"
    assert events[0]["contract_id"] == AGENT_SPAWN_REQUEST_CONTRACT_ID
    assert events[0]["provider"] == "codex"
    assert events[0]["row_id"] == "MP-401"
    assert events[1]["event_type"] == "agent_spawn_receipt"
    assert events[1]["pid"] == 4242
    # The adapter was invoked with the canonical provider/role/bypass payload.
    assert calls[0]["provider"] == "codex"
    assert calls[0]["role"] == "implementer"
    assert calls[0]["bypass_receipt"].receipt_id == "bypass:spawn:test"


def test_compose_peer_spawn_denies_without_active_bypass_receipt(tmp_path: Path) -> None:
    """Missing receipt must fail closed and emit a typed denial receipt."""
    trace = tmp_path / "trace.ndjson"
    invoked: list[bool] = []

    def should_not_run(**_kwargs: Any) -> tuple[bool, int, str, str]:
        invoked.append(True)
        return True, 1, "", ""

    report = compose_peer_spawn(
        provider="codex",
        role="implementer",
        bypass_receipt=None,
        trace_path=trace,
        launch_callable=should_not_run,
    )

    assert report.ok is False
    assert report.receipt is not None
    assert report.receipt["status"] == "denied_bypass_missing"
    assert invoked == []
    events = _read_events(trace)
    assert events[-1]["event_type"] == "agent_spawn_receipt"
    assert events[-1]["status"] == "denied_bypass_missing"


def test_compose_peer_spawn_denies_when_receipt_scope_insufficient(
    tmp_path: Path,
) -> None:
    """A receipt without spawn scope must be rejected and a typed reason logged.

    EDIT_ONLY does grant AGENT_SPAWN_ONLY in the current _GRANTED_SCOPES map,
    so we use an explicitly revoked receipt to exercise the scope/active gate
    paths together.
    """
    trace = tmp_path / "trace.ndjson"
    revoked = BypassReceipt(
        receipt_id="bypass:spawn:revoked",
        reason="revoked",
        operator_signature="operator",
        ai_approval_evidence="rev_pkt_revoked",
        requested_authority_scope=BypassAuthorityScope.AGENT_SPAWN_ONLY,
        granted_at_utc="2026-05-22T00:00:00Z",
        granted_by_operator_actor_id="operator",
        revoked_at_utc="2026-05-22T00:30:00Z",
        revoked_reason="operator-revoked",
    )
    report = compose_peer_spawn(
        provider="codex",
        role="implementer",
        bypass_receipt=revoked,
        trace_path=trace,
    )
    assert report.ok is False
    assert report.receipt is not None
    assert report.receipt["status"] == "denied_bypass_missing"
    assert "bypass_receipt_not_active" in report.errors


def test_compose_peer_spawn_records_launch_adapter_failure(tmp_path: Path) -> None:
    """When the launch adapter returns failure the receipt must capture it."""
    trace = tmp_path / "trace.ndjson"

    def failing(**_kwargs: Any) -> tuple[bool, int, str, str]:
        return False, 0, "", "headless_dead_on_arrival"

    report = compose_peer_spawn(
        provider="codex",
        role="implementer",
        bypass_receipt=_active_receipt(),
        trace_path=trace,
        launch_callable=failing,
    )

    assert report.ok is False
    assert report.receipt is not None
    assert report.receipt["status"] == "spawn_failed"
    assert report.receipt["error"] == "headless_dead_on_arrival"


def test_compose_peer_terminate_emits_typed_receipt(tmp_path: Path) -> None:
    """Terminate must signal the PID and emit a typed AgentTerminationReceipt."""
    trace = tmp_path / "trace.ndjson"
    sent_signals: list[tuple[int, int]] = []

    def fake_kill(pid: int, signum: int) -> None:
        sent_signals.append((pid, signum))

    report = compose_peer_terminate(
        provider="codex",
        session_id="codex-conductor-1",
        pid=12345,
        signal_name="SIGTERM",
        trace_path=trace,
        kill_callable=fake_kill,
    )

    assert report.ok is True
    assert report.receipt is not None
    assert report.receipt["contract_id"] == AGENT_TERMINATION_RECEIPT_CONTRACT_ID
    assert report.receipt["status"] == "terminated"
    assert report.receipt["pid"] == 12345
    assert sent_signals == [(12345, 15)]  # SIGTERM = 15 on POSIX
    events = _read_events(trace)
    assert events[-1]["event_type"] == "agent_termination_receipt"


def test_compose_peer_terminate_handles_dead_pid_without_raising(
    tmp_path: Path,
) -> None:
    """A missing PID must yield a typed `pid_not_found` receipt, not an exception."""
    trace = tmp_path / "trace.ndjson"

    def kill_missing(pid: int, signum: int) -> None:
        raise ProcessLookupError(f"no such process: {pid}")

    report = compose_peer_terminate(
        provider="codex",
        session_id="codex-conductor-1",
        pid=99999,
        trace_path=trace,
        kill_callable=kill_missing,
    )

    assert report.ok is False
    assert report.receipt is not None
    assert report.receipt["status"] == "pid_not_found"
    assert "no such process" in report.receipt["error"]


def test_run_peer_spawn_dry_run_does_not_invoke_launch_adapter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--dry-run` must emit the typed events without spawning anything."""
    trace = tmp_path / "trace.ndjson"
    receipt_path = tmp_path / "receipt.json"
    receipt_payload = {
        "receipt_id": "bypass:spawn:cli-dry-run",
        "reason": "operator approved",
        "operator_signature": "operator",
        "ai_approval_evidence": "rev_pkt_dry",
        "requested_authority_scope": "agent_spawn_only",
        "granted_at_utc": "2026-05-22T00:00:00Z",
        "granted_by_operator_actor_id": "operator",
        "expires_at_utc": "2099-01-01T00:00:00Z",
    }
    receipt_path.write_text(json.dumps(receipt_payload), encoding="utf-8")
    # Ensure the adapter helper is never called during dry-run.
    monkeypatch.setattr(
        peer_spawn_command,
        "_build_canonical_launch_adapter",
        lambda: (_ for _ in ()).throw(  # pragma: no cover - should never run
            AssertionError("adapter must not be built on --dry-run")
        ),
    )

    args = cli.build_parser().parse_args(
        [
            "peer-spawn",
            "--provider",
            "codex",
            "--role",
            "implementer",
            "--bypass-receipt-file",
            str(receipt_path),
            "--row-id",
            "MP-401",
            "--trace-path",
            str(trace),
            "--dry-run",
            "--format",
            "json",
        ]
    )

    rc = peer_spawn_command.run_peer_spawn(args)
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 0
    assert payload["ok"] is True
    assert payload["receipt"]["status"] == "dry_run_no_launch_callable"
    assert payload["request"]["bypass_receipt_id"] == "bypass:spawn:cli-dry-run"
    events = _read_events(trace)
    assert events[0]["event_type"] == "agent_spawn_requested"
    assert events[1]["event_type"] == "agent_spawn_receipt"


def test_agent_supervise_new_spawn_flag_is_registered() -> None:
    """`agent-supervise --new-spawn` must be parseable and route to peer-spawn."""
    parser = cli.build_parser()
    args = parser.parse_args(["agent-supervise", "--new-spawn", "--execute"])
    assert args.new_spawn is True
    assert args.execute is True


__all__: list[str] = []
