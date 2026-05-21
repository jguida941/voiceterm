"""Tests for the ``devctl agent-supervise`` command surface."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.runtime import agent_supervise
from dev.scripts.devctl.runtime.agent_supervise_driver import (
    AgentSuperviseLaunchResult,
    AgentSuperviseReport,
)


def test_agent_supervise_parser_accepts_threshold_alias() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    agent_supervise.add_parser(sub)

    args = parser.parse_args(["agent-supervise", "--threshold-seconds", "7"])

    assert args.staleness_threshold_seconds == 7


def test_agent_supervise_parser_accepts_execute_flag() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    agent_supervise.add_parser(sub)

    args = parser.parse_args(["agent-supervise", "--execute"])

    assert args.execute is True


def test_v4551_agent_supervise_command_exits_zero_for_ignored_helper_closed(
    tmp_path: Path,
    capsys,
) -> None:
    """v4.55.1 priority 1 (rev_pkt_4764/4765): `--session-id` audit of a
    closed read-only helper sidecar must surface as a typed nonblocking
    outcome with CLI exit code 0, so audit callers do not falsely fail
    when a helper is just dormant. Status must be `ignored_helper_closed`
    and `blocked_reasons` must be empty.
    """
    session = tmp_path / "rollout-2026-05-12T01-00-00-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl"
    session.write_text("{}\n", encoding="utf-8")
    os.utime(session, (0, 0))
    review_state = tmp_path / "review_state.json"
    review_state.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "packet_id": "rev_pkt_4381_shape",
                        "kind": "continuation_anchor",
                        "to_agent": "codex",
                        "target_role": "",
                        "target_session_id": "",
                        "session_id": None,
                        "anchor_scope": "",
                        "status": "acked",
                        "lifecycle_current_state": "acknowledged",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rc = agent_supervise.run(
        SimpleNamespace(
            actor="codex",
            provider="codex",
            role="reviewer",
            pid=0,
            session_id="019e4a49-5c2c-7292-84cb-272045b48c92",
            session_path=str(session),
            sessions_root="",
            review_state_path=str(review_state),
            bypass_receipt_file="",
            bypass_receipt_json="",
            staleness_threshold_seconds=600,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ignored_helper_closed"
    assert payload["continuation_anchor_live"] is False
    assert payload["blocked_reasons"] == []
    assert payload["spawn_action"] is None
    assert payload["next_command"] == ""


def test_agent_supervise_command_reports_spawn_authorized(
    tmp_path: Path,
    capsys,
) -> None:
    session = tmp_path / "rollout-2026-05-12T01-00-00-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl"
    session.write_text("{}\n", encoding="utf-8")
    os.utime(session, (0, 0))
    review_state = tmp_path / "review_state.json"
    review_state.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "packet_id": "rev_pkt_anchor",
                        "kind": "continuation_anchor",
                        "to_agent": "codex",
                        "status": "pending",
                        "lifecycle_current_state": "pending",
                    }
                ],
                "collaboration": {
                    "loop_autonomy_ok": True,
                    "loop_wake_mode": "continuous",
                    "loop_driver_agent": "claude",
                },
            }
        ),
        encoding="utf-8",
    )
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "receipt_id": "bypass:spawn:test",
                "reason": "operator approved",
                "operator_signature": "operator",
                "ai_approval_evidence": "rev_pkt_3685",
                "requested_authority_scope": "agent_spawn_only",
                "granted_at_utc": "2026-05-12T00:00:00Z",
                "granted_by_operator_actor_id": "operator",
            }
        ),
        encoding="utf-8",
    )

    rc = agent_supervise.run(
        SimpleNamespace(
            actor="codex",
            provider="codex",
            role="reviewer",
            pid=0,
            session_id="",
            session_path=str(session),
            sessions_root="",
            review_state_path=str(review_state),
            bypass_receipt_file=str(receipt),
            bypass_receipt_json="",
            staleness_threshold_seconds=1,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )
    )

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "spawn_authorized"
    assert payload["spawn_action"]["continuation_anchor_packet_id"] == "rev_pkt_anchor"


def test_agent_supervise_command_executes_when_requested(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    session = tmp_path / "rollout-2026-05-12T01-00-00-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.jsonl"
    session.write_text("{}\n", encoding="utf-8")
    os.utime(session, (0, 0))
    review_state = tmp_path / "review_state.json"
    review_state.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "packet_id": "rev_pkt_anchor",
                        "kind": "continuation_anchor",
                        "to_agent": "codex",
                        "status": "pending",
                        "lifecycle_current_state": "pending",
                    }
                ],
                "collaboration": {
                    "loop_autonomy_ok": True,
                    "loop_wake_mode": "continuous",
                    "loop_driver_agent": "claude",
                },
            }
        ),
        encoding="utf-8",
    )
    called = False

    def _execute(report: AgentSuperviseReport) -> AgentSuperviseReport:
        nonlocal called
        called = True
        return replace(
            report,
            launch_result=AgentSuperviseLaunchResult(
                status="spawned",
                command=("python3", "dev/scripts/devctl.py"),
                pid=12345,
            ),
        )

    monkeypatch.setattr(agent_supervise, "execute_agent_supervision_spawn", _execute)

    rc = agent_supervise.run(
        SimpleNamespace(
            actor="codex",
            provider="codex",
            role="reviewer",
            pid=99_999_999,
            session_id="",
            session_path=str(session),
            sessions_root="",
            review_state_path=str(review_state),
            bypass_receipt_file="",
            bypass_receipt_json=json.dumps(
                {
                    "receipt_id": "bypass:spawn:test",
                    "reason": "operator approved",
                    "operator_signature": "operator",
                    "ai_approval_evidence": "rev_pkt_3685",
                    "requested_authority_scope": "agent_spawn_only",
                    "granted_at_utc": "2026-05-12T00:00:00Z",
                    "granted_by_operator_actor_id": "operator",
                }
            ),
            staleness_threshold_seconds=1,
            execute=True,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )
    )

    assert rc == 0
    assert called is True
    payload = json.loads(capsys.readouterr().out)
    assert payload["launch_result"]["status"] == "spawned"
    assert payload["launch_result"]["pid"] == 12345
