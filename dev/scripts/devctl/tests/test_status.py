"""Tests for devctl status command output and CI error behavior."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import status


def make_args(**overrides) -> SimpleNamespace:
    """Build a default status args namespace with optional overrides."""
    defaults = dict(
        ci=False,
        ci_limit=10,
        require_ci=False,
        dev_logs=False,
        dev_root=None,
        dev_sessions_limit=5,
        probe_report=False,
        quality_policy=None,
        no_parallel=False,
        format="md",
        output=None,
        pipe_command=None,
        pipe_args=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class StatusCommandTests(unittest.TestCase):
    """Validate status command markdown and CI guard behavior."""

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.build_project_report")
    def test_markdown_includes_ci_runs(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {
                "branch": "develop",
                "changelog_updated": True,
                "master_plan_updated": False,
                "changes": [{"status": "M", "path": "README.md"}],
            },
            "mutants": {"results": {}},
            "ci": {
                "runs": [
                    {
                        "displayTitle": "rust_ci",
                        "status": "completed",
                        "conclusion": "success",
                    }
                ]
            },
        }
        args = make_args(ci=True)

        code = status.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- CI runs: 1", output)
        self.assertIn("rust_ci: completed/success", output)

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.build_project_report")
    def test_require_ci_fails_when_ci_fetch_errors(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "ci": {"error": "gh not found"},
        }
        args = make_args(require_ci=True)

        code = status.run(args)

        self.assertEqual(code, 2)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- CI: error (gh not found)", output)

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.build_project_report")
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
            },
        }
        args = make_args(dev_logs=True)

        code = status.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- Dev logs root: /tmp/dev", output)
        self.assertIn("- Dev sessions scanned: 2/4", output)
        self.assertIn("- Dev avg latency: 210 ms", output)

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.build_project_report")
    def test_markdown_includes_probe_report_summary(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "probe_report": {
                "ok": True,
                "mode": "working-tree",
                "summary": {
                    "probe_count": 3,
                    "files_scanned": 12,
                    "files_with_hints": 2,
                    "risk_hints": 4,
                    "priority_hotspots": [
                        {
                            "file": "rust/src/bin/voiceterm/main.rs",
                            "priority_score": 144,
                        }
                    ],
                    "topology": {
                        "edge_count": 22,
                        "changed_hint_files": 1,
                    },
                    "top_files": [
                        {
                            "file": "rust/src/bin/voiceterm/main.rs",
                            "hint_count": 2,
                        }
                    ],
                },
                "warnings": [],
                "errors": [],
            },
        }
        args = make_args(probe_report=True)

        code = status.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("## Review Probes", output)
        self.assertIn("- probes_run: 3", output)
        self.assertIn("main.rs=2", output)
        self.assertIn("priority_hotspots: rust/src/bin/voiceterm/main.rs=144", output)
        self.assertIn("- topology_edges: 22", output)

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.build_project_report")
    def test_markdown_reports_mutation_unavailable_as_note(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {
                "results": {
                    "score": None,
                    "outcomes_path": "rust/mutants.out/outcomes.json",
                    "outcomes_updated_at": "unknown",
                    "outcomes_age_hours": None,
                },
                "warning": "No results found under rust/mutants.out",
            },
        }
        args = make_args()

        code = status.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- Mutation score: unknown", output)
        self.assertIn(
            "- Mutation score note: No results found under rust/mutants.out", output
        )

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.build_project_report")
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

        status.run(args)

        call_kwargs = mock_build_report.call_args.kwargs
        self.assertTrue(call_kwargs["parallel"])

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.build_project_report")
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

        status.run(args)

        call_kwargs = mock_build_report.call_args.kwargs
        self.assertFalse(call_kwargs["parallel"])

    def test_cli_accepts_probe_report_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["status", "--probe-report"])
        self.assertTrue(args.probe_report)

    def test_cli_accepts_quality_policy_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["status", "--quality-policy", "/tmp/policy.json"])
        self.assertEqual(args.quality_policy, "/tmp/policy.json")

    @patch("dev.scripts.devctl.commands.status.write_output")
    @patch("dev.scripts.devctl.commands.status.build_project_report")
    def test_quality_policy_flag_is_forwarded(
        self,
        mock_build_report,
        _mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
        }

        status.run(make_args(probe_report=True, quality_policy="/tmp/policy.json"))

        call_kwargs = mock_build_report.call_args.kwargs
        self.assertEqual(call_kwargs["probe_policy_path"], "/tmp/policy.json")


if __name__ == "__main__":
    unittest.main()
