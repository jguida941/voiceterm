"""Tests for devctl report command output."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import report


def make_args(**overrides) -> SimpleNamespace:
    """Build a default report args namespace with optional overrides."""
    defaults = dict(
        ci=False,
        ci_limit=5,
        dev_logs=False,
        dev_root=None,
        dev_sessions_limit=5,
        no_parallel=False,
        format="md",
        output=None,
        pipe_command=None,
        pipe_args=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class ReportCommandTests(unittest.TestCase):
    """Validate report command markdown output."""

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_markdown_includes_dev_log_summary(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "dev_logs": {
                "dev_root": "/tmp/dev",
                "sessions_scanned": 1,
                "session_files_total": 3,
                "events_scanned": 4,
                "transcript_events": 2,
                "empty_events": 1,
                "error_events": 1,
                "total_words": 7,
                "avg_latency_ms": None,
                "parse_errors": 1,
                "latest_event_iso": None,
            },
        }
        args = make_args(dev_logs=True)

        code = report.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- Dev logs root: /tmp/dev", output)
        self.assertIn("- Dev sessions scanned: 1/3", output)
        self.assertIn("- Dev avg latency: unknown", output)
        self.assertIn("- Dev parse errors: 1", output)

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_parallel_flag_forwarded_to_build_report(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        """Verify that parallel=True is passed when --no-parallel is absent."""
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
        }
        args = make_args()

        report.run(args)

        call_kwargs = mock_build_report.call_args.kwargs
        self.assertTrue(call_kwargs["parallel"])

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_no_parallel_flag_disables_parallel(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        """Verify that parallel=False is passed when --no-parallel is set."""
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
        }
        args = make_args(no_parallel=True)

        report.run(args)

        call_kwargs = mock_build_report.call_args.kwargs
        self.assertFalse(call_kwargs["parallel"])


if __name__ == "__main__":
    unittest.main()
