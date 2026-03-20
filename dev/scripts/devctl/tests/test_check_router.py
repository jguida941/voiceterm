"""Tests for devctl check-router command."""

from __future__ import annotations

import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import check_router


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "since_ref": None,
        "head_ref": "HEAD",
        "execute": False,
        "dry_run": False,
        "keep_going": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class CheckRouterTests(unittest.TestCase):
    """Validate lane routing, fallback policy, and execution wiring."""

    def test_cli_accepts_check_router_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "check-router",
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD",
                "--execute",
                "--dry-run",
                "--keep-going",
                "--quality-policy",
                "/tmp/router-policy.json",
            ]
        )
        self.assertEqual(args.command, "check-router")
        self.assertEqual(args.since_ref, "origin/develop")
        self.assertEqual(args.head_ref, "HEAD")
        self.assertTrue(args.execute)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.keep_going)
        self.assertEqual(args.quality_policy, "/tmp/router-policy.json")

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_docs_only_changes_route_to_docs_lane(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "guides/USAGE.md"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --user-facing"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["lane"], "docs")
        self.assertEqual(payload["bundle"], "bundle.docs")
        self.assertEqual(payload["risk_addons"], [])

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_runtime_hud_changes_detect_overlay_addon(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {"status": "M", "path": "rust/src/bin/voiceterm/status_line/format.rs"}
            ]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py check --profile ci"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["lane"], "runtime")
        addon_ids = {item["id"] for item in payload["risk_addons"]}
        self.assertIn("overlay-hud-controls", addon_ids)
        overlay_addon = next(
            item for item in payload["risk_addons"] if item["id"] == "overlay-hud-controls"
        )
        self.assertIn(
            "python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel",
            overlay_addon["commands"],
        )

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_pty_session_changes_detect_unsafe_lifecycle_addon(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "rust/src/pty_session/pty.rs"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py check --profile ci"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        addon_ids = {item["id"] for item in payload["risk_addons"]}
        self.assertIn("unsafe-ffi-lifecycle", addon_ids)
        unsafe_addon = next(
            item for item in payload["risk_addons"] if item["id"] == "unsafe-ffi-lifecycle"
        )
        self.assertIn(
            "python3 dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy --no-parallel",
            unsafe_addon["commands"],
        )

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_tooling_precedence_over_runtime_when_both_present(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {"status": "M", "path": "rust/src/bin/voiceterm/main.rs"},
                {"status": "M", "path": "dev/scripts/devctl/commands/check.py"},
            ]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["lane"], "tooling")
        self.assertEqual(payload["bundle"], "bundle.tooling")

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_unknown_paths_escalate_to_tooling_lane(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "third_party/custom.txt"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["lane"], "tooling")
        reason_text = " ".join(payload["reasons"])
        self.assertIn("Unknown paths detected", reason_text)

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_active_plan_markdown_routes_to_tooling_lane(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "dev/active/review_channel.md"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["lane"], "tooling")
        self.assertEqual(payload["bundle"], "bundle.tooling")

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_release_signals_route_to_release_lane(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "rust/Cargo.toml"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py check --profile release"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["lane"], "release")
        self.assertEqual(payload["bundle"], "bundle.release")

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router.run_cmd")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_execute_runs_planned_commands(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "guides/USAGE.md"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --user-facing"],
            None,
        )
        run_cmd_mock.return_value = {
            "name": "router-01",
            "cmd": [
                "bash",
                "-lc",
                "python3 dev/scripts/devctl.py docs-check --user-facing",
            ],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.01,
            "skipped": False,
        }

        rc = check_router.run(make_args(execute=True))
        self.assertEqual(rc, 0)
        run_cmd_mock.assert_called_once()
        executed = run_cmd_mock.call_args.args[1]
        self.assertEqual(executed[:2], ["bash", "-lc"])
        self.assertIn(sys.executable, executed[2])
        self.assertFalse(
            executed[2].startswith("python3 "),
            f"Expected sys.executable at the start, got: {executed[2]!r}",
        )

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["execute"])
        self.assertEqual(len(payload["steps"]), 1)

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_quality_policy_override_flows_into_policy_aware_commands(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "dev/scripts/devctl/commands/check.py"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            None,
        )

        rc = check_router.run(
            make_args(quality_policy="/tmp/router-policy.json")
        )
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        planned = payload["planned_commands"][0]["command"]
        self.assertIn(sys.executable, planned)
        self.assertIn("--quality-policy /tmp/router-policy.json", planned)

    def test_bundle_contract_extracts_non_empty_commands(self) -> None:
        for lane, bundle_name in check_router.BUNDLE_BY_LANE.items():
            commands, error = check_router._extract_bundle_commands(bundle_name)
            self.assertIsNone(
                error, msg=f"bundle extraction failed for lane `{lane}`: {error}"
            )
            self.assertGreater(
                len(commands), 0, msg=f"bundle `{bundle_name}` returned no commands"
            )

    def test_bundle_contract_keeps_host_cleanup_in_non_docs_lanes(self) -> None:
        cleanup_command = "python3 dev/scripts/devctl.py process-cleanup --verify --format md"

        runtime_commands, runtime_error = check_router._extract_bundle_commands(
            "bundle.runtime"
        )
        tooling_commands, tooling_error = check_router._extract_bundle_commands(
            "bundle.tooling"
        )
        release_commands, release_error = check_router._extract_bundle_commands(
            "bundle.release"
        )
        docs_commands, docs_error = check_router._extract_bundle_commands("bundle.docs")

        self.assertIsNone(runtime_error)
        self.assertIsNone(tooling_error)
        self.assertIsNone(release_error)
        self.assertIsNone(docs_error)
        self.assertIn(cleanup_command, runtime_commands)
        self.assertIn(cleanup_command, tooling_commands)
        self.assertIn(cleanup_command, release_commands)
        self.assertNotIn(cleanup_command, docs_commands)

    @patch("dev.scripts.devctl.commands.check_router.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_latency_changes_detect_direct_host_cleanup_addon(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "rust/src/audio/latency_tracker.rs"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py check --profile ci"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        addon_ids = {item["id"] for item in payload["risk_addons"]}
        self.assertIn("performance-latency", addon_ids)
        latency_addon = next(
            item for item in payload["risk_addons"] if item["id"] == "performance-latency"
        )
        self.assertIn(
            "python3 dev/scripts/devctl.py process-cleanup --verify --format md",
            latency_addon["commands"],
        )
