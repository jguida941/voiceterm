"""Tests for devctl report command output."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands import report


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
        args = SimpleNamespace(
            ci=False,
            ci_limit=5,
            dev_logs=True,
            dev_root=None,
            dev_sessions_limit=5,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = report.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- Dev logs root: /tmp/dev", output)
        self.assertIn("- Dev sessions scanned: 1/3", output)
        self.assertIn("- Dev avg latency: unknown", output)
        self.assertIn("- Dev parse errors: 1", output)


if __name__ == "__main__":
    unittest.main()
