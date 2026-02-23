"""Tests for devctl cihub-setup command behavior."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import cihub_setup


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "steps": ["detect", "init", "update", "validate"],
        "cihub_bin": "cihub",
        "repo": None,
        "apply": False,
        "strict_capabilities": False,
        "yes": False,
        "dry_run": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class CIHubSetupCommandTests(unittest.TestCase):
    def test_cli_accepts_cihub_setup_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "cihub-setup",
                "--steps",
                "detect",
                "validate",
                "--repo",
                "owner/repo",
                "--apply",
                "--strict-capabilities",
                "--yes",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "cihub-setup")
        self.assertEqual(args.steps, ["detect", "validate"])
        self.assertEqual(args.repo, "owner/repo")
        self.assertTrue(args.apply)
        self.assertTrue(args.strict_capabilities)
        self.assertTrue(args.yes)

    @patch("dev.scripts.devctl.commands.cihub_setup.write_output")
    @patch("dev.scripts.devctl.commands.cihub_setup.run_cmd")
    @patch("dev.scripts.devctl.commands.cihub_setup._probe_capabilities")
    def test_preview_mode_reports_allowlisted_plan_without_running_commands(
        self,
        probe_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        probe_mock.return_value = {
            "available": True,
            "probe": "parsed-braces",
            "error": None,
            "commands": ["detect", "init", "update", "validate"],
        }

        rc = cihub_setup.run(make_args(apply=False, format="json"))

        self.assertEqual(rc, 0)
        run_cmd_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["mode"], "preview")
        self.assertEqual(len(payload["steps"]), 4)

    @patch("dev.scripts.devctl.commands.cihub_setup.write_output")
    @patch("dev.scripts.devctl.commands.cihub_setup._probe_capabilities")
    def test_strict_capabilities_fails_when_requested_step_is_unsupported(
        self,
        probe_mock,
        write_output_mock,
    ) -> None:
        probe_mock.return_value = {
            "available": True,
            "probe": "parsed-braces",
            "error": None,
            "commands": ["detect"],
        }

        rc = cihub_setup.run(
            make_args(
                steps=["detect", "init"],
                strict_capabilities=True,
                format="json",
            )
        )

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["errors"])

    @patch("dev.scripts.devctl.commands.cihub_setup.write_output")
    @patch("dev.scripts.devctl.commands.cihub_setup.confirm_or_abort")
    @patch("dev.scripts.devctl.commands.cihub_setup.run_cmd")
    @patch("dev.scripts.devctl.commands.cihub_setup._probe_capabilities")
    def test_apply_mode_runs_supported_steps(
        self,
        probe_mock,
        run_cmd_mock,
        confirm_mock,
        write_output_mock,
    ) -> None:
        probe_mock.return_value = {
            "available": True,
            "probe": "parsed-braces",
            "error": None,
            "commands": ["detect", "init"],
        }
        run_cmd_mock.return_value = {
            "name": "cihub-detect",
            "cmd": ["cihub", "detect", "--repo", "owner/repo"],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.01,
            "skipped": False,
        }

        rc = cihub_setup.run(
            make_args(
                apply=True,
                yes=True,
                repo="owner/repo",
                steps=["detect", "init"],
                format="json",
            )
        )

        self.assertEqual(rc, 0)
        confirm_mock.assert_called_once()
        self.assertEqual(run_cmd_mock.call_count, 2)
        first_cmd = run_cmd_mock.call_args_list[0].args[1]
        self.assertEqual(first_cmd, ["cihub", "detect", "--repo", "owner/repo"])
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
