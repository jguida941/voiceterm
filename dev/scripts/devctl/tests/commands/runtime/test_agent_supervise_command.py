"""Tests for the ``devctl agent-supervise`` command surface."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.runtime import agent_supervise


def test_agent_supervise_parser_accepts_threshold_alias() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    agent_supervise.add_parser(sub)

    args = parser.parse_args(["agent-supervise", "--threshold-seconds", "7"])

    assert args.staleness_threshold_seconds == 7


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
