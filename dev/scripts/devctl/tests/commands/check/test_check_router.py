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
        "range_scope_only": False,
        "validation_scope": "live_worktree",
        "execute": False,
        "dry_run": False,
        "keep_going": False,
        "no_parallel": False,
        "parallel_workers": 4,
        "command_timeout_seconds": 300,
        "route_timeout_seconds": 3600,
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
                "--range-scope-only",
                "--validation-scope",
                "pipeline_authorized_phase",
                "--execute",
                "--dry-run",
                "--keep-going",
                "--parallel-workers",
                "8",
                "--command-timeout-seconds",
                "120",
                "--route-timeout-seconds",
                "600",
                "--no-parallel",
                "--quality-policy",
                "/tmp/router-policy.json",
            ]
        )
        self.assertEqual(args.command, "check-router")
        self.assertEqual(args.since_ref, "origin/develop")
        self.assertEqual(args.head_ref, "HEAD")
        self.assertTrue(args.range_scope_only)
        self.assertEqual(args.validation_scope, "pipeline_authorized_phase")
        self.assertTrue(args.execute)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.keep_going)
        self.assertEqual(args.parallel_workers, 8)
        self.assertEqual(args.command_timeout_seconds, 120)
        self.assertEqual(args.route_timeout_seconds, 600)
        self.assertTrue(args.no_parallel)
        self.assertEqual(args.quality_policy, "/tmp/router-policy.json")

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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
        self.assertTrue(payload["rule_summary"])
        self.assertTrue(payload["match_evidence"])
        self.assertTrue(payload["rejected_rule_traces"])

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_devctl_change_routes_focused_devctl_tests_not_operator_console(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {
                    "status": "M",
                    "path": "dev/scripts/devctl/commands/python_tests.py",
                }
            ]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        planned_commands = [
            row["command"] for row in payload["planned_commands"]
        ]
        joined = "\n".join(planned_commands)
        self.assertIn("check_devctl_cold_boot.py --format md", joined)
        self.assertIn("test-python --suite devctl", joined)
        self.assertIn("--timeout-seconds 420", joined)
        self.assertIn("--per-test-timeout-seconds 90", joined)
        self.assertIn("--parallel-workers 1", joined)
        self.assertIn(
            "dev/scripts/devctl/tests/commands/test_python_tests.py",
            joined,
        )
        devctl_commands = [
            command
            for command in planned_commands
            if "test-python --suite devctl" in command
        ]
        self.assertEqual(len(devctl_commands), 1)
        self.assertEqual(devctl_commands[0].count("--path "), 1)
        self.assertNotIn("test-python --suite operator-console", joined)

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_devctl_focused_test_targets_split_into_serial_sessions(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {"status": "M", "path": path}
                for path in (
                    "dev/scripts/devctl/tests/checks/test_check_multi_agent_sync_runtime_truth.py",
                    "dev/scripts/devctl/tests/commands/check/test_check_router.py",
                    "dev/scripts/devctl/tests/commands/test_development_command.py",
                    "dev/scripts/devctl/tests/governance/test_bundle_registry.py",
                    "dev/scripts/devctl/tests/review_channel/test_collaboration_session.py",
                    "dev/scripts/devctl/tests/review_channel/test_current_session_projection.py",
                    "dev/scripts/devctl/tests/review_channel/test_event_post_wake.py",
                    "dev/scripts/devctl/tests/review_channel/test_event_render_typed_sections.py",
                    "dev/scripts/devctl/tests/review_channel/test_failure_packet_router.py",
                    "dev/scripts/devctl/tests/review_channel/test_follow_controller_reviewer_wake.py",
                    "dev/scripts/devctl/tests/vcs/test_push.py",
                )
            ]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        devctl_commands = [
            row["command"]
            for row in payload["planned_commands"]
            if "test-python --suite devctl" in row["command"]
        ]
        self.assertEqual(len(devctl_commands), 11)
        for command in devctl_commands:
            if "dev/scripts/devctl/tests/commands/test_development_command.py" in command:
                self.assertEqual(command.count("--path "), 1)
                self.assertIn("--timeout-seconds 900", command)
                self.assertIn("--parallel-workers 1", command)
            elif "dev/scripts/devctl/tests/vcs/test_push.py" in command:
                self.assertEqual(command.count("--path "), 6)
                self.assertIn(
                    "dev/scripts/devctl/tests/vcs/test_push.py::PushBridgeSyncTests",
                    command,
                )
                self.assertIn("--timeout-seconds 240", command)
                self.assertIn("--parallel-workers 4", command)
            else:
                self.assertEqual(command.count("--path "), 1)
                self.assertIn("--timeout-seconds 420", command)
                self.assertIn("--parallel-workers 1", command)

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_operator_console_change_routes_operator_console_tests(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {
                    "status": "M",
                    "path": "app/operator_console/state/presentation_state.py",
                }
            ]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        addon_ids = {item["id"] for item in payload["risk_addons"]}
        self.assertIn("python-tests.operator-console", addon_ids)
        planned_commands = [
            row["command"] for row in payload["planned_commands"]
        ]
        self.assertIn("test-python --suite operator-console", "\n".join(planned_commands))

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_operator_console_docs_do_not_route_operator_console_tests(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "app/operator_console/AGENTS.md"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/devctl.py docs-check --strict-tooling"],
            None,
        )

        rc = check_router.run(make_args())
        self.assertEqual(rc, 0)

        payload = json.loads(write_output_mock.call_args.args[0])
        planned_commands = [
            row["command"] for row in payload["planned_commands"]
        ]
        self.assertNotIn(
            "test-python --suite operator-console",
            "\n".join(planned_commands),
        )

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check.router_execution.run_cmd")
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
        self.assertEqual(run_cmd_mock.call_args.kwargs["policy"].timeout_seconds, 300)
        self.assertIn(sys.executable, executed[2])
        self.assertFalse(
            executed[2].startswith("python3 "),
            f"Expected sys.executable at the start, got: {executed[2]!r}",
        )

        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["execute"])
        self.assertEqual(payload["execution_policy"]["command_timeout_seconds"], 300)
        self.assertEqual(payload["planned_commands"][0]["timeout_seconds"], 300)
        self.assertEqual(len(payload["steps"]), 1)

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_since_ref_flows_into_range_aware_guard_commands(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.side_effect = [
            {
                "mode": "commit-range",
                "changes": [
                    {
                        "status": "M",
                        "path": "dev/scripts/devctl/commands/check/router.py",
                    }
                ],
            },
            {"mode": "working-tree", "changes": []},
        ]
        extract_bundle_mock.return_value = (
            [
                "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                "python3 dev/scripts/checks/check_python_broad_except.py",
                "python3 dev/scripts/checks/check_command_source_validation.py",
                "python3 dev/scripts/checks/check_code_shape.py",
                "python3 dev/scripts/checks/check_parameter_count.py",
            ],
            None,
        )

        rc = check_router.run(make_args(since_ref="origin/feature/demo"))

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        commands = [row["command"] for row in payload["planned_commands"]]
        self.assertIn(
            "--since-ref origin/feature/demo --head-ref HEAD",
            commands[0],
        )
        self.assertIn(
            "--since-ref origin/feature/demo --head-ref HEAD",
            commands[1],
        )
        self.assertIn(
            "--since-ref origin/feature/demo --head-ref HEAD",
            commands[2],
        )
        self.assertIn(
            "--since-ref origin/feature/demo --head-ref HEAD",
            commands[3],
        )
        self.assertIn(
            "--since-ref origin/feature/demo --head-ref HEAD",
            commands[4],
        )

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check.router_execution.run_cmd")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_execute_rewrites_repo_pytest_bundle_commands_to_active_interpreter(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "dev/scripts/devctl/commands/check.py"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 -m pytest app/operator_console/tests/ -q --tb=short"],
            None,
        )
        run_cmd_mock.return_value = {
            "name": "router-01",
            "cmd": [
                "bash",
                "-lc",
                "python3 -m pytest app/operator_console/tests/ -q --tb=short",
            ],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.01,
            "skipped": False,
        }

        rc = check_router.run(make_args(execute=True))
        self.assertEqual(rc, 0)

        executed = run_cmd_mock.call_args.args[1]
        self.assertEqual(executed[:2], ["bash", "-lc"])
        self.assertEqual(run_cmd_mock.call_args.kwargs["policy"].timeout_seconds, 300)
        self.assertIn(sys.executable, executed[2])
        self.assertFalse(
            executed[2].startswith("python3 "),
            f"Expected sys.executable at the start, got: {executed[2]!r}",
        )

        payload = json.loads(write_output_mock.call_args.args[0])
        planned = payload["planned_commands"][0]["command"]
        self.assertIn(sys.executable, planned)

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check.router_execution.run_step_specs")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_keep_going_reports_guard_coverage_and_remediation(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        run_step_specs_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "dev/scripts/README.md"}]
        }
        extract_bundle_mock.return_value = (
            [
                "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                "python3 dev/scripts/checks/check_registry_path_integrity.py",
            ],
            None,
        )
        run_step_specs_mock.side_effect = [
            [
                {
                    "name": "router-01",
                    "cmd": ["bash", "-lc", "docs-check"],
                    "cwd": ".",
                    "returncode": 1,
                    "duration_s": 0.01,
                    "skipped": False,
                    "failure_output": (
                        "Strict tooling docs mode requires maintainer docs; missing: "
                        "AGENTS.md, dev/guides/DEVELOPMENT.md."
                    ),
                }
            ],
            [
                {
                    "name": "router-02",
                    "cmd": ["bash", "-lc", "registry"],
                    "cwd": ".",
                    "returncode": 0,
                    "duration_s": 0.01,
                    "skipped": False,
                }
            ],
        ]

        rc = check_router.run(make_args(execute=True, keep_going=True))

        self.assertEqual(rc, 1)
        self.assertEqual(run_step_specs_mock.call_count, 2)
        first_kwargs = run_step_specs_mock.call_args_list[0].kwargs
        second_kwargs = run_step_specs_mock.call_args_list[1].kwargs
        self.assertFalse(first_kwargs["parallel_enabled"])
        self.assertTrue(second_kwargs["parallel_enabled"])
        self.assertEqual(second_kwargs["max_workers"], 4)
        second_specs = run_step_specs_mock.call_args_list[1].args[0]
        self.assertEqual(second_specs[0]["timeout_seconds"], 300)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["parallel_enabled"])
        self.assertEqual(payload["parallel_workers"], 4)
        self.assertEqual(payload["execution_plan"]["serial_required_command_count"], 1)
        self.assertEqual(payload["execution_plan"]["parallel_safe_command_count"], 1)
        coverage = payload["guard_coverage"]
        self.assertEqual(coverage["contract_id"], "CheckRouterGuardCoverageReceipt")
        self.assertEqual(coverage["planned_command_count"], 2)
        self.assertEqual(coverage["executed_command_count"], 2)
        self.assertEqual(coverage["failed_command_count"], 1)
        self.assertEqual(coverage["unexecuted_command_count"], 0)
        self.assertTrue(coverage["all_planned_commands_executed"])
        self.assertEqual(
            payload["remediation_actions"][0]["reason"],
            "strict_tooling_maintainer_docs_missing",
        )
        self.assertEqual(
            payload["remediation_actions"][0]["required_paths"],
            ["AGENTS.md", "dev/guides/DEVELOPMENT.md"],
        )

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check.router_execution.run_step_specs")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_keep_going_timeout_becomes_failed_guard_evidence(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        run_step_specs_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "dev/scripts/README.md"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/checks/check_startup_authority_contract.py"],
            None,
        )
        run_step_specs_mock.return_value = [
            {
                "name": "router-01",
                "cmd": ["bash", "-lc", "startup-authority"],
                "cwd": ".",
                "returncode": 124,
                "duration_s": 300.0,
                "skipped": False,
                "timed_out": True,
                "timeout_seconds": 300,
                "failure_output": "command timed out after 300s: startup-authority",
            }
        ]

        rc = check_router.run(make_args(execute=True, keep_going=True))

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["guard_coverage"]["failed_command_count"], 1)
        self.assertEqual(
            payload["remediation_actions"][0]["reason"],
            "guard_execution_timed_out",
        )
        self.assertTrue(payload["steps"][0]["timed_out"])

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check.router_execution.run_step_specs")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_keep_going_keeps_projection_commands_ordered_around_parallel_guards(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        run_step_specs_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "dev/scripts/README.md"}]
        }
        extract_bundle_mock.return_value = (
            [
                "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                "python3 dev/scripts/checks/check_registry_path_integrity.py",
                "python3 dev/scripts/checks/check_review_surface_consistency.py",
            ],
            None,
        )
        run_step_specs_mock.side_effect = [
            [
                {
                    "name": "router-01",
                    "cmd": ["bash", "-lc", "docs-check"],
                    "cwd": ".",
                    "returncode": 0,
                    "duration_s": 0.01,
                    "skipped": False,
                }
            ],
            [
                {
                    "name": "router-02",
                    "cmd": ["bash", "-lc", "registry"],
                    "cwd": ".",
                    "returncode": 0,
                    "duration_s": 0.01,
                    "skipped": False,
                }
            ],
            [
                {
                    "name": "router-03",
                    "cmd": ["bash", "-lc", "review-surface"],
                    "cwd": ".",
                    "returncode": 0,
                    "duration_s": 0.01,
                    "skipped": False,
                }
            ],
        ]

        rc = check_router.run(make_args(execute=True, keep_going=True))

        self.assertEqual(rc, 0)
        self.assertEqual(run_step_specs_mock.call_count, 3)
        self.assertFalse(run_step_specs_mock.call_args_list[0].kwargs["parallel_enabled"])
        self.assertTrue(run_step_specs_mock.call_args_list[1].kwargs["parallel_enabled"])
        self.assertFalse(run_step_specs_mock.call_args_list[2].kwargs["parallel_enabled"])
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["execution_plan"]["serial_required_command_count"], 2)
        self.assertEqual(payload["execution_plan"]["parallel_safe_command_count"], 1)
        self.assertEqual([step["name"] for step in payload["steps"]], ["router-01", "router-02", "router-03"])

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

    def test_tooling_bundle_routes_function_duplication_guard(self) -> None:
        tooling_commands, tooling_error = check_router._extract_bundle_commands(
            "bundle.tooling"
        )

        self.assertIsNone(tooling_error)
        self.assertIn(
            "python3 dev/scripts/checks/check_function_duplication.py",
            tooling_commands,
        )

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check.router_execution.run_cmd")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_json_dry_run_serializes_steps_without_dry_run_stdout(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [{"status": "M", "path": "dev/scripts/devctl/commands/check.py"}]
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/checks/check_function_duplication.py"],
            None,
        )

        rc = check_router.run(make_args(execute=True, dry_run=True, format="json"))

        self.assertEqual(rc, 0)
        run_cmd_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["steps"][0]["name"], "router-01")
        self.assertTrue(payload["steps"][0]["skipped"])
        self.assertIn(
            "check_function_duplication.py",
            payload["steps"][0]["router_command"],
        )

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_since_ref_uses_dirty_worktree_slice_before_branch_range(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.side_effect = [
            {
                "mode": "commit-range",
                "changes": [{"status": "M", "path": "rust/Cargo.toml"}],
            },
            {
                "mode": "working-tree",
                "changes": [
                    {
                        "status": "M",
                        "path": "dev/scripts/devctl/commands/check.py",
                    }
                ],
            },
        ]
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/checks/check_function_duplication.py"],
            None,
        )

        rc = check_router.run(make_args(since_ref="origin/develop"))

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["lane"], "tooling")
        self.assertEqual(
            payload["change_scope"]["source"],
            "working-tree-dirty-over-since-ref",
        )
        self.assertTrue(payload["change_scope"]["used_worktree_dirty_paths"])
        self.assertEqual(payload["change_scope"]["range_changed_paths_count"], 1)
        self.assertEqual(
            payload["changed_paths"],
            ["dev/scripts/devctl/commands/check.py"],
        )

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_range_scope_only_keeps_branch_range_despite_dirty_worktree(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "mode": "commit-range",
            "changes": [{"status": "M", "path": "rust/Cargo.toml"}],
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/checks/check_function_duplication.py"],
            None,
        )

        rc = check_router.run(
            make_args(since_ref="origin/develop", range_scope_only=True)
        )

        self.assertEqual(rc, 0)
        collect_git_status_mock.assert_called_once_with("origin/develop", "HEAD")
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["change_scope"]["source"], "commit-range")
        self.assertTrue(payload["change_scope"]["range_scope_only"])
        self.assertFalse(payload["change_scope"]["used_worktree_dirty_paths"])
        self.assertEqual(payload["changed_paths"], ["rust/Cargo.toml"])

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_publication_validation_scope_threads_live_projection_guards(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "mode": "commit-range",
            "changes": [
                {
                    "status": "M",
                    "path": "dev/scripts/devctl/commands/vcs/push.py",
                }
            ],
        }
        extract_bundle_mock.return_value = (
            [
                "python3 dev/scripts/devctl.py docs-check --strict-tooling",
                "python3 dev/scripts/checks/check_ground_truth_probe_gate.py",
                "python3 dev/scripts/checks/check_startup_authority_contract.py",
                "python3 dev/scripts/checks/check_tandem_consistency.py",
            ],
            None,
        )

        rc = check_router.run(
            make_args(
                since_ref="origin/develop",
                range_scope_only=True,
                validation_scope="pipeline_authorized_phase",
            )
        )

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        planned = "\n".join(row["command"] for row in payload["planned_commands"])
        self.assertIn("docs-check --strict-tooling", planned)
        self.assertIn("check_ground_truth_probe_gate.py", planned)
        self.assertIn(
            "check_startup_authority_contract.py --validation-scope pipeline_authorized_phase",
            planned,
        )
        self.assertIn(
            "check_tandem_consistency.py --validation-scope pipeline_authorized_phase",
            planned,
        )
        self.assertIn(
            "docs-check --strict-tooling --since-ref origin/develop --head-ref HEAD --validation-scope pipeline_authorized_phase",
            planned,
        )
        self.assertEqual(payload["scoped_out_commands"], [])
        self.assertEqual(
            payload["validation_scope"]["kind"],
            "pipeline_authorized_phase",
        )

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
    @patch("dev.scripts.devctl.commands.check_router._extract_bundle_commands")
    @patch("dev.scripts.devctl.commands.check_router.collect_git_status")
    def test_standalone_validation_scope_keeps_live_projection_guards(
        self,
        collect_git_status_mock,
        extract_bundle_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "mode": "commit-range",
            "changes": [
                {
                    "status": "M",
                    "path": "dev/scripts/devctl/commands/vcs/push.py",
                }
            ],
        }
        extract_bundle_mock.return_value = (
            ["python3 dev/scripts/checks/check_startup_authority_contract.py"],
            None,
        )

        rc = check_router.run(
            make_args(since_ref="origin/develop", range_scope_only=True)
        )

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        planned = "\n".join(row["command"] for row in payload["planned_commands"])
        self.assertIn("check_startup_authority_contract.py", planned)
        self.assertEqual(payload["scoped_out_commands"], [])
        self.assertEqual(payload["validation_scope"]["kind"], "live_worktree")

    @patch("dev.scripts.devctl.commands.check.router_execution.write_output")
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
