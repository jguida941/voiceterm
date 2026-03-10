"""Tests for devctl check profile wiring."""

import io
import json
import time
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import (
    check,
    check_phases,
    check_profile,
    check_progress,
    check_steps,
)


def make_args(profile: str) -> SimpleNamespace:
    return SimpleNamespace(
        profile=profile,
        ci=False,
        prepush=False,
        skip_fmt=False,
        skip_clippy=False,
        skip_tests=False,
        skip_build=False,
        fix=False,
        with_perf=False,
        with_mem_loop=False,
        mem_iterations=2,
        with_wake_guard=False,
        wake_soak_rounds=4,
        with_ai_guard=False,
        with_mutants=False,
        with_mutation_score=False,
        mutants_all=False,
        mutants_module=None,
        mutants_timeout=300,
        mutants_shard=None,
        mutants_offline=False,
        mutants_cargo_home=None,
        mutants_cargo_target_dir=None,
        mutants_plot=False,
        mutants_plot_scope=None,
        mutants_plot_top_pct=None,
        mutants_plot_output=None,
        mutants_plot_show=False,
        mutation_score_path=None,
        mutation_score_threshold=0.8,
        mutation_score_warn_age_hours=24.0,
        mutation_score_max_age_hours=None,
        since_ref=None,
        head_ref="HEAD",
        keep_going=False,
        no_parallel=False,
        parallel_workers=4,
        dry_run=False,
        format="text",
        output=None,
        pipe_command=None,
        pipe_args=None,
        offline=False,
        cargo_home=None,
        cargo_target_dir=None,
        no_process_sweep_cleanup=True,
        no_host_process_cleanup=False,
    )


def make_success_run_cmd_recorder(calls: list[dict[str, object]]):
    """Return a `run_cmd` side effect that records successful invocations."""

    def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
        calls.append(
            {
                "name": name,
                "cmd": cmd,
                "cwd": cwd,
                "env": env,
                "dry_run": dry_run,
            }
        )
        return {
            "name": name,
            "cmd": cmd,
            "cwd": str(cwd),
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": False,
        }

    return fake_run_cmd


class CheckProfileTests(TestCase):
    def test_cli_accepts_maintainer_lint_profile(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--profile", "maintainer-lint"])
        self.assertEqual(args.profile, "maintainer-lint")

    def test_cli_accepts_pedantic_profile(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--profile", "pedantic"])
        self.assertEqual(args.profile, "pedantic")

    def test_cli_accepts_ai_guard_profile(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--profile", "ai-guard"])
        self.assertEqual(args.profile, "ai-guard")

    def test_cli_accepts_fast_profile(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--profile", "fast"])
        self.assertEqual(args.profile, "fast")

    def test_fast_profile_matches_quick_preset(self) -> None:
        quick_settings, _ = check_profile.resolve_profile_settings(make_args("quick"))
        fast_settings, _ = check_profile.resolve_profile_settings(make_args("fast"))
        self.assertEqual(fast_settings, quick_settings)

    def test_fast_and_quick_profiles_keep_runtime_heavy_checks_disabled(self) -> None:
        for profile in ("fast", "quick"):
            settings, _ = check_profile.resolve_profile_settings(make_args(profile))
            self.assertTrue(
                settings["with_ai_guard"],
                "quick/fast must keep structural guards enabled by default",
            )
            self.assertFalse(settings["with_perf"])
            self.assertFalse(settings["with_mem_loop"])
            self.assertFalse(settings["with_mutation_score"])
            self.assertFalse(settings["with_wake_guard"])
            self.assertFalse(settings["with_ci_release_gate"])

    def test_prepush_and_release_profiles_keep_heavy_checks_enabled(self) -> None:
        prepush_settings, _ = check_profile.resolve_profile_settings(
            make_args("prepush")
        )
        release_settings, _ = check_profile.resolve_profile_settings(
            make_args("release")
        )

        self.assertTrue(prepush_settings["with_perf"])
        self.assertTrue(prepush_settings["with_mem_loop"])
        self.assertFalse(prepush_settings["with_ci_release_gate"])

        self.assertTrue(release_settings["with_mutation_score"])
        self.assertTrue(release_settings["mutation_score_report_only"])
        self.assertTrue(release_settings["with_wake_guard"])
        self.assertTrue(release_settings["with_ci_release_gate"])

    def test_cli_accepts_no_process_sweep_cleanup_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--no-process-sweep-cleanup"])
        self.assertTrue(args.no_process_sweep_cleanup)

    def test_cli_accepts_no_host_process_cleanup_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--no-host-process-cleanup"])
        self.assertTrue(args.no_host_process_cleanup)

    def test_cli_accepts_parallel_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--no-parallel", "--parallel-workers", "2"])
        self.assertTrue(args.no_parallel)
        self.assertEqual(args.parallel_workers, 2)

    def test_cli_accepts_commit_range_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "check",
                "--profile",
                "ai-guard",
                "--since-ref",
                "origin/develop",
                "--head-ref",
                "HEAD",
            ]
        )
        self.assertEqual(args.since_ref, "origin/develop")
        self.assertEqual(args.head_ref, "HEAD")

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    @patch("builtins.print")
    def test_failed_step_prints_failure_summary(
        self,
        mock_print,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        mock_run_cmd.return_value = {
            "name": "clippy",
            "cmd": ["cargo", "clippy"],
            "cwd": "src",
            "returncode": 1,
            "duration_s": 0.0,
            "skipped": False,
            "failure_output": "warning: unused variable",
        }
        args = make_args("")
        args.skip_fmt = True
        args.skip_tests = True
        args.skip_build = True

        rc = check.run(args)
        self.assertEqual(rc, 1)

        printed = "\n".join(
            call.args[0] for call in mock_print.call_args_list if call.args
        )
        self.assertIn("[check] step failed: clippy (exit 1)", printed)
        self.assertIn("[check] last output from clippy:", printed)
        self.assertIn("warning: unused variable", printed)

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_maintainer_lint_profile_uses_strict_clippy_subset(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        mock_run_cmd.side_effect = make_success_run_cmd_recorder(calls)

        rc = check.run(make_args("maintainer-lint"))
        self.assertEqual(rc, 0)

        names = [call["name"] for call in calls]
        self.assertIn("fmt-check", names)
        self.assertIn("clippy", names)
        self.assertNotIn("test", names)
        self.assertNotIn("build-release", names)

        clippy_cmd = next(call["cmd"] for call in calls if call["name"] == "clippy")
        self.assertIn("clippy::redundant_clone", clippy_cmd)
        self.assertIn("clippy::redundant_closure_for_method_calls", clippy_cmd)
        self.assertIn("clippy::cast_possible_wrap", clippy_cmd)
        self.assertIn("dead_code", clippy_cmd)
        # cast_precision_loss / cast_possible_truncation are deferred:
        # 20+ intentional usize<->f32/f64 casts in audio DSP pipeline require
        # per-site #[allow] annotations before these can be enforced.
        self.assertNotIn("clippy::cast_precision_loss", clippy_cmd)
        self.assertNotIn("clippy::cast_possible_truncation", clippy_cmd)

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_pedantic_profile_uses_opt_in_pedantic_clippy_only(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        mock_run_cmd.side_effect = make_success_run_cmd_recorder(calls)

        rc = check.run(make_args("pedantic"))
        self.assertEqual(rc, 0)

        names = [call["name"] for call in calls]
        self.assertIn("fmt-check", names)
        self.assertIn("clippy", names)
        self.assertNotIn("test", names)
        self.assertNotIn("build-release", names)

        clippy_cmd = next(call["cmd"] for call in calls if call["name"] == "clippy")
        self.assertEqual(clippy_cmd[0:2], ["python3", "dev/scripts/collect_clippy_warnings.py"])
        self.assertIn("--output-json", clippy_cmd)
        self.assertIn("--output-lints-json", clippy_cmd)
        self.assertIn("--extra-clippy-arg", clippy_cmd)
        self.assertIn("clippy::pedantic", clippy_cmd)
        self.assertNotIn("clippy::redundant_clone", clippy_cmd)

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_with_wake_guard_adds_gate_step(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        mock_run_cmd.side_effect = make_success_run_cmd_recorder(calls)
        args = make_args("")
        args.with_wake_guard = True
        args.wake_soak_rounds = 7

        rc = check.run(args)
        self.assertEqual(rc, 0)

        wake_call = next(call for call in calls if call["name"] == "wake-guard")
        self.assertEqual(
            wake_call["cmd"], ["bash", "dev/scripts/tests/wake_word_guard.sh"]
        )
        self.assertEqual(wake_call["env"]["WAKE_WORD_SOAK_ROUNDS"], "7")

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check_phases.build_mutation_score_cmd")
    @patch("dev.scripts.devctl.commands.check_phases.resolve_outcomes_path")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_release_profile_enables_wake_guard_and_mutation_score(
        self,
        mock_build_env,
        mock_resolve_outcomes,
        mock_build_mutation_score_cmd,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        mock_resolve_outcomes.return_value = "/tmp/outcomes.json"
        mock_build_mutation_score_cmd.return_value = [
            "python3",
            "dev/scripts/checks/check_mutation_score.py",
            "--path",
            "/tmp/outcomes.json",
            "--threshold",
            "0.8",
        ]
        calls = []

        mock_run_cmd.side_effect = make_success_run_cmd_recorder(calls)
        args = make_args("release")
        args.skip_tests = True
        args.skip_build = True
        args.skip_fmt = True
        args.skip_clippy = True

        rc = check.run(args)
        self.assertEqual(rc, 0)

        names = [call["name"] for call in calls]
        self.assertIn("wake-guard", names)
        self.assertIn("mutation-score", names)
        self.assertIn("ci-status-gate", names)
        self.assertIn("coderabbit-release-gate", names)
        self.assertIn("coderabbit-ralph-release-gate", names)
        self.assertIn("code-shape-guard", names)
        self.assertIn("python-broad-except-guard", names)
        self.assertIn("python-subprocess-policy-guard", names)
        self.assertIn("duplicate-types-guard", names)
        self.assertIn("structural-complexity-guard", names)
        self.assertIn("rust-test-shape-guard", names)
        self.assertIn("ide-provider-isolation-guard", names)
        self.assertIn("compat-matrix-guard", names)
        self.assertIn("compat-matrix-smoke-guard", names)
        self.assertIn("naming-consistency-guard", names)
        self.assertIn("rust-lint-debt-guard", names)
        self.assertIn("rust-best-practices-guard", names)
        self.assertIn("rust-runtime-panic-policy-guard", names)
        self.assertIn("rust-audit-patterns-guard", names)
        self.assertIn("rust-security-footguns-guard", names)
        release_gate_commands = check.build_release_gate_commands()
        ci_status_call = next(
            call for call in calls if call["name"] == "ci-status-gate"
        )
        self.assertEqual(ci_status_call["cmd"], release_gate_commands[0])
        mock_build_mutation_score_cmd.assert_called_once_with(
            "/tmp/outcomes.json",
            args.mutation_score_threshold,
            args.mutation_score_max_age_hours,
            args.mutation_score_warn_age_hours,
            True,
        )
        coderabbit_gate_call = next(
            call for call in calls if call["name"] == "coderabbit-release-gate"
        )
        coderabbit_ralph_gate_call = next(
            call for call in calls if call["name"] == "coderabbit-ralph-release-gate"
        )
        self.assertEqual(coderabbit_gate_call["cmd"], release_gate_commands[1])
        self.assertEqual(coderabbit_ralph_gate_call["cmd"], release_gate_commands[2])
        self.assertEqual(coderabbit_gate_call["env"]["CI"], "1")
        self.assertEqual(coderabbit_ralph_gate_call["env"]["CI"], "1")

    @patch("dev.scripts.devctl.commands.check_phases.write_output")
    @patch("dev.scripts.devctl.commands.check_phases.resolve_outcomes_path")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_with_mutation_score_missing_outcomes_fails(
        self,
        mock_build_env,
        mock_resolve_outcomes,
        mock_write_output,
    ) -> None:
        mock_build_env.return_value = {}
        mock_resolve_outcomes.return_value = None
        args = make_args("")
        args.with_mutation_score = True
        args.skip_fmt = True
        args.skip_clippy = True
        args.skip_tests = True
        args.skip_build = True
        args.format = "json"

        rc = check.run(args)

        self.assertEqual(rc, 1)
        report = json.loads(mock_write_output.call_args.args[0])
        self.assertFalse(report["success"])
        check_halt = next(
            step for step in report["steps"] if step["name"] == "check-halt"
        )
        self.assertEqual(check_halt["returncode"], 1)
        self.assertIn("mutation outcomes.json not found", check_halt["error"])

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check_phases.build_mutation_score_cmd")
    @patch("dev.scripts.devctl.commands.check_phases.resolve_outcomes_path")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_release_profile_allows_missing_outcomes_in_report_only_mode(
        self,
        mock_build_env,
        mock_resolve_outcomes,
        mock_build_mutation_score_cmd,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        mock_resolve_outcomes.return_value = None
        mock_build_mutation_score_cmd.return_value = [
            "python3",
            "dev/scripts/checks/check_mutation_score.py",
            "--threshold",
            "0.80",
            "--report-only",
        ]
        calls = []

        mock_run_cmd.side_effect = make_success_run_cmd_recorder(calls)
        args = make_args("release")
        args.skip_fmt = True
        args.skip_clippy = True
        args.skip_tests = True
        args.skip_build = True

        rc = check.run(args)

        self.assertEqual(rc, 0)
        mock_build_mutation_score_cmd.assert_called_once_with(
            None,
            args.mutation_score_threshold,
            args.mutation_score_max_age_hours,
            args.mutation_score_warn_age_hours,
            True,
        )
        names = [call["name"] for call in calls]
        self.assertIn("mutation-score", names)

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_prepush_profile_enables_ai_guard_steps(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        mock_run_cmd.side_effect = make_success_run_cmd_recorder(calls)
        args = make_args("prepush")
        args.skip_tests = True
        args.skip_build = True
        args.skip_fmt = True
        args.skip_clippy = True

        rc = check.run(args)
        self.assertEqual(rc, 0)

        names = [call["name"] for call in calls]
        self.assertIn("code-shape-guard", names)
        self.assertIn("python-broad-except-guard", names)
        self.assertIn("python-subprocess-policy-guard", names)
        self.assertIn("duplicate-types-guard", names)
        self.assertIn("structural-complexity-guard", names)
        self.assertIn("rust-test-shape-guard", names)
        self.assertIn("ide-provider-isolation-guard", names)
        self.assertIn("compat-matrix-guard", names)
        self.assertIn("compat-matrix-smoke-guard", names)
        self.assertIn("naming-consistency-guard", names)
        self.assertIn("rust-lint-debt-guard", names)
        self.assertIn("rust-best-practices-guard", names)
        self.assertIn("rust-runtime-panic-policy-guard", names)
        self.assertIn("rust-audit-patterns-guard", names)
        self.assertIn("rust-security-footguns-guard", names)

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_ci_profile_enables_ai_guard_steps(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        mock_run_cmd.side_effect = make_success_run_cmd_recorder(calls)
        args = make_args("ci")
        args.skip_tests = True
        args.skip_fmt = True
        args.skip_clippy = True

        rc = check.run(args)
        self.assertEqual(rc, 0)

        names = [call["name"] for call in calls]
        self.assertIn("code-shape-guard", names)
        self.assertIn("python-broad-except-guard", names)
        self.assertIn("python-subprocess-policy-guard", names)
        self.assertIn("duplicate-types-guard", names)
        self.assertIn("structural-complexity-guard", names)
        self.assertIn("rust-test-shape-guard", names)
        self.assertIn("ide-provider-isolation-guard", names)
        self.assertIn("compat-matrix-guard", names)
        self.assertIn("compat-matrix-smoke-guard", names)
        self.assertIn("naming-consistency-guard", names)
        self.assertIn("rust-lint-debt-guard", names)
        self.assertIn("rust-best-practices-guard", names)
        self.assertIn("rust-runtime-panic-policy-guard", names)
        self.assertIn("rust-audit-patterns-guard", names)
        self.assertIn("rust-security-footguns-guard", names)

    @patch("dev.scripts.devctl.commands.check_phases.run_cmd")
    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_ai_guard_failure_triggers_audit_scaffold_auto_generation(
        self,
        mock_build_env,
        mock_step_run_cmd,
        mock_scaffold_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}

        def fake_step_run(name, cmd, cwd=None, env=None, dry_run=False):
            if name == "code-shape-guard":
                return {
                    "name": name,
                    "cmd": cmd,
                    "cwd": str(cwd),
                    "returncode": 1,
                    "duration_s": 0.0,
                    "skipped": False,
                    "failure_output": "shape drift detected",
                }
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd),
                "returncode": 0,
                "duration_s": 0.0,
                "skipped": False,
            }

        mock_step_run_cmd.side_effect = fake_step_run
        mock_scaffold_run_cmd.return_value = {
            "name": "audit-scaffold-auto",
            "cmd": ["python3", "dev/scripts/devctl.py", "audit-scaffold"],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": False,
        }

        args = make_args("ai-guard")
        args.skip_fmt = True
        args.skip_clippy = True
        args.skip_tests = True

        rc = check.run(args)

        self.assertEqual(rc, 1)
        mock_scaffold_run_cmd.assert_called_once()
        called_cmd = mock_scaffold_run_cmd.call_args.args[1]
        self.assertIn("audit-scaffold", called_cmd)
        self.assertIn("--trigger", called_cmd)
        self.assertIn("check-ai-guard", called_cmd)
        self.assertIn("--trigger-steps", called_cmd)
        self.assertIn("code-shape-guard", called_cmd)

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_ai_guard_commit_range_forwarding(
        self, mock_build_env, mock_run_cmd
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        mock_run_cmd.side_effect = make_success_run_cmd_recorder(calls)
        args = make_args("ai-guard")
        args.skip_fmt = True
        args.skip_clippy = True
        args.skip_tests = True
        args.skip_build = True
        args.since_ref = "origin/develop"
        args.head_ref = "HEAD"

        rc = check.run(args)
        self.assertEqual(rc, 0)

        code_shape_cmd = next(
            call["cmd"] for call in calls if call["name"] == "code-shape-guard"
        )
        python_broad_except_cmd = next(
            call["cmd"]
            for call in calls
            if call["name"] == "python-broad-except-guard"
        )
        python_subprocess_policy_cmd = next(
            call["cmd"]
            for call in calls
            if call["name"] == "python-subprocess-policy-guard"
        )
        duplicate_types_cmd = next(
            call["cmd"] for call in calls if call["name"] == "duplicate-types-guard"
        )
        structural_complexity_cmd = next(
            call["cmd"]
            for call in calls
            if call["name"] == "structural-complexity-guard"
        )
        rust_test_shape_cmd = next(
            call["cmd"] for call in calls if call["name"] == "rust-test-shape-guard"
        )
        rust_lint_cmd = next(
            call["cmd"] for call in calls if call["name"] == "rust-lint-debt-guard"
        )
        rust_best_cmd = next(
            call["cmd"] for call in calls if call["name"] == "rust-best-practices-guard"
        )
        serde_compatibility_cmd = next(
            call["cmd"] for call in calls if call["name"] == "serde-compatibility-guard"
        )
        rust_panic_policy_cmd = next(
            call["cmd"]
            for call in calls
            if call["name"] == "rust-runtime-panic-policy-guard"
        )
        rust_audit_patterns_cmd = next(
            call["cmd"] for call in calls if call["name"] == "rust-audit-patterns-guard"
        )
        rust_footguns_cmd = next(
            call["cmd"]
            for call in calls
            if call["name"] == "rust-security-footguns-guard"
        )
        isolation_cmd = next(
            call["cmd"]
            for call in calls
            if call["name"] == "ide-provider-isolation-guard"
        )
        compat_matrix_cmd = next(
            call["cmd"] for call in calls if call["name"] == "compat-matrix-guard"
        )
        compat_matrix_smoke_cmd = next(
            call["cmd"] for call in calls if call["name"] == "compat-matrix-smoke-guard"
        )
        naming_consistency_cmd = next(
            call["cmd"] for call in calls if call["name"] == "naming-consistency-guard"
        )

        self.assertIn("--since-ref", code_shape_cmd)
        self.assertIn("--head-ref", code_shape_cmd)
        self.assertIn("--since-ref", python_broad_except_cmd)
        self.assertIn("--head-ref", python_broad_except_cmd)
        self.assertIn("--since-ref", python_subprocess_policy_cmd)
        self.assertIn("--head-ref", python_subprocess_policy_cmd)
        self.assertIn("--since-ref", duplicate_types_cmd)
        self.assertIn("--head-ref", duplicate_types_cmd)
        self.assertIn("--since-ref", structural_complexity_cmd)
        self.assertIn("--head-ref", structural_complexity_cmd)
        self.assertIn("--since-ref", rust_test_shape_cmd)
        self.assertIn("--head-ref", rust_test_shape_cmd)
        self.assertIn("--since-ref", rust_lint_cmd)
        self.assertIn("--head-ref", rust_lint_cmd)
        self.assertIn("--since-ref", rust_best_cmd)
        self.assertIn("--head-ref", rust_best_cmd)
        self.assertIn("--since-ref", serde_compatibility_cmd)
        self.assertIn("--head-ref", serde_compatibility_cmd)
        self.assertIn("--since-ref", rust_panic_policy_cmd)
        self.assertIn("--head-ref", rust_panic_policy_cmd)
        self.assertIn("--since-ref", rust_footguns_cmd)
        self.assertIn("--head-ref", rust_footguns_cmd)
        self.assertIn("--since-ref", rust_audit_patterns_cmd)
        self.assertIn("--head-ref", rust_audit_patterns_cmd)
        self.assertIn("--fail-on-violations", isolation_cmd)
        self.assertNotIn("--since-ref", isolation_cmd)
        self.assertNotIn("--since-ref", compat_matrix_cmd)
        self.assertNotIn("--since-ref", compat_matrix_smoke_cmd)
        self.assertNotIn("--since-ref", naming_consistency_cmd)

    @patch("dev.scripts.devctl.commands.check_phases.run_step_specs")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_parallel_mode_uses_parallel_runner_for_setup_phase(
        self,
        mock_build_env,
        mock_run_step_specs,
    ) -> None:
        mock_build_env.return_value = {}
        mock_run_step_specs.return_value = [
            {
                "name": "fmt-check",
                "cmd": ["cargo", "fmt", "--all", "--", "--check"],
                "cwd": "src",
                "returncode": 0,
                "duration_s": 0.0,
                "skipped": False,
            },
            {
                "name": "clippy",
                "cmd": ["cargo", "clippy"],
                "cwd": "src",
                "returncode": 0,
                "duration_s": 0.0,
                "skipped": False,
            },
        ]

        args = make_args("")
        args.skip_tests = True
        args.skip_build = True
        rc = check.run(args)
        self.assertEqual(rc, 0)
        mock_run_step_specs.assert_called_once()
        step_specs = mock_run_step_specs.call_args.args[0]
        self.assertEqual([spec["name"] for spec in step_specs], ["fmt-check", "clippy"])
        self.assertTrue(mock_run_step_specs.call_args.kwargs["parallel_enabled"])

    @patch("dev.scripts.devctl.commands.check_phases.run_step_specs")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_no_parallel_flag_uses_serial_runner(
        self,
        mock_build_env,
        mock_run_step_specs,
    ) -> None:
        mock_build_env.return_value = {}
        mock_run_step_specs.return_value = [
            {
                "name": "fmt-check",
                "cmd": ["cargo", "fmt"],
                "cwd": "src",
                "returncode": 0,
                "duration_s": 0.0,
                "skipped": False,
            },
            {
                "name": "clippy",
                "cmd": ["cargo", "clippy"],
                "cwd": "src",
                "returncode": 0,
                "duration_s": 0.0,
                "skipped": False,
            },
        ]
        args = make_args("")
        args.skip_tests = True
        args.skip_build = True
        args.no_parallel = True

        rc = check.run(args)
        self.assertEqual(rc, 0)
        mock_run_step_specs.assert_called_once()
        self.assertFalse(mock_run_step_specs.call_args.kwargs["parallel_enabled"])

    @patch("dev.scripts.devctl.commands.check_phases.run_step_specs")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_clippy_high_signal_guard_runs_after_setup_batch(
        self,
        mock_build_env,
        mock_run_step_specs,
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        def fake_run_step_specs(step_specs, *, dry_run, parallel_enabled, max_workers):
            calls.append(
                {
                    "names": [spec["name"] for spec in step_specs],
                    "parallel_enabled": parallel_enabled,
                    "max_workers": max_workers,
                }
            )
            return [
                {
                    "name": spec["name"],
                    "cmd": spec["cmd"],
                    "cwd": str(spec["cwd"]),
                    "returncode": 0,
                    "duration_s": 0.0,
                    "skipped": False,
                }
                for spec in step_specs
            ]

        mock_run_step_specs.side_effect = fake_run_step_specs
        args = make_args("ci")
        args.skip_fmt = True
        args.skip_tests = True
        args.skip_build = True

        rc = check.run(args)
        self.assertEqual(rc, 0)

        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0]["parallel_enabled"])
        self.assertIn("clippy", calls[0]["names"])
        self.assertNotIn("clippy-high-signal-guard", calls[0]["names"])
        self.assertFalse(calls[1]["parallel_enabled"])
        self.assertEqual(calls[1]["names"], ["clippy-high-signal-guard"])


class CheckProcessSweepTests(TestCase):
    def test_parse_etime_seconds_handles_mm_ss_hh_mm_ss_and_days(self) -> None:
        self.assertEqual(check._parse_etime_seconds("05:30"), 330)
        self.assertEqual(check._parse_etime_seconds("01:05:30"), 3930)
        self.assertEqual(check._parse_etime_seconds("2-01:05:30"), 176730)
        self.assertIsNone(check._parse_etime_seconds("bad"))

    @patch("dev.scripts.devctl.commands.check.kill_processes")
    @patch("dev.scripts.devctl.commands.check.scan_repo_hygiene_process_tree")
    def test_cleanup_kills_orphaned_and_stale_voiceterm_test_binaries(
        self,
        scan_mock,
        kill_mock,
    ) -> None:
        scan_mock.return_value = (
            [
                {
                    "pid": 1234,
                    "ppid": 1,
                    "etime": "05:00",
                    "elapsed_seconds": 300,
                    "command": "/tmp/project/target/debug/deps/voiceterm-deadbeef --test-threads=4",
                },
                {
                    "pid": 5678,
                    "ppid": 777,
                    "etime": "15:00",
                    "elapsed_seconds": 900,
                    "command": "/tmp/project/target/debug/deps/voiceterm-feedface --nocapture",
                },
            ],
            [],
        )
        kill_mock.return_value = ([1234, 5678], [])

        result = check._cleanup_orphaned_voiceterm_test_binaries(
            "process-sweep-test", dry_run=False
        )

        kill_mock.assert_called_once()
        self.assertEqual(result["detected_orphans"], 1)
        self.assertEqual(result["detected_stale_active"], 1)
        self.assertEqual(result["killed_pids"], [1234, 5678])
        self.assertEqual(result["returncode"], 0)

    @patch("dev.scripts.devctl.commands.check.kill_processes")
    @patch("dev.scripts.devctl.commands.check.scan_repo_hygiene_process_tree")
    def test_cleanup_reports_warning_when_ps_unavailable(
        self, scan_mock, kill_mock
    ) -> None:
        scan_mock.return_value = (
            [],
            ["Process sweep skipped: unable to execute ps (blocked)"],
        )
        kill_mock.return_value = ([], [])
        result = check._cleanup_orphaned_voiceterm_test_binaries(
            "process-sweep-test", dry_run=False
        )

        kill_mock.assert_called_once_with([])
        self.assertEqual(result["detected_orphans"], 0)
        self.assertEqual(result["detected_stale_active"], 0)
        self.assertTrue(result["warnings"])
        self.assertEqual(result["returncode"], 0)

    @patch("dev.scripts.devctl.commands.check.build_process_cleanup_report")
    def test_quick_profile_runs_host_process_cleanup_by_default(
        self,
        cleanup_report_mock,
    ) -> None:
        cleanup_report_mock.return_value = {
            "dry_run": False,
            "warnings": [],
            "errors": [],
            "killed_pids": [],
            "orphaned_count_pre": 0,
            "stale_active_count_pre": 0,
            "verify_ok": True,
            "ok": True,
        }
        result = check._cleanup_host_processes(
            "host-process-cleanup-post",
            dry_run=False,
        )

        cleanup_report_mock.assert_called_once_with(dry_run=False, verify=True)
        self.assertEqual(result["returncode"], 0)
        self.assertTrue(result["verify_ok"])

    @patch("dev.scripts.devctl.commands.check.build_report_and_emit", return_value=0)
    @patch("dev.scripts.devctl.commands.check.run_specialized_phases")
    @patch("dev.scripts.devctl.commands.check.run_test_build_phase")
    @patch("dev.scripts.devctl.commands.check.run_setup_phase")
    @patch("dev.scripts.devctl.commands.check._cleanup_host_processes")
    @patch("dev.scripts.devctl.commands.check._cleanup_orphaned_voiceterm_test_binaries")
    @patch("dev.scripts.devctl.commands.check.build_env", return_value={})
    def test_quick_profile_appends_host_process_cleanup_step(
        self,
        _build_env_mock,
        sweep_mock,
        host_cleanup_mock,
        _run_setup_mock,
        _run_test_build_mock,
        _run_specialized_mock,
        report_mock,
    ) -> None:
        sweep_mock.side_effect = [
            {"name": "process-sweep-pre", "returncode": 0},
            {"name": "process-sweep-post", "returncode": 0},
        ]
        host_cleanup_mock.return_value = {
            "name": "host-process-cleanup-post",
            "returncode": 0,
        }

        captured_steps: list[dict] = []

        def fake_build_report(ctx):
            captured_steps.extend(ctx.steps)
            return 0

        report_mock.side_effect = fake_build_report
        args = make_args("quick")
        args.no_process_sweep_cleanup = False

        rc = check.run(args)

        self.assertEqual(rc, 0)
        host_cleanup_mock.assert_called_once_with(
            step_name="host-process-cleanup-post",
            dry_run=False,
        )
        self.assertEqual(
            [step["name"] for step in captured_steps],
            [
                "process-sweep-pre",
                "process-sweep-post",
                "host-process-cleanup-post",
            ],
        )

    @patch("dev.scripts.devctl.commands.check.build_report_and_emit", return_value=0)
    @patch("dev.scripts.devctl.commands.check.run_specialized_phases")
    @patch("dev.scripts.devctl.commands.check.run_test_build_phase")
    @patch("dev.scripts.devctl.commands.check.run_setup_phase")
    @patch("dev.scripts.devctl.commands.check._cleanup_host_processes")
    @patch("dev.scripts.devctl.commands.check._cleanup_orphaned_voiceterm_test_binaries")
    @patch("dev.scripts.devctl.commands.check.build_env", return_value={})
    def test_fast_profile_appends_host_process_cleanup_step(
        self,
        _build_env_mock,
        sweep_mock,
        host_cleanup_mock,
        _run_setup_mock,
        _run_test_build_mock,
        _run_specialized_mock,
        report_mock,
    ) -> None:
        sweep_mock.side_effect = [
            {"name": "process-sweep-pre", "returncode": 0},
            {"name": "process-sweep-post", "returncode": 0},
        ]
        host_cleanup_mock.return_value = {
            "name": "host-process-cleanup-post",
            "returncode": 0,
        }

        captured_steps: list[dict] = []

        def fake_build_report(ctx):
            captured_steps.extend(ctx.steps)
            return 0

        report_mock.side_effect = fake_build_report
        args = make_args("fast")
        args.no_process_sweep_cleanup = False

        rc = check.run(args)

        self.assertEqual(rc, 0)
        host_cleanup_mock.assert_called_once_with(
            step_name="host-process-cleanup-post",
            dry_run=False,
        )
        self.assertEqual(captured_steps[-1]["name"], "host-process-cleanup-post")

    @patch("dev.scripts.devctl.commands.check.build_report_and_emit", return_value=0)
    @patch("dev.scripts.devctl.commands.check.run_specialized_phases")
    @patch("dev.scripts.devctl.commands.check.run_test_build_phase")
    @patch("dev.scripts.devctl.commands.check.run_setup_phase")
    @patch("dev.scripts.devctl.commands.check._cleanup_host_processes")
    @patch("dev.scripts.devctl.commands.check._cleanup_orphaned_voiceterm_test_binaries")
    @patch("dev.scripts.devctl.commands.check.build_env", return_value={})
    def test_quick_profile_respects_no_host_process_cleanup_flag(
        self,
        _build_env_mock,
        sweep_mock,
        host_cleanup_mock,
        _run_setup_mock,
        _run_test_build_mock,
        _run_specialized_mock,
        report_mock,
    ) -> None:
        sweep_mock.side_effect = [
            {"name": "process-sweep-pre", "returncode": 0},
            {"name": "process-sweep-post", "returncode": 0},
        ]

        captured_steps: list[dict] = []

        def fake_build_report(ctx):
            captured_steps.extend(ctx.steps)
            return 0

        report_mock.side_effect = fake_build_report
        args = make_args("quick")
        args.no_process_sweep_cleanup = False
        args.no_host_process_cleanup = True

        rc = check.run(args)

        self.assertEqual(rc, 0)
        host_cleanup_mock.assert_not_called()
        self.assertEqual(
            [step["name"] for step in captured_steps],
            ["process-sweep-pre", "process-sweep-post"],
        )


class CheckParallelHelperTests(TestCase):
    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    def test_parallel_runner_preserves_declared_step_order(self, mock_run_cmd) -> None:
        def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
            if name == "fmt-check":
                time.sleep(0.05)
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd),
                "returncode": 0,
                "duration_s": 0.0,
                "skipped": False,
            }

        mock_run_cmd.side_effect = fake_run_cmd
        specs = [
            {"name": "fmt-check", "cmd": ["cargo", "fmt"], "cwd": "src", "env": {}},
            {"name": "clippy", "cmd": ["cargo", "clippy"], "cwd": "src", "env": {}},
        ]
        results = check_steps.run_step_specs_parallel(
            specs, dry_run=False, max_workers=2
        )
        self.assertEqual([entry["name"] for entry in results], ["fmt-check", "clippy"])


class CheckProfileFlagConflictTests(TestCase):
    """Tests for _validate_profile_flag_conflicts warning generation."""

    def test_no_profile_returns_no_warnings(self) -> None:
        args = make_args("")
        args.skip_fmt = True
        args.no_parallel = True
        warnings = check_profile.validate_profile_flag_conflicts(args)
        self.assertEqual(warnings, [])

    def test_profile_none_returns_no_warnings(self) -> None:
        args = make_args("")
        args.profile = None
        warnings = check_profile.validate_profile_flag_conflicts(args)
        self.assertEqual(warnings, [])

    def test_ci_profile_with_skip_build_warns_redundant(self) -> None:
        args = make_args("ci")
        args.skip_build = True  # ci forces skip_build=True
        warnings = check_profile.validate_profile_flag_conflicts(args)
        matching = [w for w in warnings if "--skip-build" in w and "redundant" in w]
        self.assertEqual(len(matching), 1)
        self.assertIn("profile already sets skip_build=True", matching[0])

    def test_ci_profile_with_with_perf_warns_override(self) -> None:
        args = make_args("ci")
        args.with_perf = True  # ci forces with_perf=False
        warnings = check_profile.validate_profile_flag_conflicts(args)
        matching = [w for w in warnings if "--with-perf" in w and "conflicts" in w]
        self.assertEqual(len(matching), 1)
        self.assertIn("profile forces with_perf=False", matching[0])

    def test_ci_profile_with_skip_fmt_warns_noted(self) -> None:
        args = make_args("ci")
        args.skip_fmt = True  # not controlled by ci profile
        warnings = check_profile.validate_profile_flag_conflicts(args)
        matching = [w for w in warnings if "--skip-fmt" in w]
        self.assertEqual(len(matching), 1)
        self.assertIn("does not control this flag", matching[0])

    def test_release_profile_with_no_parallel_warns(self) -> None:
        args = make_args("release")
        args.no_parallel = True
        warnings = check_profile.validate_profile_flag_conflicts(args)
        matching = [w for w in warnings if "--no-parallel" in w]
        self.assertEqual(len(matching), 1)
        self.assertIn("sequential mode will take effect", matching[0])

    def test_prepush_profile_with_keep_going_warns(self) -> None:
        args = make_args("prepush")
        args.keep_going = True
        warnings = check_profile.validate_profile_flag_conflicts(args)
        matching = [w for w in warnings if "--keep-going" in w]
        self.assertEqual(len(matching), 1)
        self.assertIn("will take effect", matching[0])

    def test_maintainer_lint_with_skip_tests_warns_redundant(self) -> None:
        args = make_args("maintainer-lint")
        args.skip_tests = True  # maintainer-lint forces skip_tests=True
        warnings = check_profile.validate_profile_flag_conflicts(args)
        matching = [w for w in warnings if "--skip-tests" in w and "redundant" in w]
        self.assertEqual(len(matching), 1)

    def test_release_profile_with_with_ai_guard_warns_redundant(self) -> None:
        args = make_args("release")
        args.with_ai_guard = True  # release forces with_ai_guard=True
        warnings = check_profile.validate_profile_flag_conflicts(args)
        matching = [w for w in warnings if "--with-ai-guard" in w and "redundant" in w]
        self.assertEqual(len(matching), 1)

    def test_no_flags_at_default_produces_no_warnings(self) -> None:
        args = make_args("ci")
        # All flags at defaults - no conflicts
        warnings = check_profile.validate_profile_flag_conflicts(args)
        self.assertEqual(warnings, [])

    def test_multiple_conflicts_produce_multiple_warnings(self) -> None:
        args = make_args("ci")
        args.with_perf = True  # conflicts (ci forces False)
        args.skip_build = True  # redundant (ci forces True)
        args.skip_fmt = True  # noted (not controlled by ci)
        warnings = check_profile.validate_profile_flag_conflicts(args)
        self.assertGreaterEqual(len(warnings), 3)

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_run_emits_conflict_warnings_to_stderr(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        mock_run_cmd.return_value = {
            "name": "clippy",
            "cmd": ["cargo", "clippy"],
            "cwd": "src",
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": False,
        }
        args = make_args("ci")
        args.skip_fmt = True
        args.skip_clippy = True
        args.skip_tests = True

        with patch("sys.stderr") as mock_stderr:
            mock_stderr.write = lambda s: None
            with patch("builtins.print") as mock_print:
                check.run(args)

        # Check that at least one warning was printed (via the print calls
        # that include file=sys.stderr).
        warning_calls = [
            call
            for call in mock_print.call_args_list
            if call.args and "[check] warning:" in str(call.args[0])
        ]
        self.assertGreater(len(warning_calls), 0)


class CheckProgressFeedbackTests(TestCase):
    """Tests for step-counter progress output."""

    def test_count_quality_steps_default_profile(self) -> None:
        """Default profile with no skips counts fmt + clippy + test + build."""
        args = make_args("")
        settings = {
            "skip_tests": False,
            "skip_build": False,
            "with_ai_guard": False,
            "with_wake_guard": False,
            "with_perf": False,
            "with_mem_loop": False,
            "with_mutants": False,
            "with_mutation_score": False,
        }
        total = check_progress.count_quality_steps(args, settings)
        self.assertEqual(total, 4)  # fmt-check, clippy, test, build-release

    def test_count_quality_steps_with_skips(self) -> None:
        args = make_args("")
        args.skip_fmt = True
        args.skip_clippy = True
        settings = {
            "skip_tests": True,
            "skip_build": True,
            "with_ai_guard": False,
            "with_wake_guard": False,
            "with_perf": False,
            "with_mem_loop": False,
            "with_mutants": False,
            "with_mutation_score": False,
        }
        total = check_progress.count_quality_steps(args, settings)
        self.assertEqual(total, 0)

    def test_count_quality_steps_with_ai_guard(self) -> None:
        args = make_args("")
        args.skip_fmt = True
        args.skip_clippy = True
        settings = {
            "skip_tests": True,
            "skip_build": True,
            "with_ai_guard": True,
            "with_wake_guard": False,
            "with_perf": False,
            "with_mem_loop": False,
            "with_mutants": False,
            "with_mutation_score": False,
        }
        total = check_progress.count_quality_steps(args, settings)
        self.assertEqual(total, len(check_progress.AI_GUARD_CHECKS))

    def test_count_quality_steps_with_clippy_high_signal(self) -> None:
        args = make_args("")
        args.skip_fmt = True
        settings = {
            "skip_tests": True,
            "skip_build": True,
            "with_ai_guard": False,
            "with_wake_guard": False,
            "with_perf": False,
            "with_mem_loop": False,
            "with_mutants": False,
            "with_mutation_score": False,
            "with_clippy_high_signal": True,
        }
        total = check_progress.count_quality_steps(args, settings)
        self.assertEqual(total, 2)

    def test_count_quality_steps_with_release_ci_gates(self) -> None:
        args = make_args("")
        args.skip_fmt = True
        args.skip_clippy = True
        settings = {
            "skip_tests": True,
            "skip_build": True,
            "with_ai_guard": False,
            "with_wake_guard": False,
            "with_perf": False,
            "with_mem_loop": False,
            "with_mutants": False,
            "with_mutation_score": False,
            "with_ci_release_gate": True,
        }
        total = check_progress.count_quality_steps(args, settings)
        self.assertEqual(total, 3)

    def test_emit_progress_serial_single_step(self) -> None:
        """Single-step serial prints [1/4] name..."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            check_progress.emit_progress(
                [{"name": "fmt-check"}], current=0, total=4, is_parallel=False
            )
        self.assertEqual(stderr.getvalue().strip(), "[1/4] fmt-check...")

    def test_emit_progress_serial_multiple_steps(self) -> None:
        """Multiple steps in serial mode print one line each."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            check_progress.emit_progress(
                [{"name": "fmt-check"}, {"name": "clippy"}],
                current=0,
                total=4,
                is_parallel=False,
            )
        lines = stderr.getvalue().strip().split("\n")
        self.assertEqual(lines[0], "[1/4] fmt-check...")
        self.assertEqual(lines[1], "[2/4] clippy...")

    def test_emit_progress_parallel_batch(self) -> None:
        """Parallel batch prints [1-2/4] running 2 steps in parallel (...)..."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            check_progress.emit_progress(
                [{"name": "fmt-check"}, {"name": "clippy"}],
                current=0,
                total=4,
                is_parallel=True,
            )
        output = stderr.getvalue().strip()
        self.assertIn("[1-2/4]", output)
        self.assertIn("running 2 steps in parallel", output)
        self.assertIn("fmt-check", output)
        self.assertIn("clippy", output)

    def test_emit_progress_parallel_single_step_uses_serial_format(self) -> None:
        """A single-step parallel call uses serial format (no range)."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            check_progress.emit_progress(
                [{"name": "test"}], current=2, total=4, is_parallel=True
            )
        self.assertEqual(stderr.getvalue().strip(), "[3/4] test...")

    def test_emit_progress_empty_specs_is_noop(self) -> None:
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            check_progress.emit_progress([], current=0, total=4, is_parallel=False)
        self.assertEqual(stderr.getvalue(), "")

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_run_emits_serial_progress_to_stderr(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        """With --no-parallel, each step gets [N/M] progress on stderr."""
        mock_build_env.return_value = {}
        mock_run_cmd.side_effect = (
            lambda name, cmd, cwd=None, env=None, dry_run=False: {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd),
                "returncode": 0,
                "duration_s": 0.0,
                "skipped": False,
            }
        )

        args = make_args("")
        args.no_parallel = True
        args.skip_tests = True
        args.skip_build = True

        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            rc = check.run(args)
        self.assertEqual(rc, 0)

        output = stderr.getvalue()
        self.assertIn("[1/2] fmt-check...", output)
        self.assertIn("[2/2] clippy...", output)

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_run_emits_parallel_progress_to_stderr(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        """With parallel enabled, batched steps show range progress on stderr."""
        mock_build_env.return_value = {}
        mock_run_cmd.side_effect = (
            lambda name, cmd, cwd=None, env=None, dry_run=False: {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd),
                "returncode": 0,
                "duration_s": 0.0,
                "skipped": False,
            }
        )

        args = make_args("")
        args.skip_tests = True
        args.skip_build = True
        # parallel is default (no_parallel=False)

        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            rc = check.run(args)
        self.assertEqual(rc, 0)

        output = stderr.getvalue()
        # fmt-check and clippy run as a parallel batch
        self.assertIn("[1-2/2]", output)
        self.assertIn("running 2 steps in parallel", output)
