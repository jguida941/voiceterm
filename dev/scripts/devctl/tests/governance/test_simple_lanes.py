"""Tests for simple policy-backed lane aliases."""

from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from dev.scripts.devctl import cli, quality_policy
from dev.scripts.devctl.commands import listing
from dev.scripts.devctl.commands.governance import simple_lanes


class SimpleLaneCommandTests(unittest.TestCase):
    def test_launcher_policy_resolves_python_only_launcher_scope(self) -> None:
        resolved = quality_policy.resolve_quality_policy(
            policy_path=simple_lanes.LAUNCHER_POLICY_PATH,
        )

        self.assertTrue(resolved.capabilities.python)
        self.assertFalse(resolved.capabilities.rust)
        self.assertEqual(
            resolved.scopes.python_guard_roots,
            (Path("scripts"), Path("pypi/src")),
        )
        self.assertEqual(
            resolved.scopes.python_probe_roots,
            (Path("scripts"), Path("pypi/src")),
        )
        self.assertIn("command_source_validation", {spec.script_id for spec in resolved.ai_guard_checks})
        self.assertIn("python_subprocess_policy", {spec.script_id for spec in resolved.ai_guard_checks})
        self.assertIn("probe_dict_as_struct", {spec.script_id for spec in resolved.review_probe_checks})

    def test_launcher_check_delegates_to_check_with_focused_policy(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "launcher-check",
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD~1",
                "--dry-run",
                "--keep-going",
                "--no-parallel",
                "--format",
                "json",
                "--output",
                "/tmp/launcher-check.json",
            ]
        )
        delegated = {}

        def fake_check(parsed_args) -> int:
            delegated["args"] = parsed_args
            return 0

        with patch.dict(cli.COMMAND_HANDLERS, {"check": fake_check}, clear=False):
            rc = cli.COMMAND_HANDLERS["launcher-check"](args)

        parsed = delegated["args"]
        self.assertEqual(rc, 0)
        self.assertEqual(parsed.command, "check")
        self.assertTrue(parsed.with_ai_guard)
        self.assertTrue(parsed.skip_fmt)
        self.assertTrue(parsed.skip_clippy)
        self.assertTrue(parsed.skip_tests)
        self.assertTrue(parsed.skip_build)
        self.assertEqual(parsed.quality_policy, simple_lanes.LAUNCHER_POLICY_PATH)
        self.assertEqual(parsed.since_ref, "origin/develop")
        self.assertEqual(parsed.head_ref, "HEAD~1")
        self.assertTrue(parsed.dry_run)
        self.assertTrue(parsed.keep_going)
        self.assertTrue(parsed.no_parallel)
        self.assertEqual(parsed.format, "json")
        self.assertEqual(parsed.output, "/tmp/launcher-check.json")

    def test_launcher_probes_delegates_to_probe_report_with_focused_policy(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "launcher-probes",
                "--adoption-scan",
                "--no-emit-artifacts",
                "--output-root",
                "/tmp/launcher-probes",
                "--format",
                "terminal",
                "--json-output",
                "/tmp/launcher-probes.json",
            ]
        )
        delegated = {}

        def fake_probe_report(parsed_args) -> int:
            delegated["args"] = parsed_args
            return 0

        with patch.dict(cli.COMMAND_HANDLERS, {"probe-report": fake_probe_report}, clear=False):
            rc = cli.COMMAND_HANDLERS["launcher-probes"](args)

        parsed = delegated["args"]
        self.assertEqual(rc, 0)
        self.assertEqual(parsed.command, "probe-report")
        self.assertEqual(parsed.quality_policy, simple_lanes.LAUNCHER_POLICY_PATH)
        self.assertTrue(parsed.adoption_scan)
        self.assertFalse(parsed.emit_artifacts)
        self.assertEqual(parsed.output_root, "/tmp/launcher-probes")
        self.assertEqual(parsed.format, "terminal")
        self.assertEqual(parsed.json_output, "/tmp/launcher-probes.json")

    def test_launcher_policy_delegates_to_quality_policy_with_focused_policy(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "launcher-policy",
                "--format",
                "json",
                "--output",
                "/tmp/launcher-policy.json",
            ]
        )
        delegated = {}

        def fake_quality_policy(parsed_args) -> int:
            delegated["args"] = parsed_args
            return 0

        with patch.dict(cli.COMMAND_HANDLERS, {"quality-policy": fake_quality_policy}, clear=False):
            rc = cli.COMMAND_HANDLERS["launcher-policy"](args)

        parsed = delegated["args"]
        self.assertEqual(rc, 0)
        self.assertEqual(parsed.command, "quality-policy")
        self.assertEqual(parsed.quality_policy, simple_lanes.LAUNCHER_POLICY_PATH)
        self.assertEqual(parsed.format, "json")
        self.assertEqual(parsed.output, "/tmp/launcher-policy.json")

    def test_list_exposes_simple_launcher_aliases(self) -> None:
        self.assertIn("launcher-check", listing.COMMANDS)
        self.assertIn("launcher-probes", listing.COMMANDS)
        self.assertIn("launcher-policy", listing.COMMANDS)


if __name__ == "__main__":
    unittest.main()
