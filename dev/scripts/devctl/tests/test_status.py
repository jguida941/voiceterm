"""Tests for devctl status command output and CI error behavior."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import status


class StatusCommandTests(unittest.TestCase):
    """Validate status command markdown and CI guard behavior."""

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.collect_dev_log_summary")
    @patch("dev.scripts.devctl.commands.status.collect_ci_runs")
    @patch("dev.scripts.devctl.commands.status.collect_mutation_summary")
    @patch("dev.scripts.devctl.commands.status.collect_git_status")
    def test_markdown_includes_ci_runs(
        self,
        mock_git,
        mock_mutants,
        mock_ci,
        mock_dev_logs,
        mock_write_output,
    ) -> None:
        mock_git.return_value = {
            "branch": "develop",
            "changelog_updated": True,
            "master_plan_updated": False,
            "changes": [{"status": "M", "path": "README.md"}],
        }
        mock_mutants.return_value = {"results": []}
        mock_ci.return_value = {
            "runs": [
                {
                    "displayTitle": "rust_ci",
                    "status": "completed",
                    "conclusion": "success",
                }
            ]
        }
        mock_dev_logs.return_value = {}
        args = SimpleNamespace(
            ci=True,
            ci_limit=10,
            require_ci=False,
            dev_logs=False,
            dev_root=None,
            dev_sessions_limit=5,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = status.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- CI runs: 1", output)
        self.assertIn("rust_ci: completed/success", output)

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.collect_dev_log_summary")
    @patch("dev.scripts.devctl.commands.status.collect_ci_runs")
    @patch("dev.scripts.devctl.commands.status.collect_mutation_summary")
    @patch("dev.scripts.devctl.commands.status.collect_git_status")
    def test_require_ci_fails_when_ci_fetch_errors(
        self,
        mock_git,
        mock_mutants,
        mock_ci,
        mock_dev_logs,
        mock_write_output,
    ) -> None:
        mock_git.return_value = {"branch": "develop", "changes": []}
        mock_mutants.return_value = {"results": []}
        mock_ci.return_value = {"error": "gh not found"}
        mock_dev_logs.return_value = {}
        args = SimpleNamespace(
            ci=False,
            ci_limit=10,
            require_ci=True,
            dev_logs=False,
            dev_root=None,
            dev_sessions_limit=5,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = status.run(args)

        self.assertEqual(code, 2)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- CI: error (gh not found)", output)

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.collect_dev_log_summary")
    @patch("dev.scripts.devctl.commands.status.collect_mutation_summary")
    @patch("dev.scripts.devctl.commands.status.collect_git_status")
    def test_markdown_includes_dev_log_summary(
        self,
        mock_git,
        mock_mutants,
        mock_dev_logs,
        mock_write_output,
    ) -> None:
        mock_git.return_value = {"branch": "develop", "changes": []}
        mock_mutants.return_value = {"results": []}
        mock_dev_logs.return_value = {
            "dev_root": "/tmp/dev",
            "sessions_scanned": 2,
            "session_files_total": 4,
            "events_scanned": 9,
            "transcript_events": 5,
            "empty_events": 3,
            "error_events": 1,
            "total_words": 42,
            "avg_latency_ms": 210,
            "parse_errors": 0,
            "latest_event_iso": "2026-02-23T00:00:00+00:00",
        }
        args = SimpleNamespace(
            ci=False,
            ci_limit=10,
            require_ci=False,
            dev_logs=True,
            dev_root=None,
            dev_sessions_limit=5,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = status.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- Dev logs root: /tmp/dev", output)
        self.assertIn("- Dev sessions scanned: 2/4", output)
        self.assertIn("- Dev avg latency: 210 ms", output)


if __name__ == "__main__":
    unittest.main()
