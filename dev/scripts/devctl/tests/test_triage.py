"""Tests for devctl triage command behavior."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import triage
from dev.scripts.devctl.triage import support as triage_support


def make_args(**overrides):
    defaults = {
        "ci": False,
        "ci_limit": 5,
        "dev_logs": False,
        "dev_root": None,
        "dev_sessions_limit": 5,
        "pedantic": False,
        "pedantic_refresh": False,
        "pedantic_summary_json": None,
        "pedantic_lints_json": None,
        "pedantic_policy_file": None,
        "probe_report": False,
        "probe_since_ref": None,
        "probe_head_ref": "HEAD",
        "quality_policy": None,
        "cihub": False,
        "no_cihub": True,
        "require_cihub": False,
        "cihub_bin": "cihub",
        "cihub_latest": True,
        "cihub_run": None,
        "cihub_repo": None,
        "cihub_emit_dir": ".cihub",
        "emit_bundle": False,
        "bundle_dir": ".cihub",
        "bundle_prefix": "devctl-triage",
        "owner_map_file": None,
        "external_issues_file": [],
        "dry_run": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def minimal_project_report() -> dict:
    return {
        "git": {
            "branch": "develop",
            "changes": [],
            "changelog_updated": False,
            "master_plan_updated": False,
        },
        "mutants": {"results": {"score": 82.0}},
    }


class TriageParserTests(unittest.TestCase):
    def test_cli_accepts_triage_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "triage",
                "--ci",
                "--ci-limit",
                "7",
                "--pedantic",
                "--pedantic-refresh",
                "--pedantic-summary-json",
                "/tmp/pedantic-summary.json",
                "--probe-report",
                "--probe-since-ref",
                "origin/develop",
                "--probe-head-ref",
                "HEAD~1",
                "--quality-policy",
                "/tmp/policy.json",
                "--cihub",
                "--cihub-run",
                "123",
                "--cihub-repo",
                "owner/repo",
                "--emit-bundle",
                "--bundle-prefix",
                "my-triage",
                "--owner-map-file",
                "/tmp/owners.json",
                "--external-issues-file",
                "/tmp/external-issues.json",
                "--format",
                "md",
            ]
        )
        self.assertEqual(args.command, "triage")
        self.assertTrue(args.ci)
        self.assertEqual(args.ci_limit, 7)
        self.assertTrue(args.pedantic)
        self.assertTrue(args.pedantic_refresh)
        self.assertEqual(args.pedantic_summary_json, "/tmp/pedantic-summary.json")
        self.assertTrue(args.probe_report)
        self.assertEqual(args.probe_since_ref, "origin/develop")
        self.assertEqual(args.probe_head_ref, "HEAD~1")
        self.assertEqual(args.quality_policy, "/tmp/policy.json")
        self.assertTrue(args.cihub)
        self.assertEqual(args.cihub_run, "123")
        self.assertEqual(args.cihub_repo, "owner/repo")
        self.assertTrue(args.emit_bundle)
        self.assertEqual(args.bundle_prefix, "my-triage")
        self.assertEqual(args.owner_map_file, "/tmp/owners.json")
        self.assertEqual(args.external_issues_file, ["/tmp/external-issues.json"])
        self.assertEqual(args.format, "md")


class TriageCommandTests(unittest.TestCase):
    def test_render_triage_markdown_includes_cihub_and_external_sections(self) -> None:
        markdown = triage_support.render_triage_markdown(
            {
                "timestamp": "2026-03-11T22:00:00Z",
                "issues": [
                    {
                        "severity": "high",
                        "category": "ci",
                        "owner": "operator",
                        "summary": "CI run failed",
                    }
                ],
                "warnings": ["warning"],
                "rollup": {"total": 1, "by_severity": {"high": 1}},
                "project": minimal_project_report(),
                "next_actions": ["Inspect the failing workflow."],
                "cihub": {
                    "enabled": True,
                    "step": {"returncode": 0},
                    "artifacts": {
                        "triage_json_path": "/tmp/triage.json",
                        "priority_json_path": "/tmp/priority.json",
                        "triage_markdown_path": "/tmp/triage.md",
                    },
                },
                "external_inputs": [
                    {"source": "jira", "path": "/tmp/jira.json", "issues": 2}
                ],
                "bundle": {
                    "written": True,
                    "markdown_path": "/tmp/triage.md",
                    "ai_json_path": "/tmp/triage.ai.json",
                },
            }
        )

        self.assertIn("## Project Snapshot", markdown)
        self.assertIn("## CIHub", markdown)
        self.assertIn("- triage_json: /tmp/triage.json", markdown)
        self.assertIn("## External Issue Sources", markdown)
        self.assertIn("- jira: /tmp/jira.json (issues=2)", markdown)
        self.assertIn("## Bundle", markdown)

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_pedantic_snapshot_adds_issues_and_next_action(
        self,
        build_report_mock,
        write_output_mock,
    ) -> None:
        build_report_mock.return_value = {
            **minimal_project_report(),
            "pedantic": {
                "artifact_found": True,
                "issues": [
                    {
                        "category": "quality",
                        "severity": "medium",
                        "source": "devctl.pedantic",
                        "summary": "Pedantic promote candidate `clippy::redundant_else` observed 4 time(s); consider graduating it into `maintainer-lint` after cleanup.",
                    }
                ],
            },
        }
        args = make_args(pedantic=True, format="json")

        rc = triage.run(args)
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(
            any(
                issue["source"] == "devctl.pedantic"
                for issue in payload["issues"]
            )
        )
        self.assertTrue(
            any(
                "check --profile pedantic" in action
                for action in payload["next_actions"]
            )
        )

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.run_cmd")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_pedantic_refresh_runs_collector_before_triage(
        self,
        build_report_mock,
        run_cmd_mock,
        _write_output_mock,
    ) -> None:
        run_cmd_mock.return_value = {
            "name": "pedantic-refresh",
            "returncode": 1,
            "skipped": False,
        }
        build_report_mock.return_value = {
            **minimal_project_report(),
            "pedantic": {
                "artifact_found": True,
                "issues": [],
            },
        }

        triage.run(
            make_args(
                pedantic=True,
                pedantic_refresh=True,
                pedantic_summary_json="/tmp/pedantic-summary.json",
                pedantic_lints_json="/tmp/pedantic-lints.json",
                format="json",
            )
        )

        run_cmd_mock.assert_called_once()
        refresh_cmd = run_cmd_mock.call_args.args[1]
        self.assertIn("/tmp/pedantic-summary.json", refresh_cmd)
        self.assertIn("/tmp/pedantic-lints.json", refresh_cmd)
        self.assertEqual(
            build_report_mock.return_value["pedantic"]["refresh"]["name"],
            "pedantic-refresh",
        )

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_probe_report_is_forwarded_and_generates_triage_actions(
        self,
        build_report_mock,
        write_output_mock,
    ) -> None:
        build_report_mock.return_value = {
            **minimal_project_report(),
            "probe_report": {
                "ok": True,
                "mode": "commit-range",
                "summary": {
                    "probe_count": 13,
                    "files_scanned": 441,
                    "files_with_hints": 14,
                    "risk_hints": 23,
                    "hints_by_severity": {"high": 8, "medium": 14, "low": 1},
                    "priority_hotspots": [
                        {
                            "file": "dev/scripts/devctl/commands/triage.py",
                            "priority_score": 181,
                            "hint_count": 3,
                        }
                    ],
                    "top_files": [
                        {"file": "dev/scripts/devctl/commands/triage.py", "hint_count": 3}
                    ],
                },
                "warnings": [],
                "errors": [],
            },
        }
        args = make_args(
            probe_report=True,
            probe_since_ref="origin/develop",
            probe_head_ref="HEAD~1",
            format="json",
        )

        rc = triage.run(args)
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        summaries = {issue["summary"]: issue for issue in payload["issues"]}
        expected = (
            "Review probes flagged 23 risk hints across 14 file(s) "
            "(high=8, medium=14, low=1). "
            "Top hotspot: dev/scripts/devctl/commands/triage.py (score=181, hints=3)."
        )
        self.assertIn(expected, summaries)
        self.assertEqual(summaries[expected]["severity"], "high")
        self.assertTrue(
            any("probe-report --format md" in action for action in payload["next_actions"])
        )
        self.assertTrue(
            any("triage --probe-report --no-cihub --format md" in action for action in payload["next_actions"])
        )
        call_kwargs = build_report_mock.call_args.kwargs
        self.assertTrue(call_kwargs["include_probe_report"])
        self.assertEqual(call_kwargs["probe_since_ref"], "origin/develop")
        self.assertEqual(call_kwargs["probe_head_ref"], "HEAD~1")
        self.assertIsNone(call_kwargs["probe_policy_path"])

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_quality_policy_flag_is_forwarded(
        self,
        build_report_mock,
        _write_output_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()

        triage.run(make_args(probe_report=True, quality_policy="/tmp/policy.json"))

        call_kwargs = build_report_mock.call_args.kwargs
        self.assertEqual(call_kwargs["probe_policy_path"], "/tmp/policy.json")

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_probe_report_errors_add_infra_issue(
        self,
        build_report_mock,
        write_output_mock,
    ) -> None:
        build_report_mock.return_value = {
            **minimal_project_report(),
            "probe_report": {
                "ok": False,
                "summary": {
                    "probe_count": 11,
                    "files_scanned": 300,
                    "files_with_hints": 0,
                    "risk_hints": 0,
                },
                "warnings": [],
                "errors": ["probe_magic_numbers exited 1"],
            },
        }
        args = make_args(probe_report=True, format="json")

        rc = triage.run(args)
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(
            any(
                issue["summary"] == "Review probe run incomplete: 1 probe error(s)."
                and issue["category"] == "infra"
                for issue in payload["issues"]
            )
        )

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_external_issue_file_is_ingested(
        self,
        build_report_mock,
        write_output_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        with tempfile.TemporaryDirectory() as tmp_dir:
            external_path = Path(tmp_dir) / "external.json"
            external_path.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "category": "security",
                                "severity": "high",
                                "summary": "CodeRabbit flagged unsafe command interpolation",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            args = make_args(
                external_issues_file=[str(external_path)],
                format="json",
            )
            rc = triage.run(args)
            self.assertEqual(rc, 0)

            payload = json.loads(write_output_mock.call_args.args[0])
            summaries = {issue["summary"]: issue for issue in payload["issues"]}
            self.assertIn("CodeRabbit flagged unsafe command interpolation", summaries)
            self.assertEqual(
                summaries["CodeRabbit flagged unsafe command interpolation"][
                    "severity"
                ],
                "high",
            )
            self.assertTrue(payload["external_inputs"])

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_external_issue_file_error_adds_warning_issue(
        self,
        build_report_mock,
        write_output_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        args = make_args(
            external_issues_file=["/tmp/does-not-exist-triage-input.json"],
            format="json",
        )
        rc = triage.run(args)
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(
            any(
                "external issues ingest failed" in warning
                for warning in payload["warnings"]
            )
        )
        self.assertTrue(
            any(
                issue["summary"]
                == "external issues ingest failed for /tmp/does-not-exist-triage-input.json"
                for issue in payload["issues"]
            )
        )

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_emit_bundle_writes_markdown_and_ai_json(
        self,
        build_report_mock,
        write_output_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = make_args(
                emit_bundle=True,
                bundle_dir=tmp_dir,
                bundle_prefix="triage-pack",
                cihub_emit_dir=tmp_dir,
                no_cihub=True,
            )

            rc = triage.run(args)
            self.assertEqual(rc, 0)
            write_output_mock.assert_called_once()

            md_path = Path(tmp_dir) / "triage-pack.md"
            ai_path = Path(tmp_dir) / "triage-pack.ai.json"
            self.assertTrue(md_path.exists())
            self.assertTrue(ai_path.exists())

            ai_payload = json.loads(ai_path.read_text(encoding="utf-8"))
            self.assertEqual(ai_payload["command"], "triage")
            self.assertIn("next_actions", ai_payload)

    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_require_cihub_fails_when_disabled(
        self,
        build_report_mock,
        write_output_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        args = make_args(require_cihub=True, no_cihub=True, cihub=False)

        rc = triage.run(args)
        self.assertEqual(rc, 1)

        output = write_output_mock.call_args.args[0]
        payload = json.loads(output)
        self.assertTrue(any(issue["severity"] == "high" for issue in payload["issues"]))

    @patch("dev.scripts.devctl.triage.input_sources.run_cmd")
    @patch("dev.scripts.devctl.triage.input_sources.cihub_supports_triage")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_cihub_artifacts_are_ingested_when_available(
        self,
        build_report_mock,
        write_output_mock,
        cihub_supports_mock,
        run_cmd_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        cihub_supports_mock.return_value = (True, "parsed-help")
        run_cmd_mock.return_value = {
            "name": "cihub-triage",
            "cmd": ["cihub", "triage", "--latest"],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.03,
            "skipped": False,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            emit_dir = Path(tmp_dir)
            (emit_dir / "triage.json").write_text(
                json.dumps({"summary": {"severity": "high"}}),
                encoding="utf-8",
            )
            (emit_dir / "priority.json").write_text(
                json.dumps({"priority": ["ci", "security"]}),
                encoding="utf-8",
            )
            (emit_dir / "triage.md").write_text("# triage", encoding="utf-8")

            args = make_args(
                cihub=True,
                no_cihub=False,
                require_cihub=True,
                cihub_emit_dir=str(emit_dir),
                format="json",
            )

            rc = triage.run(args)
            self.assertEqual(rc, 0)
            run_cmd_mock.assert_called_once()

            payload = json.loads(write_output_mock.call_args.args[0])
            artifacts = payload["cihub"]["artifacts"]
            self.assertIn("triage_json", artifacts)
            self.assertIn("priority_json", artifacts)
            self.assertEqual(artifacts["triage_json"]["summary"]["severity"], "high")
            self.assertIn("rollup", payload)

    @patch("dev.scripts.devctl.triage.input_sources.run_cmd")
    @patch("dev.scripts.devctl.triage.input_sources.cihub_supports_triage")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_priority_entries_route_to_severity_and_owner(
        self,
        build_report_mock,
        write_output_mock,
        cihub_supports_mock,
        run_cmd_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        cihub_supports_mock.return_value = (True, "parsed-help")
        run_cmd_mock.return_value = {
            "name": "cihub-triage",
            "cmd": ["cihub", "triage", "--latest"],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.03,
            "skipped": False,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            emit_dir = Path(tmp_dir)
            (emit_dir / "priority.json").write_text(
                json.dumps(
                    {
                        "priorities": [
                            {
                                "category": "security",
                                "priority": "p1",
                                "summary": "Critical dependency exposure",
                            },
                            {
                                "category": "ci",
                                "priority": "p2",
                                "summary": "Flaky workflow retries",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            args = make_args(
                cihub=True,
                no_cihub=False,
                cihub_emit_dir=str(emit_dir),
                format="json",
            )
            rc = triage.run(args)
            self.assertEqual(rc, 0)

            payload = json.loads(write_output_mock.call_args.args[0])
            summaries = {issue["summary"]: issue for issue in payload["issues"]}
            self.assertEqual(
                summaries["Critical dependency exposure"]["severity"], "high"
            )
            self.assertEqual(
                summaries["Critical dependency exposure"]["owner"], "security"
            )
            self.assertEqual(summaries["Flaky workflow retries"]["severity"], "medium")
            self.assertEqual(summaries["Flaky workflow retries"]["owner"], "platform")

    @patch("dev.scripts.devctl.triage.input_sources.run_cmd")
    @patch("dev.scripts.devctl.triage.input_sources.cihub_supports_triage")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_owner_map_file_overrides_default_owner(
        self,
        build_report_mock,
        write_output_mock,
        cihub_supports_mock,
        run_cmd_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        cihub_supports_mock.return_value = (True, "parsed-help")
        run_cmd_mock.return_value = {
            "name": "cihub-triage",
            "cmd": ["cihub", "triage", "--latest"],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.03,
            "skipped": False,
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            emit_dir = Path(tmp_dir)
            owner_path = emit_dir / "owners.json"
            owner_path.write_text(json.dumps({"security": "secops"}), encoding="utf-8")
            (emit_dir / "priority.json").write_text(
                json.dumps(
                    {
                        "items": [
                            {
                                "category": "security",
                                "severity": "high",
                                "summary": "Policy drift detected",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            args = make_args(
                cihub=True,
                no_cihub=False,
                owner_map_file=str(owner_path),
                cihub_emit_dir=str(emit_dir),
                format="json",
            )
            rc = triage.run(args)
            self.assertEqual(rc, 0)

            payload = json.loads(write_output_mock.call_args.args[0])
            matching = [
                issue
                for issue in payload["issues"]
                if issue["summary"] == "Policy drift detected"
            ]
            self.assertTrue(matching)
            self.assertEqual(matching[0]["owner"], "secops")
            self.assertTrue(
                any("owner map loaded" in warning for warning in payload["warnings"])
            )

    @patch("dev.scripts.devctl.triage.input_sources.run_cmd")
    @patch("dev.scripts.devctl.triage.input_sources.cihub_supports_triage")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_cihub_failure_adds_warning_issue(
        self,
        build_report_mock,
        write_output_mock,
        cihub_supports_mock,
        run_cmd_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        cihub_supports_mock.return_value = (True, "parsed-help")
        run_cmd_mock.return_value = {
            "name": "cihub-triage",
            "cmd": ["cihub", "triage", "--latest"],
            "cwd": ".",
            "returncode": 2,
            "duration_s": 0.03,
            "skipped": False,
        }
        args = make_args(cihub=True, no_cihub=False, format="json")

        rc = triage.run(args)
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(
            any(
                "cihub triage command failed" in warning
                for warning in payload["warnings"]
            )
        )
        self.assertTrue(
            any(
                issue["summary"]
                == "cihub triage command failed; check cihub version/flags."
                for issue in payload["issues"]
            )
        )

    @patch("dev.scripts.devctl.triage.input_sources.cihub_supports_triage")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_cihub_unsupported_subcommand_skips_without_medium_failure_issue(
        self,
        build_report_mock,
        write_output_mock,
        cihub_supports_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
        cihub_supports_mock.return_value = (False, "parsed-help")
        args = make_args(cihub=True, no_cihub=False, format="json")

        rc = triage.run(args)
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        summaries = [issue["summary"] for issue in payload["issues"]]
        self.assertNotIn(
            "cihub triage command failed; check cihub version/flags.", summaries
        )
        self.assertIn("warning", payload["cihub"])
        self.assertIn("does not support `triage`", payload["cihub"]["warning"])


if __name__ == "__main__":
    unittest.main()
