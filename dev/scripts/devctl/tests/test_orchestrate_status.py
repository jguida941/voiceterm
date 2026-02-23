"""Tests for devctl orchestrate-status command wiring and output."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import orchestrate_status


class OrchestrateStatusParserTests(unittest.TestCase):
    def test_cli_accepts_orchestrate_status_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "orchestrate-status",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "orchestrate-status")
        self.assertEqual(args.format, "json")

    def test_cli_accepts_orchestrate_watch_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "orchestrate-watch",
                "--stale-minutes",
                "45",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "orchestrate-watch")
        self.assertEqual(args.stale_minutes, 45)
        self.assertEqual(args.format, "json")


class OrchestrateStatusCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.orchestrate_status.write_output")
    @patch(
        "dev.scripts.devctl.commands.orchestrate_status._run_multi_agent_sync_gate",
        return_value={"ok": True, "errors": [], "warnings": []},
    )
    @patch(
        "dev.scripts.devctl.commands.orchestrate_status._run_active_plan_sync_gate",
        return_value={"ok": True, "errors": []},
    )
    @patch("dev.scripts.devctl.commands.orchestrate_status.collect_git_status")
    def test_orchestrate_status_passes_when_all_gates_pass(
        self,
        mock_collect_git_status,
        _mock_active,
        _mock_multi,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "branch": "develop",
            "changes": [{"status": "M", "path": "dev/active/MASTER_PLAN.md"}],
        }
        args = SimpleNamespace(
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = orchestrate_status.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- ok: True", output)
        self.assertIn("- active_plan_sync_ok: True", output)
        self.assertIn("- multi_agent_sync_ok: True", output)

    @patch("dev.scripts.devctl.commands.orchestrate_status.write_output")
    @patch(
        "dev.scripts.devctl.commands.orchestrate_status._run_multi_agent_sync_gate",
        return_value={"ok": False, "errors": ["AGENT-2 mismatch"], "warnings": []},
    )
    @patch(
        "dev.scripts.devctl.commands.orchestrate_status._run_active_plan_sync_gate",
        return_value={"ok": True, "errors": []},
    )
    @patch("dev.scripts.devctl.commands.orchestrate_status.collect_git_status")
    def test_orchestrate_status_fails_when_multi_agent_sync_fails(
        self,
        mock_collect_git_status,
        _mock_active,
        _mock_multi,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"branch": "develop", "changes": []}
        args = SimpleNamespace(
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = orchestrate_status.run(args)

        self.assertEqual(code, 1)
        output = mock_write_output.call_args.args[0]
        self.assertIn("multi-agent-sync: AGENT-2 mismatch", output)

    @patch("dev.scripts.devctl.commands.orchestrate_status.write_output")
    @patch(
        "dev.scripts.devctl.commands.orchestrate_status._run_multi_agent_sync_gate",
        return_value={"ok": True, "errors": [], "warnings": []},
    )
    @patch(
        "dev.scripts.devctl.commands.orchestrate_status._run_active_plan_sync_gate",
        return_value={"ok": True, "errors": []},
    )
    @patch("dev.scripts.devctl.commands.orchestrate_status.collect_git_status")
    def test_orchestrate_status_json_includes_git_error(
        self,
        mock_collect_git_status,
        _mock_active,
        _mock_multi,
        mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"error": "git not found"}
        args = SimpleNamespace(
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = orchestrate_status.run(args)

        self.assertEqual(code, 1)
        payload = json.loads(mock_write_output.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["git"]["error"], "git not found")
        self.assertIn("git-status: git not found", payload["errors"])


if __name__ == "__main__":
    unittest.main()
