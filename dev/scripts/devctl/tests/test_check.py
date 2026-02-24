"""Tests for devctl check profile wiring."""

import io
import json
import time
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import check
from dev.scripts.devctl.commands import check_profile
from dev.scripts.devctl.commands import check_progress
from dev.scripts.devctl.commands import check_steps


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
    )


class CheckProfileTests(TestCase):
    def test_cli_accepts_maintainer_lint_profile(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--profile", "maintainer-lint"])
        self.assertEqual(args.profile, "maintainer-lint")

    def test_cli_accepts_ai_guard_profile(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--profile", "ai-guard"])
        self.assertEqual(args.profile, "ai-guard")

    def test_cli_accepts_no_process_sweep_cleanup_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--no-process-sweep-cleanup"])
        self.assertTrue(args.no_process_sweep_cleanup)

    def test_cli_accepts_parallel_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check", "--no-parallel", "--parallel-workers", "2"])
        self.assertTrue(args.no_parallel)
        self.assertEqual(args.parallel_workers, 2)

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

        printed = "\n".join(call.args[0] for call in mock_print.call_args_list if call.args)
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

        def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
            calls.append({"name": name, "cmd": cmd, "cwd": cwd})
            return {"name": name, "cmd": cmd, "cwd": str(cwd), "returncode": 0, "duration_s": 0.0, "skipped": False}

        mock_run_cmd.side_effect = fake_run_cmd

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
    def test_with_wake_guard_adds_gate_step(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
            calls.append({"name": name, "cmd": cmd, "cwd": cwd, "env": env})
            return {"name": name, "cmd": cmd, "cwd": str(cwd), "returncode": 0, "duration_s": 0.0, "skipped": False}

        mock_run_cmd.side_effect = fake_run_cmd
        args = make_args("")
        args.with_wake_guard = True
        args.wake_soak_rounds = 7

        rc = check.run(args)
        self.assertEqual(rc, 0)

        wake_call = next(call for call in calls if call["name"] == "wake-guard")
        self.assertEqual(wake_call["cmd"], ["bash", "dev/scripts/tests/wake_word_guard.sh"])
        self.assertEqual(wake_call["env"]["WAKE_WORD_SOAK_ROUNDS"], "7")

    @patch("dev.scripts.devctl.commands.check_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.check.build_mutation_score_cmd")
    @patch("dev.scripts.devctl.commands.check.resolve_outcomes_path")
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

        def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
            calls.append({"name": name, "cmd": cmd, "cwd": cwd, "env": env})
            return {"name": name, "cmd": cmd, "cwd": str(cwd), "returncode": 0, "duration_s": 0.0, "skipped": False}

        mock_run_cmd.side_effect = fake_run_cmd
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
        self.assertIn("code-shape-guard", names)
        self.assertIn("rust-lint-debt-guard", names)
        self.assertIn("rust-best-practices-guard", names)
        self.assertIn("rust-audit-patterns-guard", names)
        self.assertIn("rust-security-footguns-guard", names)

    @patch("dev.scripts.devctl.commands.check.write_output")
    @patch("dev.scripts.devctl.commands.check.resolve_outcomes_path")
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
    @patch("dev.scripts.devctl.commands.check.build_env")
    def test_prepush_profile_enables_ai_guard_steps(
        self,
        mock_build_env,
        mock_run_cmd,
    ) -> None:
        mock_build_env.return_value = {}
        calls = []

        def fake_run_cmd(name, cmd, cwd=None, env=None, dry_run=False):
            calls.append({"name": name, "cmd": cmd, "cwd": cwd, "env": env})
            return {"name": name, "cmd": cmd, "cwd": str(cwd), "returncode": 0, "duration_s": 0.0, "skipped": False}

        mock_run_cmd.side_effect = fake_run_cmd
        args = make_args("prepush")
        args.skip_tests = True
        args.skip_build = True
        args.skip_fmt = True
        args.skip_clippy = True

        rc = check.run(args)
        self.assertEqual(rc, 0)

        names = [call["name"] for call in calls]
        self.assertIn("code-shape-guard", names)
        self.assertIn("rust-lint-debt-guard", names)
        self.assertIn("rust-best-practices-guard", names)
        self.assertIn("rust-audit-patterns-guard", names)
        self.assertIn("rust-security-footguns-guard", names)

    @patch("dev.scripts.devctl.commands.check.run_cmd")
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

    @patch("dev.scripts.devctl.commands.check.run_step_specs")
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

    @patch("dev.scripts.devctl.commands.check.run_step_specs")
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


class CheckProcessSweepTests(TestCase):
    def test_parse_etime_seconds_handles_mm_ss_hh_mm_ss_and_days(self) -> None:
        self.assertEqual(check._parse_etime_seconds("05:30"), 330)
        self.assertEqual(check._parse_etime_seconds("01:05:30"), 3930)
        self.assertEqual(check._parse_etime_seconds("2-01:05:30"), 176730)
        self.assertIsNone(check._parse_etime_seconds("bad"))

    @patch("dev.scripts.devctl.commands.check.kill_processes")
    @patch("dev.scripts.devctl.commands.check.scan_voiceterm_test_binaries")
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

        result = check._cleanup_orphaned_voiceterm_test_binaries("process-sweep-test", dry_run=False)

        kill_mock.assert_called_once()
        self.assertEqual(result["detected_orphans"], 1)
        self.assertEqual(result["detected_stale_active"], 1)
        self.assertEqual(result["killed_pids"], [1234, 5678])
        self.assertEqual(result["returncode"], 0)

    @patch("dev.scripts.devctl.commands.check.kill_processes")
    @patch("dev.scripts.devctl.commands.check.scan_voiceterm_test_binaries")
    def test_cleanup_reports_warning_when_ps_unavailable(self, scan_mock, kill_mock) -> None:
        scan_mock.return_value = ([], ["Process sweep skipped: unable to execute ps (blocked)"])
        kill_mock.return_value = ([], [])
        result = check._cleanup_orphaned_voiceterm_test_binaries("process-sweep-test", dry_run=False)

        kill_mock.assert_called_once_with([])
        self.assertEqual(result["detected_orphans"], 0)
        self.assertEqual(result["detected_stale_active"], 0)
        self.assertTrue(result["warnings"])
        self.assertEqual(result["returncode"], 0)


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
        results = check_steps.run_step_specs_parallel(specs, dry_run=False, max_workers=2)
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
        self.assertEqual(total, 5)

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
        mock_run_cmd.side_effect = lambda name, cmd, cwd=None, env=None, dry_run=False: {
            "name": name,
            "cmd": cmd,
            "cwd": str(cwd),
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": False,
        }

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
        mock_run_cmd.side_effect = lambda name, cmd, cwd=None, env=None, dry_run=False: {
            "name": name,
            "cmd": cmd,
            "cwd": str(cwd),
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": False,
        }

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
