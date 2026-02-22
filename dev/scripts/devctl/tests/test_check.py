"""Tests for devctl check profile wiring."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import check


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

    @patch("dev.scripts.devctl.commands.check.run_cmd")
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

    @patch("dev.scripts.devctl.commands.check.run_cmd")
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

    @patch("dev.scripts.devctl.commands.check.run_cmd")
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
            "dev/scripts/check_mutation_score.py",
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

    @patch("dev.scripts.devctl.commands.check.run_cmd")
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


class CheckProcessSweepTests(TestCase):
    def test_parse_etime_seconds_handles_mm_ss_hh_mm_ss_and_days(self) -> None:
        self.assertEqual(check._parse_etime_seconds("05:30"), 330)
        self.assertEqual(check._parse_etime_seconds("01:05:30"), 3930)
        self.assertEqual(check._parse_etime_seconds("2-01:05:30"), 176730)
        self.assertIsNone(check._parse_etime_seconds("bad"))

    @patch("dev.scripts.devctl.commands.check.os.getpid", return_value=99999)
    @patch("dev.scripts.devctl.commands.check.subprocess.run")
    @patch("dev.scripts.devctl.commands.check.os.kill")
    def test_cleanup_kills_only_orphaned_voiceterm_test_binaries(
        self,
        kill_mock,
        run_mock,
        _getpid_mock,
    ) -> None:
        run_mock.return_value = SimpleNamespace(
            returncode=0,
            stdout=(
                "1234 1 05:00 /tmp/project/target/debug/deps/voiceterm-deadbeef --test-threads=4\n"
                "2222 777 05:00 /tmp/project/target/debug/deps/voiceterm-deadbeef --test-threads=4\n"
                "3333 1 05:00 /tmp/project/target/debug/deps/not-voiceterm-deadbeef\n"
            ),
            stderr="",
        )

        result = check._cleanup_orphaned_voiceterm_test_binaries("process-sweep-test", dry_run=False)

        kill_mock.assert_called_once_with(1234, check.signal.SIGKILL)
        self.assertEqual(result["detected_orphans"], 1)
        self.assertEqual(result["killed_pids"], [1234])
        self.assertEqual(result["returncode"], 0)

    @patch("dev.scripts.devctl.commands.check.subprocess.run", side_effect=OSError("blocked"))
    @patch("dev.scripts.devctl.commands.check.os.kill")
    def test_cleanup_reports_warning_when_ps_unavailable(self, kill_mock, _run_mock) -> None:
        result = check._cleanup_orphaned_voiceterm_test_binaries("process-sweep-test", dry_run=False)

        kill_mock.assert_not_called()
        self.assertEqual(result["detected_orphans"], 0)
        self.assertTrue(result["warnings"])
        self.assertEqual(result["returncode"], 0)
