"""Tests for the typed ``devctl session`` orientation packet."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.governance import session
from dev.scripts.devctl.commands.governance import session_orientation
from dev.scripts.devctl.cli_parser.artifact_suppression import ARTIFACT_WRITES_ENV
from dev.scripts.devctl.commands.governance.session_orientation_command_classification import (
    CommandClassification,
    classify_devctl_command,
)
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

        def fake_run(
            command,
            _repo_root,
            *,
            timeout_seconds,
            suppress_artifact_writes=False,
        ):
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

    def test_session_child_artifact_suppression_preserves_graph_freshness(self) -> None:
        specs = session_orientation_runner._step_specs(_args(), "implementer")

        self.assertEqual(
            [(spec.name, spec.suppress_artifact_writes) for spec in specs],
            [
                ("startup", True),
                ("session_resume", True),
                ("review_status", True),
                ("context_graph", False),
            ],
        )

    def test_suppressed_session_child_sets_artifact_suppression_env(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["python3"],
            returncode=0,
            stdout="{}",
            stderr="",
        )
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(
                session_orientation_runner.subprocess,
                "run",
                return_value=completed,
            ) as run_mock:
                session_orientation_runner._run_subprocess(
                    ["python3", "dev/scripts/devctl.py", "startup-context"],
                    Path("/repo"),
                    timeout_seconds=1,
                    suppress_artifact_writes=True,
                )

        self.assertEqual(run_mock.call_args.kwargs["env"][ARTIFACT_WRITES_ENV], "1")

    def test_command_classifier_identifies_only_devctl_push_commands(self) -> None:
        self.assertIs(
            classify_devctl_command(
                "PYTHONDONTWRITEBYTECODE=1 python3 "
                "/repo/dev/scripts/devctl.py push --execute"
            ),
            CommandClassification.GOVERNED_PUSH,
        )
        self.assertIs(
            classify_devctl_command("devctl push --execute"),
            CommandClassification.GOVERNED_PUSH,
        )
        self.assertIs(
            classify_devctl_command("echo devctl.py push --execute"),
            CommandClassification.UNKNOWN,
        )

    def test_startup_push_decision_beats_idle_status_command(self) -> None:
        """Fresh sessions should surface push when startup proves it is next."""
        startup = {
            "command": "startup-context",
            "advisory_action": "push_allowed",
            "authority_snapshot": {
                "required_action": "continue_scoped_loop",
                "next_command": "python3 dev/scripts/devctl.py push --execute",
                "safe_to_continue": True,
                "root_cause": "worktree clean",
            },
            "startup_receipt": {"head_commit_sha": "abcdef123456"},
            "push_decision": {
                "action": "run_devctl_push",
                "next_step_command": "python3 dev/scripts/devctl.py push --execute",
                "reason": "push_preconditions_satisfied",
            },
        }
        resume = {
            "command": "session-resume",
            "branch": "feature/session",
            "head_sha": "abcdef123456",
            "authority_snapshot": {
                "required_action": "continue_scoped_loop",
                "next_command": "python3 dev/scripts/devctl.py review-channel --action status",
                "safe_to_continue": True,
                "root_cause": "resume healthy",
            },
        }
        status = {
            "command": "review-channel",
            "ok": True,
            "attention": {
                "status": "healthy",
                "recommended_command": "",
            },
            "authority_snapshot": {
                "required_action": "continue_scoped_loop",
                "next_command": (
                    "python3 dev/scripts/devctl.py review-channel "
                    "--action status --terminal none --format json"
                ),
                "safe_to_continue": True,
                "root_cause": "review loop healthy",
            },
        }
        graph = {
            "command": "context-graph",
            "branch": "feature/session",
            "snapshot": {
                "path": "dev/reports/graph_snapshots/example.json",
                "commit_hash": "abcdef123456",
            },
        }

        calls: list[list[str]] = []

        def fake_run(
            command,
            _repo_root,
            *,
            timeout_seconds,
            suppress_artifact_writes=False,
        ):
            calls.append(command)
            payload = (startup, resume, status, graph)[len(calls) - 1]
            return _completed(command, payload)

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

        self.assertEqual(packet.final["next_command_source"], "startup.push_decision")
        self.assertEqual(
            packet.final["next_command"],
            "python3 dev/scripts/devctl.py push --execute",
        )

    def test_startup_push_decision_does_not_override_blocking_authority(self) -> None:
        """A fresh-session packet must not recommend push through a live blocker."""
        startup = {
            "command": "startup-context",
            "advisory_action": "push_allowed",
            "authority_snapshot": {
                "required_action": "continue_scoped_loop",
                "next_command": "python3 dev/scripts/devctl.py push --execute",
                "safe_to_continue": True,
                "root_cause": "worktree clean",
            },
            "startup_receipt": {"head_commit_sha": "abcdef123456"},
            "push_decision": {
                "action": "run_devctl_push",
                "next_step_command": "python3 dev/scripts/devctl.py push --execute",
                "reason": "push_preconditions_satisfied",
            },
        }
        resume = {
            "command": "session-resume",
            "branch": "feature/session",
            "head_sha": "abcdef123456",
            "authority_snapshot": {
                "required_action": "resume_live_review_loop",
                "next_command": "python3 dev/scripts/devctl.py review-channel --action status",
                "safe_to_continue": False,
                "root_cause": "review loop inactive",
                "blocked_actions": ["vcs.push"],
            },
        }
        status = {
            "command": "review-channel",
            "ok": True,
            "attention": {"status": "inactive", "recommended_command": ""},
            "authority_snapshot": {
                "required_action": "resume_live_review_loop",
                "next_command": (
                    "python3 dev/scripts/devctl.py review-channel "
                    "--action status --terminal none --format json"
                ),
                "safe_to_continue": False,
                "root_cause": "review loop inactive",
                "blocked_actions": ["implementation.edit", "vcs.push"],
            },
        }
        graph = {
            "command": "context-graph",
            "branch": "feature/session",
            "snapshot": {
                "path": "dev/reports/graph_snapshots/example.json",
                "commit_hash": "abcdef123456",
            },
        }

        calls: list[list[str]] = []

        def fake_run(
            command,
            _repo_root,
            *,
            timeout_seconds,
            suppress_artifact_writes=False,
        ):
            calls.append(command)
            payload = (startup, resume, status, graph)[len(calls) - 1]
            return _completed(command, payload)

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

        self.assertEqual(packet.final["next_command_source"], "review_status")
        self.assertEqual(
            packet.final["next_command"],
            (
                "python3 dev/scripts/devctl.py review-channel "
                "--action status --terminal none --format json"
            ),
        )
        self.assertFalse(packet.final["safe_to_continue"])

    def test_fallback_push_decision_does_not_override_blocking_authority(self) -> None:
        """Push fallback cannot bypass a blocking preferred AuthoritySnapshot."""
        startup = {
            "command": "startup-context",
            "authority_snapshot": {
                "required_action": "continue_scoped_loop",
                "next_command": "",
                "safe_to_continue": True,
            },
            "push_decision": {
                "action": "run_devctl_push",
                "next_step_command": "python3 dev/scripts/devctl.py push --execute",
            },
        }
        resume = {
            "command": "session-resume",
            "authority_snapshot": {
                "required_action": "resume_live_review_loop",
                "next_command": "",
                "safe_to_continue": True,
            },
        }
        status = {
            "command": "review-channel",
            "ok": True,
            "attention": {"status": "inactive", "recommended_command": ""},
            "authority_snapshot": {
                "required_action": "resume_live_review_loop",
                "next_command": "",
                "safe_to_continue": False,
                "root_cause": "review loop inactive",
                "blocked_actions": ["vcs.push"],
            },
        }
        graph = {
            "command": "context-graph",
            "snapshot": {"path": "dev/reports/graph_snapshots/example.json"},
        }

        calls: list[list[str]] = []

        def fake_run(
            command,
            _repo_root,
            *,
            timeout_seconds,
            suppress_artifact_writes=False,
        ):
            calls.append(command)
            payload = (startup, resume, status, graph)[len(calls) - 1]
            return _completed(command, payload)

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

        self.assertEqual(packet.final["next_command_source"], "review_status")
        self.assertEqual(packet.final["next_command"], "")
        self.assertFalse(packet.final["safe_to_continue"])


if __name__ == "__main__":
    unittest.main()
