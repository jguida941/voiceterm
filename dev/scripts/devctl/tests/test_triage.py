"""Tests for devctl triage command behavior."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import triage


def make_args(**overrides):
    defaults = {
        "ci": False,
        "ci_limit": 5,
        "dev_logs": False,
        "dev_root": None,
        "dev_sessions_limit": 5,
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
                "--format",
                "md",
            ]
        )
        self.assertEqual(args.command, "triage")
        self.assertTrue(args.ci)
        self.assertEqual(args.ci_limit, 7)
        self.assertTrue(args.cihub)
        self.assertEqual(args.cihub_run, "123")
        self.assertEqual(args.cihub_repo, "owner/repo")
        self.assertTrue(args.emit_bundle)
        self.assertEqual(args.bundle_prefix, "my-triage")
        self.assertEqual(args.owner_map_file, "/tmp/owners.json")
        self.assertEqual(args.format, "md")


class TriageCommandTests(unittest.TestCase):
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

    @patch("dev.scripts.devctl.commands.triage.run_cmd")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_cihub_artifacts_are_ingested_when_available(
        self,
        build_report_mock,
        write_output_mock,
        run_cmd_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
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

    @patch("dev.scripts.devctl.commands.triage.run_cmd")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_priority_entries_route_to_severity_and_owner(
        self,
        build_report_mock,
        write_output_mock,
        run_cmd_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
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
            self.assertEqual(summaries["Critical dependency exposure"]["severity"], "high")
            self.assertEqual(summaries["Critical dependency exposure"]["owner"], "security")
            self.assertEqual(summaries["Flaky workflow retries"]["severity"], "medium")
            self.assertEqual(summaries["Flaky workflow retries"]["owner"], "platform")

    @patch("dev.scripts.devctl.commands.triage.run_cmd")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_owner_map_file_overrides_default_owner(
        self,
        build_report_mock,
        write_output_mock,
        run_cmd_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
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
            matching = [issue for issue in payload["issues"] if issue["summary"] == "Policy drift detected"]
            self.assertTrue(matching)
            self.assertEqual(matching[0]["owner"], "secops")
            self.assertTrue(any("owner map loaded" in warning for warning in payload["warnings"]))

    @patch("dev.scripts.devctl.commands.triage.run_cmd")
    @patch("dev.scripts.devctl.commands.triage.write_output")
    @patch("dev.scripts.devctl.commands.triage.build_project_report")
    def test_cihub_failure_adds_warning_issue(
        self,
        build_report_mock,
        write_output_mock,
        run_cmd_mock,
    ) -> None:
        build_report_mock.return_value = minimal_project_report()
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
        self.assertTrue(any("cihub triage command failed" in warning for warning in payload["warnings"]))
        self.assertTrue(
            any(
                issue["summary"] == "cihub triage command failed; check cihub version/flags."
                for issue in payload["issues"]
            )
        )


if __name__ == "__main__":
    unittest.main()
