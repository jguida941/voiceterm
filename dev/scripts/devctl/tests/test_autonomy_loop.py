"""Tests for devctl autonomy-loop parser and command behavior."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import autonomy_loop


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "repo": "owner/repo",
        "plan_id": "mp-ctrl",
        "branch_base": "develop",
        "working_branch_prefix": "autoloop",
        "workflow": "CodeRabbit Triage Bridge",
        "mode": "report-only",
        "loop_branch_mode": "base",
        "fix_command": None,
        "max_rounds": 2,
        "max_hours": 1.0,
        "max_tasks": 10,
        "checkpoint_every": 1,
        "loop_max_attempts": 1,
        "run_list_limit": 30,
        "poll_seconds": 20,
        "timeout_seconds": 1800,
        "notify": "summary-only",
        "comment_target": "auto",
        "comment_pr_number": None,
        "packet_out": "dev/reports/autonomy/packets",
        "queue_out": "dev/reports/autonomy/queue",
        "max_packet_age_hours": 72.0,
        "max_draft_chars": 1600,
        "allow_auto_send": False,
        "terminal_trace_lines": 12,
        "dry_run": True,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _triage_payload(*, mode: str, unresolved_count: int, reason: str, attempt: int) -> dict:
    return {
        "command": "triage-loop",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": unresolved_count == 0,
        "repo": "owner/repo",
        "branch": "develop",
        "mode": mode,
        "unresolved_count": unresolved_count,
        "reason": reason,
        "attempts": [
            {
                "attempt": attempt,
                "run_id": 100 + attempt,
                "run_sha": "a" * 40,
                "run_url": f"https://example.invalid/run/{100 + attempt}",
                "run_conclusion": "success",
                "backlog_count": unresolved_count,
                "status": "resolved" if unresolved_count == 0 else "blocked",
                "message": "simulated attempt",
            }
        ],
    }


def _loop_packet_payload(*, unresolved_count: int) -> dict:
    risk = "low" if unresolved_count == 0 else "medium"
    return {
        "command": "loop-packet",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ok": True,
        "reason": "packet_ready",
        "risk": risk,
        "next_actions": ["review next step"],
        "terminal_packet": {
            "packet_id": "abc123",
            "source_command": "triage-loop",
            "draft_text": "Loop feedback packet",
            "auto_send": False,
        },
    }


class AutonomyLoopParserTests(unittest.TestCase):
    def test_cli_accepts_autonomy_loop_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "autonomy-loop",
                "--repo",
                "owner/repo",
                "--plan-id",
                "mp-325",
                "--branch-base",
                "develop",
                "--mode",
                "plan-then-fix",
                "--max-rounds",
                "4",
                "--max-hours",
                "2",
                "--max-tasks",
                "12",
                "--checkpoint-every",
                "2",
                "--allow-auto-send",
                "--format",
                "md",
            ]
        )
        self.assertEqual(args.command, "autonomy-loop")
        self.assertEqual(args.repo, "owner/repo")
        self.assertEqual(args.plan_id, "mp-325")
        self.assertEqual(args.branch_base, "develop")
        self.assertEqual(args.mode, "plan-then-fix")
        self.assertEqual(args.max_rounds, 4)
        self.assertEqual(args.max_hours, 2.0)
        self.assertEqual(args.max_tasks, 12)
        self.assertEqual(args.checkpoint_every, 2)
        self.assertTrue(args.allow_auto_send)
        self.assertEqual(args.format, "md")


class AutonomyLoopCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.autonomy_loop.resolve_repo", return_value="owner/repo")
    @patch("dev.scripts.devctl.commands.autonomy_loop._load_policy", return_value={})
    def test_run_emits_round_packets_and_resolves(
        self,
        _policy_mock,
        _resolve_repo_mock,
    ) -> None:
        round_counter = {"count": 0}

        def triage_side_effect(args) -> int:
            round_counter["count"] += 1
            unresolved = 2 if round_counter["count"] == 1 else 0
            reason = "no fix command configured" if unresolved else "resolved"
            payload = _triage_payload(
                mode=args.mode,
                unresolved_count=unresolved,
                reason=reason,
                attempt=round_counter["count"],
            )
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(json.dumps(payload), encoding="utf-8")
            return 1 if unresolved else 0

        def packet_side_effect(args) -> int:
            source_payload = json.loads(Path(args.source_json[0]).read_text(encoding="utf-8"))
            payload = _loop_packet_payload(
                unresolved_count=int(source_payload.get("unresolved_count") or 0)
            )
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(json.dumps(payload), encoding="utf-8")
            return 0

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "autonomy.json"
            args = make_args(
                output=str(output_path),
                packet_out=str(Path(tmp_dir) / "packets"),
                queue_out=str(Path(tmp_dir) / "queue"),
                dry_run=True,
            )
            with patch(
                "dev.scripts.devctl.commands.autonomy_loop_rounds.triage_loop_command.run",
                side_effect=triage_side_effect,
            ), patch(
                "dev.scripts.devctl.commands.autonomy_loop_rounds.loop_packet_command.run",
                side_effect=packet_side_effect,
            ):
                rc = autonomy_loop.run(args)

            self.assertEqual(rc, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(report["ok"])
            self.assertTrue(report["resolved"])
            self.assertEqual(report["rounds_completed"], 2)
            self.assertEqual(report["tasks_completed"], 2)
            self.assertTrue(report["latest_packet"])
            self.assertIn("phone_status_latest_json", report)
            self.assertIn("phone_status_latest_md", report)

            inbox_dir = Path(report["queue_root"]) / "inbox"
            self.assertTrue(inbox_dir.exists())
            inbox_files = list(inbox_dir.glob("*.json"))
            self.assertGreaterEqual(len(inbox_files), 2)

            latest_phone_json = Path(report["phone_status_latest_json"])
            latest_phone_md = Path(report["phone_status_latest_md"])
            self.assertTrue(latest_phone_json.exists())
            self.assertTrue(latest_phone_md.exists())
            phone_payload = json.loads(latest_phone_json.read_text(encoding="utf-8"))
            self.assertEqual(phone_payload["command"], "autonomy-phone-status")
            self.assertEqual(
                phone_payload["controller"]["controller_run_id"],
                report["controller_run_id"],
            )
            self.assertIn("Loop feedback packet", phone_payload["terminal"]["draft_text"])
            self.assertGreaterEqual(len(phone_payload["terminal"]["trace"]), 1)

            first_round_phone = Path(report["rounds"][0]["phone_status_json"])
            self.assertTrue(first_round_phone.exists())

    @patch("dev.scripts.devctl.commands.autonomy_loop.resolve_repo", return_value="owner/repo")
    @patch("dev.scripts.devctl.commands.autonomy_loop._load_policy", return_value={})
    def test_non_operate_mode_forces_report_only(
        self,
        _policy_mock,
        _resolve_repo_mock,
    ) -> None:
        observed_modes: list[str] = []

        def triage_side_effect(args) -> int:
            observed_modes.append(args.mode)
            payload = _triage_payload(
                mode=args.mode,
                unresolved_count=0,
                reason="resolved",
                attempt=1,
            )
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(json.dumps(payload), encoding="utf-8")
            return 0

        def packet_side_effect(args) -> int:
            payload = _loop_packet_payload(unresolved_count=0)
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(json.dumps(payload), encoding="utf-8")
            return 0

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "autonomy.json"
            args = make_args(
                mode="fix-only",
                output=str(output_path),
                packet_out=str(Path(tmp_dir) / "packets"),
                queue_out=str(Path(tmp_dir) / "queue"),
                dry_run=True,
            )
            with patch.dict(os.environ, {"AUTONOMY_MODE": "read-only"}, clear=False), patch(
                "dev.scripts.devctl.commands.autonomy_loop_rounds.triage_loop_command.run",
                side_effect=triage_side_effect,
            ), patch(
                "dev.scripts.devctl.commands.autonomy_loop_rounds.loop_packet_command.run",
                side_effect=packet_side_effect,
            ):
                rc = autonomy_loop.run(args)

            self.assertEqual(rc, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["mode_effective"], "report-only")
            self.assertTrue(any("AUTONOMY_MODE" in row for row in report.get("warnings", [])))
            self.assertEqual(observed_modes, ["report-only"])

    @patch("dev.scripts.devctl.commands.autonomy_loop.resolve_repo", return_value="owner/repo")
    @patch("dev.scripts.devctl.commands.autonomy_loop._load_policy", return_value={})
    def test_non_operate_mode_denies_non_dry_run(
        self,
        _policy_mock,
        _resolve_repo_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "autonomy.json"
            args = make_args(
                mode="fix-only",
                dry_run=False,
                output=str(output_path),
                packet_out=str(Path(tmp_dir) / "packets"),
                queue_out=str(Path(tmp_dir) / "queue"),
            )
            with patch.dict(os.environ, {"AUTONOMY_MODE": "read-only"}, clear=False):
                rc = autonomy_loop.run(args)

            self.assertEqual(rc, 1)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertEqual(report["reason"], "policy_denied")
            self.assertTrue(any("AUTONOMY_MODE" in row for row in report.get("errors", [])))

    @patch("dev.scripts.devctl.commands.autonomy_loop.resolve_repo", return_value="owner/repo")
    @patch(
        "dev.scripts.devctl.commands.autonomy_loop._load_policy",
        return_value={"autonomy_loop": {"allowed_branches": ["develop"]}},
    )
    def test_policy_denial_for_disallowed_branch(
        self,
        _policy_mock,
        _resolve_repo_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "autonomy.json"
            args = make_args(
                branch_base="master",
                output=str(output_path),
                packet_out=str(Path(tmp_dir) / "packets"),
                queue_out=str(Path(tmp_dir) / "queue"),
            )
            rc = autonomy_loop.run(args)

            self.assertEqual(rc, 1)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertEqual(report["reason"], "policy_denied")


if __name__ == "__main__":
    unittest.main()
