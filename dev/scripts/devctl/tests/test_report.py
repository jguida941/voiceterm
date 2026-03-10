"""Tests for devctl report command output."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import report


def make_args(**overrides) -> SimpleNamespace:
    """Build a default report args namespace with optional overrides."""
    defaults = dict(
        ci=False,
        ci_limit=5,
        dev_logs=False,
        dev_root=None,
        dev_sessions_limit=5,
        pedantic=False,
        pedantic_refresh=False,
        pedantic_summary_json=None,
        pedantic_lints_json=None,
        pedantic_policy_file=None,
        rust_audits=False,
        rust_audit_mode="auto",
        since_ref=None,
        head_ref="HEAD",
        with_charts=False,
        chart_dir=None,
        emit_bundle=False,
        bundle_dir="dev/reports/report",
        bundle_prefix="devctl-report",
        quality_backlog=False,
        quality_backlog_top_n=40,
        quality_backlog_include_tests=False,
        python_guard_backlog=False,
        python_guard_backlog_top_n=20,
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

    def test_cli_accepts_pedantic_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "report",
                "--pedantic",
                "--pedantic-refresh",
                "--pedantic-summary-json",
                "/tmp/pedantic-summary.json",
                "--pedantic-lints-json",
                "/tmp/pedantic-lints.json",
                "--pedantic-policy-file",
                "/tmp/pedantic-policy.json",
            ]
        )
        self.assertTrue(args.pedantic)
        self.assertTrue(args.pedantic_refresh)
        self.assertEqual(args.pedantic_summary_json, "/tmp/pedantic-summary.json")
        self.assertEqual(args.pedantic_lints_json, "/tmp/pedantic-lints.json")
        self.assertEqual(args.pedantic_policy_file, "/tmp/pedantic-policy.json")

    def test_cli_accepts_rust_audit_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "report",
                "--rust-audits",
                "--rust-audit-mode",
                "commit-range",
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD~1",
                "--with-charts",
                "--chart-dir",
                "/tmp/rust-audit-charts",
                "--emit-bundle",
                "--bundle-dir",
                "/tmp/rust-audit-bundle",
                "--bundle-prefix",
                "rust-audit",
            ]
        )
        self.assertTrue(args.rust_audits)
        self.assertEqual(args.rust_audit_mode, "commit-range")
        self.assertEqual(args.since_ref, "origin/develop")
        self.assertEqual(args.head_ref, "HEAD~1")
        self.assertTrue(args.with_charts)
        self.assertEqual(args.chart_dir, "/tmp/rust-audit-charts")
        self.assertTrue(args.emit_bundle)
        self.assertEqual(args.bundle_dir, "/tmp/rust-audit-bundle")
        self.assertEqual(args.bundle_prefix, "rust-audit")

    def test_cli_accepts_quality_backlog_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "report",
                "--quality-backlog",
                "--quality-backlog-top-n",
                "25",
                "--quality-backlog-include-tests",
            ]
        )
        self.assertTrue(args.quality_backlog)
        self.assertEqual(args.quality_backlog_top_n, 25)
        self.assertTrue(args.quality_backlog_include_tests)

    def test_cli_accepts_python_guard_backlog_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "report",
                "--python-guard-backlog",
                "--python-guard-backlog-top-n",
                "15",
            ]
        )
        self.assertTrue(args.python_guard_backlog)
        self.assertEqual(args.python_guard_backlog_top_n, 15)

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
    def test_markdown_includes_pedantic_summary(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "pedantic": {
                "artifact_found": True,
                "observed_lints": 3,
                "warnings": 12,
                "exit_code": 101,
                "status": "failure",
                "reviewed_lints": 2,
                "unreviewed_lints": 1,
                "top_promote_candidates": [
                    {"lint": "clippy::redundant_else", "count": 4},
                ],
            },
        }
        args = make_args(pedantic=True)

        code = report.run(args)

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("- Pedantic advisory: 3 lint ids / 12 warnings", output)
        self.assertIn(
            "- Pedantic advisory note: last sweep failed (status=failure, exit=101)",
            output,
        )
        self.assertIn("- Pedantic policy coverage: reviewed=2, unreviewed=1", output)
        self.assertIn(
            "- Pedantic promote candidates: clippy::redundant_else=4",
            output,
        )

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_markdown_includes_rust_audit_summary(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "rust_audits": {
                "mode": "absolute",
                "ok": False,
                "summary": {
                    "total_violation_files": 2,
                    "total_active_findings": 5,
                    "active_categories": 2,
                    "dead_code_without_reason_count": 1,
                },
                "guards": [
                    {
                        "guard": "best_practices",
                        "ok": False,
                        "files_considered": 10,
                        "violations": 2,
                    }
                ],
                "categories": [
                    {
                        "label": "dropped send results",
                        "count": 3,
                        "severity": "high",
                        "why": "Signals can be lost silently.",
                        "fix": "Handle send failures explicitly.",
                    }
                ],
                "hotspots": [
                    {
                        "path": "rust/src/bin/voiceterm/dev_command/broker/mod.rs",
                        "score": 9,
                        "count": 3,
                        "signals": ["dropped send results"],
                    }
                ],
                "warnings": [],
                "errors": [],
                "charts": [],
            },
        }

        code = report.run(make_args(rust_audits=True))

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("## Rust Audit", output)
        self.assertIn("- Audit mode: absolute", output)
        self.assertIn("dropped send results", output)
        self.assertIn("broker/mod.rs", output)

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_markdown_includes_quality_backlog_summary(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "quality_backlog": {
                "ok": False,
                "summary": {
                    "source_files_scanned": 100,
                    "guard_failures": 2,
                    "critical_paths": 1,
                    "high_paths": 2,
                    "medium_paths": 3,
                    "low_paths": 4,
                    "ranked_paths": 10,
                },
                "priorities": [
                    {
                        "path": "rust/src/bin/voiceterm/dev_panel/review_surface.rs",
                        "score": 720,
                        "severity": "critical",
                        "signals": ["shape:hard", "code_shape:absolute_hard_limit_exceeded"],
                    }
                ],
            },
        }

        code = report.run(make_args(quality_backlog=True))

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("## Quality Backlog", output)
        self.assertIn("source_files_scanned: 100", output)
        self.assertIn("severities: critical=1", output)
        self.assertIn("review_surface.rs", output)

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_markdown_includes_python_guard_backlog_summary(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "python_guard_backlog": {
                "mode": "working-tree",
                "ok": False,
                "summary": {
                    "guard_count": 5,
                    "guard_failures": 2,
                    "active_paths": 3,
                    "total_active_findings": 9,
                    "top_risk_score": 710,
                },
                "hotspots": [
                    {
                        "path": "app/operator_console/views/main_window.py",
                        "score": 710,
                        "count": 4,
                        "guard_count": 2,
                    }
                ],
            },
        }

        code = report.run(make_args(python_guard_backlog=True))

        self.assertEqual(code, 0)
        output = mock_write_output.call_args.args[0]
        self.assertIn("## Python Guard Backlog", output)
        self.assertIn("- guard_failures: 2", output)
        self.assertIn("main_window.py: score=710", output)

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
        self.assertFalse(call_kwargs["include_pedantic"])
        self.assertFalse(call_kwargs["include_rust_audits"])

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

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_pedantic_flags_forwarded_to_build_report(
        self,
        mock_build_report,
        mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
        }
        args = make_args(
            pedantic=True,
            pedantic_summary_json="/tmp/pedantic-summary.json",
            pedantic_lints_json="/tmp/pedantic-lints.json",
            pedantic_policy_file="/tmp/pedantic-policy.json",
        )

        report.run(args)

        call_kwargs = mock_build_report.call_args.kwargs
        self.assertTrue(call_kwargs["include_pedantic"])
        self.assertEqual(
            call_kwargs["pedantic_summary_path"], "/tmp/pedantic-summary.json"
        )
        self.assertEqual(
            call_kwargs["pedantic_lints_path"], "/tmp/pedantic-lints.json"
        )
        self.assertEqual(
            call_kwargs["pedantic_policy_path"], "/tmp/pedantic-policy.json"
        )

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_rust_audit_flags_forwarded_to_build_report(
        self,
        mock_build_report,
        _mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
        }

        report.run(
            make_args(
                rust_audits=True,
                rust_audit_mode="commit-range",
                since_ref="origin/develop",
                head_ref="HEAD~1",
            )
        )

        call_kwargs = mock_build_report.call_args.kwargs
        self.assertTrue(call_kwargs["include_rust_audits"])
        self.assertEqual(call_kwargs["rust_audit_mode"], "commit-range")
        self.assertEqual(call_kwargs["rust_audit_since_ref"], "origin/develop")
        self.assertEqual(call_kwargs["rust_audit_head_ref"], "HEAD~1")

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_quality_backlog_flags_forwarded_to_build_report(
        self,
        mock_build_report,
        _mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
        }
        report.run(
            make_args(
                quality_backlog=True,
                quality_backlog_top_n=12,
                quality_backlog_include_tests=True,
            )
        )
        call_kwargs = mock_build_report.call_args.kwargs
        self.assertTrue(call_kwargs["include_quality_backlog"])
        self.assertEqual(call_kwargs["quality_backlog_top_n"], 12)
        self.assertTrue(call_kwargs["quality_backlog_include_tests"])

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_python_guard_backlog_flags_forwarded_to_build_report(
        self,
        mock_build_report,
        _mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
        }
        report.run(
            make_args(
                python_guard_backlog=True,
                python_guard_backlog_top_n=9,
                since_ref="origin/develop",
                head_ref="HEAD~1",
            )
        )
        call_kwargs = mock_build_report.call_args.kwargs
        self.assertTrue(call_kwargs["include_python_guard_backlog"])
        self.assertEqual(call_kwargs["python_guard_backlog_top_n"], 9)
        self.assertEqual(call_kwargs["python_guard_since_ref"], "origin/develop")
        self.assertEqual(call_kwargs["python_guard_head_ref"], "HEAD~1")

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.run_cmd")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_pedantic_refresh_runs_collector_before_report(
        self,
        mock_build_report,
        mock_run_cmd,
        _mock_write_output,
    ) -> None:
        mock_run_cmd.return_value = {
            "name": "pedantic-refresh",
            "returncode": 1,
            "skipped": False,
        }
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "pedantic": {"artifact_found": True},
        }

        report.run(
            make_args(
                pedantic=True,
                pedantic_refresh=True,
                pedantic_summary_json="/tmp/pedantic-summary.json",
                pedantic_lints_json="/tmp/pedantic-lints.json",
            )
        )

        mock_run_cmd.assert_called_once()
        refresh_cmd = mock_run_cmd.call_args.args[1]
        self.assertIn("/tmp/pedantic-summary.json", refresh_cmd)
        self.assertIn("/tmp/pedantic-lints.json", refresh_cmd)
        self.assertEqual(
            mock_build_report.return_value["pedantic"]["refresh"]["name"],
            "pedantic-refresh",
        )

    @patch("dev.scripts.devctl.commands.report.write_output")
    @patch("dev.scripts.devctl.commands.report.build_rust_audit_charts")
    @patch("dev.scripts.devctl.commands.report.build_project_report")
    def test_emit_bundle_writes_markdown_and_json(
        self,
        mock_build_report,
        mock_build_charts,
        _mock_write_output,
    ) -> None:
        mock_build_report.return_value = {
            "git": {"branch": "develop", "changes": []},
            "mutants": {"results": {}},
            "rust_audits": {
                "mode": "absolute",
                "ok": True,
                "summary": {
                    "total_violation_files": 0,
                    "total_active_findings": 0,
                    "active_categories": 0,
                    "dead_code_without_reason_count": 0,
                },
                "guards": [],
                "categories": [],
                "hotspots": [],
                "warnings": [],
                "errors": [],
                "charts": [],
            },
        }
        mock_build_charts.return_value = (["/tmp/chart.png"], None)
        with tempfile.TemporaryDirectory() as tmpdir:
            args = make_args(
                rust_audits=True,
                with_charts=True,
                emit_bundle=True,
                bundle_dir=tmpdir,
                bundle_prefix="rust-audit",
            )

            code = report.run(args)

            self.assertEqual(code, 0)
            md_path = Path(tmpdir) / "rust-audit.md"
            json_path = Path(tmpdir) / "rust-audit.json"
            self.assertTrue(md_path.exists())
            self.assertTrue(json_path.exists())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["bundle"]["markdown_path"], str(md_path))
            self.assertEqual(
                payload["rust_audits"]["charts"], ["/tmp/chart.png"]
            )


if __name__ == "__main__":
    unittest.main()
