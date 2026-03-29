"""Tests for simple policy-backed lane aliases."""

from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from dev.scripts.devctl import cli, quality_policy
from dev.scripts.devctl.commands import listing
from dev.scripts.devctl.commands.governance import simple_lanes
from dev.scripts.devctl.commands.governance.simple_lanes_support import CURRENT_PYTHON


def _successful_tandem_run(name, cmd, cwd=None, dry_run=False) -> dict[str, object]:
    response = {
        "name": name,
        "cmd": cmd,
        "cwd": str(cwd),
        "returncode": 0,
    }
    response["duration_s"] = 0.01
    response["skipped"] = dry_run
    return response


def _mock_changes(*paths: str) -> dict[str, object]:
    return {"changes": [{"status": "M", "path": path} for path in paths]}


def _mock_bundle(*commands: str) -> tuple[list[str], None]:
    return (list(commands), None)


class SimpleLaneCommandTests(unittest.TestCase):
    def test_tandem_validate_parser_accepts_router_flags(self) -> None:
        args = cli.build_parser().parse_args(
            [
                "tandem-validate",
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD~1",
                "--quality-policy",
                "/tmp/pilot-policy.json",
                "--dry-run",
                "--keep-going",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "tandem-validate")
        self.assertEqual(args.since_ref, "origin/develop")
        self.assertEqual(args.head_ref, "HEAD~1")
        self.assertEqual(args.quality_policy, "/tmp/pilot-policy.json")
        self.assertTrue(args.dry_run)
        self.assertTrue(args.keep_going)
        self.assertEqual(args.format, "json")

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
        self.assertIn("tandem-validate", listing.COMMANDS)

    @patch("dev.scripts.devctl.commands.governance.simple_lanes.write_output")
    @patch("dev.scripts.devctl.commands.governance.simple_lanes.run_cmd")
    @patch("dev.scripts.devctl.commands.governance.simple_lanes_support._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.governance.simple_lanes_support.collect_git_status")
    def test_tandem_validate_routes_release_lane_and_rechecks_postflight(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        """Release lane should append tandem postflight checks."""
        args = cli.build_parser().parse_args(["tandem-validate", "--format", "json"])
        self.assertEqual(args.format, "json")
        collect_git_status_mock.return_value = _mock_changes(
            ".github/workflows/release_preflight.yml",
            "dev/scripts/devctl/governance/parser.py",
        )
        extract_bundle_mock.return_value = _mock_bundle(
            "python3 dev/scripts/devctl.py check --profile release",
            "python3 dev/scripts/checks/check_review_channel_bridge.py",
        )

        run_cmd_mock.side_effect = _successful_tandem_run

        rc = simple_lanes.run_tandem_validate(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["lane"], "release")
        self.assertEqual(payload["bundle"], "bundle.release")
        sources = [row["source"] for row in payload["planned_commands"]]
        self.assertEqual(sources[:2], ["tandem-preflight", "tandem-preflight"])
        self.assertIn("bundle.release", sources)
        self.assertIn("parser-ansi-boundary", sources)
        self.assertEqual(sources[-2:], ["tandem-postflight", "tandem-postflight"])
        self.assertEqual(payload["steps"][-1]["source"], "tandem-postflight")
        self.assertTrue(
            payload["planned_commands"][0]["command"].startswith(CURRENT_PYTHON)
        )
        self.assertTrue(
            any(
                row["command"].startswith(CURRENT_PYTHON)
                and "dev/scripts/devctl.py check --profile release" in row["command"]
                for row in payload["planned_commands"]
            )
        )

    @patch("dev.scripts.devctl.commands.governance.simple_lanes.write_output")
    @patch("dev.scripts.devctl.commands.governance.simple_lanes.run_cmd")
    @patch("dev.scripts.devctl.commands.governance.simple_lanes_support._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.governance.simple_lanes_support.collect_git_status")
    def test_tandem_validate_injects_policy_into_policy_aware_devctl_commands(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        """Policy-aware devctl commands should inherit the override path."""
        args = cli.build_parser().parse_args(
            [
                "tandem-validate",
                "--quality-policy",
                "/tmp/pilot-policy.json",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.quality_policy, "/tmp/pilot-policy.json")
        collect_git_status_mock.return_value = _mock_changes("dev/scripts/README.md")
        extract_bundle_mock.return_value = _mock_bundle(
            "python3 dev/scripts/devctl.py docs-check --strict-tooling",
            "python3 dev/scripts/devctl.py check --profile ci",
            "python3 dev/scripts/checks/check_active_plan_sync.py",
        )
        run_cmd_mock.side_effect = _successful_tandem_run

        rc = simple_lanes.run_tandem_validate(args)

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        commands = [row["command"] for row in payload["planned_commands"]]
        self.assertIn(
            f"{CURRENT_PYTHON} dev/scripts/devctl.py docs-check --strict-tooling --quality-policy /tmp/pilot-policy.json",
            commands,
        )
        self.assertIn(
            f"{CURRENT_PYTHON} dev/scripts/devctl.py check --profile ci --quality-policy /tmp/pilot-policy.json",
            commands,
        )
        self.assertIn(
            f"{CURRENT_PYTHON} dev/scripts/checks/check_active_plan_sync.py",
            commands,
        )


if __name__ == "__main__":
    unittest.main()
