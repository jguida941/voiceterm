"""Tests for devctl controller-action parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import controller_action


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "action": "refresh-status",
        "repo": "owner/repo",
        "branch": "develop",
        "workflow": ".github/workflows/coderabbit_ralph_loop.yml",
        "max_attempts": 3,
        "phone_json": "dev/reports/autonomy/queue/phone/latest.json",
        "view": "compact",
        "mode_file": "dev/reports/autonomy/queue/phone/controller_mode.json",
        "remote": True,
        "dry_run": False,
        "format": "json",
        "output": None,
        "json_output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class ControllerActionParserTests(unittest.TestCase):
    def test_cli_accepts_controller_action_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "controller-action",
                "--action",
                "dispatch-report-only",
                "--repo",
                "owner/repo",
                "--branch",
                "develop",
                "--workflow",
                ".github/workflows/coderabbit_ralph_loop.yml",
                "--max-attempts",
                "4",
                "--dry-run",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "controller-action")
        self.assertEqual(args.action, "dispatch-report-only")
        self.assertEqual(args.max_attempts, 4)
        self.assertTrue(args.dry_run)


class ControllerActionCommandTests(unittest.TestCase):
    @patch(
        "dev.scripts.devctl.commands.controller_action.resolve_repo",
        return_value="owner/repo",
    )
    @patch("dev.scripts.devctl.commands.controller_action.write_output")
    def test_refresh_status_reads_phone_payload(
        self,
        write_output_mock,
        _resolve_repo_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            phone_json = Path(tmp_dir) / "latest.json"
            phone_json.write_text(
                json.dumps(
                    {
                        "phase": "paused",
                        "reason": "max_rounds_reached",
                        "controller": {"controller_run_id": "abc123"},
                        "loop": {"unresolved_count": 0, "risk": "low"},
                        "terminal": {"trace": ["line1"], "draft_text": "draft"},
                    }
                ),
                encoding="utf-8",
            )
            args = make_args(action="refresh-status", phone_json=str(phone_json))
            rc = controller_action.run(args)
            self.assertEqual(rc, 0)
            payload = json.loads(write_output_mock.call_args.args[0])
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["reason"], "status_refreshed")
            self.assertEqual(payload["result"]["view"], "compact")

    @patch(
        "dev.scripts.devctl.commands.controller_action.resolve_repo",
        return_value="owner/repo",
    )
    @patch("dev.scripts.devctl.commands.controller_action.write_output")
    def test_dispatch_rejects_non_allowlisted_workflow(
        self,
        write_output_mock,
        _resolve_repo_mock,
    ) -> None:
        args = make_args(
            action="dispatch-report-only",
            workflow=".github/workflows/not-allowed.yml",
            dry_run=True,
        )
        rc = controller_action.run(args)
        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["reason"], "workflow_not_allowlisted")

    @patch(
        "dev.scripts.devctl.commands.controller_action.load_controller_policy",
        return_value={
            "autonomy_mode_default": "read-only",
            "allowed_workflow_dispatches": [
                ".github/workflows/coderabbit_ralph_loop.yml"
            ],
            "triage_loop": {"allowed_branches": ["develop"]},
        },
    )
    @patch(
        "dev.scripts.devctl.commands.controller_action.resolve_repo",
        return_value="owner/repo",
    )
    @patch("dev.scripts.devctl.commands.controller_action.write_output")
    def test_dispatch_dry_run_succeeds_when_allowlisted(
        self,
        write_output_mock,
        _resolve_repo_mock,
        _load_policy_mock,
    ) -> None:
        args = make_args(action="dispatch-report-only", dry_run=True)
        rc = controller_action.run(args)
        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["reason"], "dispatched_report_only")
        self.assertIn("gh workflow run", payload["result"]["command"])

    @patch(
        "dev.scripts.devctl.commands.controller_action.resolve_repo",
        return_value="owner/repo",
    )
    @patch("dev.scripts.devctl.commands.controller_action.write_output")
    def test_pause_loop_writes_mode_file(
        self,
        write_output_mock,
        _resolve_repo_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            mode_file = Path(tmp_dir) / "controller_mode.json"
            args = make_args(
                action="pause-loop",
                mode_file=str(mode_file),
                remote=False,
                dry_run=True,
            )
            rc = controller_action.run(args)
            self.assertEqual(rc, 0)
            self.assertTrue(mode_file.exists())
            mode_payload = json.loads(mode_file.read_text(encoding="utf-8"))
            self.assertEqual(mode_payload["requested_mode"], "read-only")
            payload = json.loads(write_output_mock.call_args.args[0])
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["reason"], "mode_updated")


if __name__ == "__main__":
    unittest.main()
