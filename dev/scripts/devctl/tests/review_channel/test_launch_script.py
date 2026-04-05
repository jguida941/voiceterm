"""Tests for review-channel launch script generation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel._publisher import (
    AutoPollCadence,
    resolve_auto_poll_cadence,
)
from dev.scripts.devctl.review_channel.launch_script import build_session_script
from dev.scripts.devctl.review_channel.reviewer_follow_recovery import (
    ReviewerFollowRolloverInput,
    ReviewerFollowRolloverState,
    _build_rollover_action_args,
    _resolve_recovery_terminal,
)


def _build_script(
    *,
    headless: bool = False,
    log_path: Path | None = None,
    interaction_mode: str = "",
) -> str:
    """Build a session script in a temp dir and return its text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        script_path = root / "conductor.sh"
        build_session_script(
            provider="claude",
            repo_root=root,
            prompt="test prompt",
            script_path=script_path,
            log_path=log_path,
            resolve_cli_path_fn=lambda p: f"/usr/bin/{p}",
            headless=headless,
            interaction_mode=interaction_mode,
        )
        return script_path.read_text(encoding="utf-8")


class TestLaunchScriptHeadlessMode(unittest.TestCase):
    """Verify headless lifecycle flag propagation in generated scripts."""

    def test_default_headless_mode_is_off(self) -> None:
        script = _build_script(headless=False)
        self.assertIn('REVIEW_CHANNEL_HEADLESS_MODE="${REVIEW_CHANNEL_HEADLESS_MODE:-0}"', script)

    def test_headless_true_sets_default_to_one(self) -> None:
        script = _build_script(headless=True)
        self.assertIn('REVIEW_CHANNEL_HEADLESS_MODE="${REVIEW_CHANNEL_HEADLESS_MODE:-1}"', script)

    def test_headless_script_contains_restart_on_nonzero(self) -> None:
        script = _build_script(headless=True)
        self.assertIn('REVIEW_CHANNEL_HEADLESS_MODE" == "1"', script)
        self.assertIn("headless mode: conductor exited with status", script)
        self.assertIn("continue", script)

    def test_non_headless_script_exits_on_nonzero(self) -> None:
        script = _build_script(headless=False)
        self.assertIn('exit "$exit_code"', script)
        self.assertIn("leaving the session stopped so the failure stays visible", script)

    def test_headless_script_still_has_exit_fallback(self) -> None:
        """Even in headless=True the non-headless exit path is present for
        env-override scenarios where REVIEW_CHANNEL_HEADLESS_MODE=0."""
        script = _build_script(headless=True)
        self.assertIn('exit "$exit_code"', script)
        self.assertIn("leaving the session stopped", script)


class TestLaunchScriptBaseline(unittest.TestCase):
    """Baseline checks that existing script generation is not broken."""

    def test_script_contains_restart_loop(self) -> None:
        script = _build_script()
        self.assertIn("while true; do", script)
        self.assertIn("run_review_channel_once", script)

    def test_script_contains_exit_on_success_guard(self) -> None:
        script = _build_script()
        self.assertIn("REVIEW_CHANNEL_EXIT_ON_SUCCESS", script)

    def test_script_is_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            script_path = root / "conductor.sh"
            build_session_script(
                provider="codex",
                repo_root=root,
                prompt="test",
                script_path=script_path,
                resolve_cli_path_fn=lambda p: p,
            )
            import stat
            mode = script_path.stat().st_mode
            self.assertTrue(mode & stat.S_IXUSR)


class TestLaunchScriptInteractionMode(unittest.TestCase):
    """Verify interaction_mode=remote_control forces headless rollover."""

    def test_remote_control_forces_headless(self) -> None:
        script = _build_script(interaction_mode="remote_control")
        self.assertIn(
            'REVIEW_CHANNEL_HEADLESS_MODE="${REVIEW_CHANNEL_HEADLESS_MODE:-1}"',
            script,
        )

    def test_local_terminal_keeps_default_non_headless(self) -> None:
        script = _build_script(interaction_mode="local_terminal")
        self.assertIn(
            'REVIEW_CHANNEL_HEADLESS_MODE="${REVIEW_CHANNEL_HEADLESS_MODE:-0}"',
            script,
        )

    def test_empty_interaction_mode_keeps_default(self) -> None:
        script = _build_script(interaction_mode="")
        self.assertIn(
            'REVIEW_CHANNEL_HEADLESS_MODE="${REVIEW_CHANNEL_HEADLESS_MODE:-0}"',
            script,
        )


class TestResolveRecoveryTerminal(unittest.TestCase):
    """Verify _resolve_recovery_terminal respects operator_interaction_mode."""

    def test_remote_control_forces_none(self) -> None:
        args = SimpleNamespace(
            terminal="terminal-app",
            operator_interaction_mode="remote_control",
        )
        self.assertEqual(_resolve_recovery_terminal(args), "none")

    def test_local_terminal_inherits_parent(self) -> None:
        args = SimpleNamespace(
            terminal="terminal-app",
            operator_interaction_mode="local_terminal",
        )
        self.assertEqual(_resolve_recovery_terminal(args), "terminal-app")

    def test_missing_interaction_mode_falls_through(self) -> None:
        args = SimpleNamespace(terminal="none")
        self.assertEqual(_resolve_recovery_terminal(args), "none")

    def test_no_terminal_attr_defaults_to_terminal_app(self) -> None:
        args = SimpleNamespace()
        self.assertEqual(_resolve_recovery_terminal(args), "terminal-app")

    def test_dual_agent_mode_inherits_parent_terminal(self) -> None:
        args = SimpleNamespace(
            terminal="none",
            operator_interaction_mode="dual_agent",
        )
        self.assertEqual(_resolve_recovery_terminal(args), "none")


class TestAutoFollowPollCadence(unittest.TestCase):
    """Verify resolve_auto_poll_cadence respects operator interaction mode."""

    def test_remote_control_uses_tight_cadence(self) -> None:
        cadence = resolve_auto_poll_cadence(
            operator_interaction_mode="remote_control",
        )
        self.assertEqual(cadence.interval_seconds, 30)
        self.assertEqual(cadence.operator_interaction_mode, "remote_control")

    def test_local_terminal_uses_default_cadence(self) -> None:
        cadence = resolve_auto_poll_cadence(
            operator_interaction_mode="local_terminal",
        )
        self.assertEqual(cadence.interval_seconds, 150)

    def test_single_agent_uses_relaxed_cadence(self) -> None:
        cadence = resolve_auto_poll_cadence(
            operator_interaction_mode="single_agent",
        )
        self.assertEqual(cadence.interval_seconds, 300)

    def test_empty_mode_defaults_to_unresolved(self) -> None:
        cadence = resolve_auto_poll_cadence(operator_interaction_mode="")
        self.assertEqual(cadence.interval_seconds, 150)
        self.assertEqual(cadence.operator_interaction_mode, "unresolved")

    def test_explicit_interval_overrides_mode_default(self) -> None:
        cadence = resolve_auto_poll_cadence(
            operator_interaction_mode="remote_control",
            explicit_interval_seconds=60,
        )
        self.assertEqual(cadence.interval_seconds, 60)

    def test_cadence_interval_floor_is_one_second(self) -> None:
        cadence = resolve_auto_poll_cadence(
            operator_interaction_mode="remote_control",
            explicit_interval_seconds=0,
        )
        self.assertEqual(cadence.interval_seconds, 1)

    def test_unknown_mode_uses_default_interval(self) -> None:
        cadence = resolve_auto_poll_cadence(
            operator_interaction_mode="unknown_mode",
        )
        self.assertEqual(cadence.interval_seconds, 150)


class TestRolloverProviderCarried(unittest.TestCase):
    """Verify same-provider rollover state flows through args."""

    def test_rollover_args_carry_provider(self) -> None:
        base_args = SimpleNamespace(
            terminal="none",
            await_ack_seconds=180,
        )
        result = _build_rollover_action_args(
            base_args, rollover_provider="claude",
        )
        self.assertEqual(result.rollover_provider, "claude")

    def test_rollover_args_omit_provider_when_empty(self) -> None:
        base_args = SimpleNamespace(
            terminal="none",
            await_ack_seconds=180,
        )
        result = _build_rollover_action_args(base_args, rollover_provider="")
        self.assertFalse(hasattr(result, "rollover_provider"))

    def test_rollover_input_carries_provider(self) -> None:
        rollover_input = ReviewerFollowRolloverInput(
            args=SimpleNamespace(),
            repo_root=Path("/tmp"),
            paths={},
            report={},
            rollover_state=ReviewerFollowRolloverState(),
            rollover_provider="codex",
        )
        self.assertEqual(rollover_input.rollover_provider, "codex")


if __name__ == "__main__":
    unittest.main()
