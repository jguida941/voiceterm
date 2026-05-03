"""Tests for the typed ``devctl session`` orientation packet."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.governance import session
from dev.scripts.devctl.commands.governance import session_orientation
from dev.scripts.devctl.commands.governance import session_orientation_runner


def _completed(command: list[str], payload: dict[str, object], rc: int = 0):
    return subprocess.CompletedProcess(
        args=command,
        returncode=rc,
        stdout=json.dumps(payload),
        stderr="",
    )


def _args(**overrides):
    values = {
        "format": "md",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
        "provider": "",
        "session_id_or_transcript_path": "",
        "write_resume_receipt": False,
        "resume_result": "loaded",
        "authority_result": "",
        "include_review_status": "always",
        "timeout_seconds": 30,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class SessionOrientationTests(unittest.TestCase):
    """Lock in the governed fresh-session bootstrap sequence."""

    def test_orientation_runs_authority_status_and_graph_in_order(self) -> None:
        """A startup blocker is typed data, not a reason to stop early."""
        startup = {
            "command": "startup-context",
            "advisory_action": "checkpoint_before_continue",
            "advisory_reason": "dirty_after_local_checkpoint",
            "authority_snapshot": {
                "required_action": "cut_checkpoint",
                "next_command": "python3 dev/scripts/devctl.py commit -m x",
                "safe_to_continue": False,
                "root_cause": "dirty worktree",
            },
            "startup_receipt": {"head_commit_sha": "abcdef123456"},
            "push_decision": {"action": "await_checkpoint"},
        }
        resume = {
            "command": "session-resume",
            "branch": "feature/session",
            "head_sha": "abcdef123456",
            "blockers": "startup authority",
            "authority_snapshot": {
                "required_action": "continue_scoped_loop",
                "next_command": "python3 dev/scripts/devctl.py commit -m x",
                "safe_to_continue": True,
                "root_cause": "resume says continue",
            },
        }
        status = {
            "command": "review-channel",
            "ok": False,
            "attention": {
                "recommended_command": "python3 dev/scripts/devctl.py commit -m x",
            },
            "authority_snapshot": {
                "required_action": "cut_checkpoint",
                "next_command": (
                    "python3 dev/scripts/devctl.py context-graph "
                    "--mode bootstrap --format md"
                ),
                "safe_to_continue": False,
                "root_cause": "review status wins",
                "packet_target": {"agent": "codex", "latest_finding_packet_id": "rev_pkt_1"},
            },
        }
        graph = {
            "command": "context-graph",
            "branch": "feature/session",
            "snapshot": {
                "path": "dev/reports/graph_snapshots/example.json",
                "commit_hash": "abcdef123456",
                "node_count": 7,
                "edge_count": 9,
            },
            "active_plans": [],
            "hotspots": [],
        }

        calls: list[list[str]] = []

        def fake_run(command, _repo_root, *, timeout_seconds):
            calls.append(command)
            payload = (startup, resume, status, graph)[len(calls) - 1]
            rc = 1 if len(calls) == 1 else 0
            return _completed(command, payload, rc=rc)

        with patch.object(
            session_orientation_runner,
            "_run_subprocess",
            side_effect=fake_run,
        ):
            packet = session_orientation.build_session_orientation(
                _args(),
                Path("/repo"),
                role="implementer",
            )

        self.assertEqual([step.name for step in packet.steps], [
            "startup",
            "session_resume",
            "review_status",
            "context_graph",
        ])
        self.assertEqual(packet.steps[0].exit_code, 1)
        self.assertTrue(packet.steps[0].parsed)
        self.assertTrue(packet.final["orientation_complete"])
        self.assertEqual(packet.final["next_command_source"], "review_status.attention")
        self.assertEqual(
            packet.final["next_command"],
            "python3 dev/scripts/devctl.py commit -m x",
        )
        self.assertEqual(packet.final["required_action"], "cut_checkpoint")
        self.assertEqual(
            packet.context_graph["snapshot"]["path"],
            "dev/reports/graph_snapshots/example.json",
        )
        self.assertIn("--terminal", calls[2])
        self.assertIn("none", calls[2])

    def test_session_command_maps_dashboard_to_observer_orientation(self) -> None:
        with patch.object(session, "emit_session_orientation", return_value=0) as emit_mock:
            rc = session.run(
                SimpleNamespace(
                    role="dashboard",
                    loop=False,
                    interval=30,
                    headless=True,
                )
            )

        self.assertEqual(rc, 0)
        self.assertEqual(emit_mock.call_args.kwargs["role"], "observer")


if __name__ == "__main__":
    unittest.main()
