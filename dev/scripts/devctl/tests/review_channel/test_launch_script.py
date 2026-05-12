"""Tests for review-channel launch script generation."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.approval_mode import BypassLifecycleRequired
from dev.scripts.devctl.commands.review_channel._publisher import (
    resolve_auto_poll_cadence,
)
from dev.scripts.devctl.commands.review_channel.launcher_discipline import (
    validate_visible_launch_in_local_mode,
)
from dev.scripts.devctl.review_channel.launch_script import build_session_script
from dev.scripts.devctl.review_channel.launch_authority import (
    NON_RESTARTABLE_LAUNCH_AUTHORITY_EXIT_CODE,
    build_prepared_launch_authority,
    current_head_sha,
    launch_session_token,
)
from dev.scripts.devctl.review_channel.peer_recovery import (
    build_implementer_recover_command,
    build_live_relaunch_command,
)
from dev.scripts.devctl.review_channel.reviewer_follow_recovery import (
    ReviewerFollowRolloverInput,
    ReviewerFollowRolloverState,
)
from dev.scripts.devctl.review_channel.reviewer_follow_recovery_support import (
    build_rollover_action_args,
    resolve_recovery_terminal,
)
from dev.scripts.devctl.review_channel.terminal_mode import resolve_terminal_mode
from dev.scripts.devctl.runtime.lifetime_bypass_mode import (
    BypassAuthorityScope,
    BypassEvaluationInput,
    BypassRequest,
    evaluate_bypass_request,
)


def _active_bypass_lifecycle():
    return evaluate_bypass_request(
        BypassRequest(
            request_id="launch-trusted",
            scope=BypassAuthorityScope.EDIT_ONLY,
            reason="operator approved trusted launch",
            actor="operator",
            requested_at_utc="2026-05-12T16:10:00Z",
            target_surface="runtime:review-channel-launch",
            evidence_refs=("packet:rev_pkt_3847",),
        ),
        BypassEvaluationInput(
            operator_signature="operator",
            ai_approval_evidence="packet:rev_pkt_3847",
            evaluated_at_utc="2026-05-12T16:10:01Z",
        ),
    )


def _build_script(
    *,
    headless: bool = False,
    log_path: Path | None = None,
    interaction_mode: str = "",
    role: str = "",
    workspace_root: Path | None = None,
) -> str:
    """Build a session script in a temp dir and return its text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        script_path = root / "conductor.sh"
        build_session_script(
            provider="claude",
            repo_root=root,
            workspace_root=workspace_root,
            prompt="test prompt",
            role=role,
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

    def test_script_exports_caller_role_for_devctl_children(self) -> None:
        script = _build_script(role="reviewer")
        self.assertIn("REVIEW_CHANNEL_CALLER_ROLE=reviewer", script)
        self.assertIn('export DEVCTL_CALLER_ROLE="${DEVCTL_CALLER_ROLE:-$REVIEW_CHANNEL_CALLER_ROLE}"', script)

    def test_script_uses_workspace_root_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace_root = (root / "../worker-lane").resolve()
            script = _build_script(workspace_root=workspace_root)
            self.assertIn(
                f"REVIEW_CHANNEL_WORKSPACE_ROOT={workspace_root}",
                script,
            )
            self.assertIn(f"cd {workspace_root}", script)

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


class TestLaunchScriptAuthority(unittest.TestCase):
    """Verify prepared launcher scripts fail closed on stale typed authority."""

    def _write_review_state(
        self,
        root: Path,
        *,
        instruction_revision: str,
        last_codex_poll_utc: str,
        session_id: str = "markdown-bridge",
    ) -> Path:
        review_state_path = root / "review_state.json"
        review_state_path.write_text(
            json.dumps(
                {
                    "review": {"session_id": session_id},
                    "current_session": {
                        "current_instruction_revision": instruction_revision,
                    },
                    "bridge": {
                        "current_instruction_revision": instruction_revision,
                        "last_codex_poll_utc": last_codex_poll_utc,
                    },
                }
            ),
            encoding="utf-8",
        )
        return review_state_path

    def _run_authority_script(
        self,
        *,
        review_state_revision: str,
        prepared_revision: str = "rev-1",
        headless: bool = True,
        review_state_session_id: str = "markdown-bridge",
        prepared_session_id: str = "markdown-bridge",
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            last_poll = "2026-04-07T00:00:00Z"
            review_state_path = self._write_review_state(
                root,
                instruction_revision=review_state_revision,
                last_codex_poll_utc=last_poll,
                session_id=review_state_session_id,
            )
            script_path = root / "conductor.sh"
            repo_root = Path.cwd()
            build_session_script(
                provider="claude",
                repo_root=repo_root,
                prompt="test prompt",
                script_path=script_path,
                resolve_cli_path_fn=lambda _provider: "/usr/bin/true",
                headless=headless,
                prepared_head_sha=current_head_sha(repo_root),
                prepared_instruction_revision=prepared_revision,
                prepared_session_token=launch_session_token(
                    session_id=prepared_session_id,
                    instruction_revision=prepared_revision,
                    last_codex_poll_utc=last_poll,
                ),
                review_state_path=review_state_path,
            )
            env = {**os.environ, "REVIEW_CHANNEL_EXIT_ON_SUCCESS": "1"}
            return subprocess.run(
                ["/bin/zsh", str(script_path)],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
                check=False,
            )

    def test_fresh_authority_allows_provider_start(self) -> None:
        result = self._run_authority_script(review_state_revision="rev-1")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_compatible_session_ids_do_not_stale_launch_authority(self) -> None:
        result = self._run_authority_script(
            review_state_revision="rev-1",
            review_state_session_id="local-review",
            prepared_session_id="markdown-bridge",
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_stale_instruction_revision_exits_non_restartable_headless(self) -> None:
        result = self._run_authority_script(review_state_revision="rev-2")

        self.assertEqual(
            result.returncode,
            NON_RESTARTABLE_LAUNCH_AUTHORITY_EXIT_CODE,
        )
        self.assertIn("launch authority stale", result.stderr)
        self.assertIn("non-restartable status", result.stderr)
        self.assertNotIn("restarting in", result.stderr)

    def test_prepared_authority_ignores_stale_bridge_revision_when_typed_state_blank(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            review_state_path = root / "review_state.json"
            review_state_path.write_text(
                json.dumps(
                    {
                        "review": {"session_id": "markdown-bridge"},
                        "current_session": {"current_instruction_revision": ""},
                        "bridge": {
                            "current_instruction_revision": "",
                            "last_codex_poll_utc": "2026-04-15T23:08:48Z",
                        },
                    }
                ),
                encoding="utf-8",
            )
            bridge_path = root / "bridge.md"
            bridge_path.write_text(
                "\n".join(
                    (
                        "- Current instruction revision: `stale-bridge-rev`",
                        "- Last Codex poll: `2026-04-15T23:08:48Z`",
                    )
                ),
                encoding="utf-8",
            )

            authority = build_prepared_launch_authority(
                repo_root=Path.cwd(),
                bridge_path=bridge_path,
                bridge_liveness={
                    "current_instruction_revision": "stale-liveness-rev",
                    "last_codex_poll_utc": "2026-04-15T23:08:48Z",
                },
                review_state_path=review_state_path,
            )

        self.assertEqual(authority.instruction_revision, "")
        self.assertEqual(
            authority.session_token,
            launch_session_token(
                session_id="markdown-bridge",
                instruction_revision="",
                last_codex_poll_utc="2026-04-15T23:08:48Z",
            ),
        )


class TestResolveRecoveryTerminal(unittest.TestCase):
    """Verify resolve_recovery_terminal respects operator_interaction_mode."""

    def test_remote_control_forces_none(self) -> None:
        args = SimpleNamespace(
            terminal="terminal-app",
            operator_interaction_mode="remote_control",
        )
        self.assertEqual(resolve_recovery_terminal(args), "none")

    def test_local_terminal_inherits_parent(self) -> None:
        args = SimpleNamespace(
            terminal="terminal-app",
            operator_interaction_mode="local_terminal",
        )
        self.assertEqual(resolve_recovery_terminal(args), "terminal-app")

    def test_missing_interaction_mode_falls_through(self) -> None:
        args = SimpleNamespace(terminal="none")
        self.assertEqual(resolve_recovery_terminal(args), "none")

    def test_no_terminal_attr_defaults_to_terminal_app(self) -> None:
        args = SimpleNamespace()
        self.assertEqual(resolve_recovery_terminal(args), "terminal-app")

    def test_dual_agent_mode_inherits_parent_terminal(self) -> None:
        args = SimpleNamespace(
            terminal="none",
            operator_interaction_mode="dual_agent",
        )
        self.assertEqual(resolve_recovery_terminal(args), "none")


class TestResolveTerminalMode(unittest.TestCase):
    """Verify the shared review-channel terminal policy."""

    def test_explicit_terminal_wins(self) -> None:
        self.assertEqual(
            resolve_terminal_mode(
                "terminal-app",
                operator_interaction_mode="remote_control",
                parent_terminal="none",
            ),
            "terminal-app",
        )

    def test_remote_control_defaults_headless(self) -> None:
        self.assertEqual(
            resolve_terminal_mode(operator_interaction_mode="remote_control"),
            "none",
        )

    def test_dual_agent_defaults_headless(self) -> None:
        self.assertEqual(
            resolve_terminal_mode(operator_interaction_mode="dual_agent"),
            "none",
        )

    def test_unresolved_defaults_headless(self) -> None:
        self.assertEqual(
            resolve_terminal_mode(operator_interaction_mode="unresolved"),
            "none",
        )

    def test_parent_headless_is_inherited(self) -> None:
        self.assertEqual(resolve_terminal_mode(parent_terminal="none"), "none")

    def test_local_default_is_visible(self) -> None:
        self.assertEqual(resolve_terminal_mode(), "terminal-app")

    def test_remote_control_visible_terminal_launch_is_denied(self) -> None:
        verdict = validate_visible_launch_in_local_mode(
            interaction_mode="remote_control",
            terminal_arg="terminal-app",
        )
        self.assertFalse(verdict.allowed)
        self.assertEqual(verdict.denial_reason, "visible_launch_in_remote_control")

    def test_local_terminal_visible_terminal_launch_is_allowed(self) -> None:
        verdict = validate_visible_launch_in_local_mode(
            interaction_mode="local_terminal",
            terminal_arg="terminal-app",
        )
        self.assertTrue(verdict.allowed)


class TestRecoveryCommands(unittest.TestCase):
    """Verify human-facing recovery commands respect operator interaction mode."""

    def test_live_relaunch_defaults_to_terminal_app(self) -> None:
        command = build_live_relaunch_command()
        self.assertIn("--action launch", command)
        self.assertIn("--terminal terminal-app", command)

    def test_live_relaunch_remote_control_stays_headless(self) -> None:
        command = build_live_relaunch_command("remote_control")
        self.assertIn("--action launch", command)
        self.assertIn("--terminal none", command)

    def test_implementer_recover_defaults_to_terminal_app(self) -> None:
        command = build_implementer_recover_command()
        self.assertIn("--action recover", command)
        self.assertIn("--terminal terminal-app", command)

    def test_implementer_recover_remote_control_stays_headless(self) -> None:
        command = build_implementer_recover_command("remote_control")
        self.assertIn("--action recover", command)
        self.assertIn("--terminal none", command)


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
        result = build_rollover_action_args(
            base_args, rollover_provider="claude",
        )
        self.assertEqual(result.rollover_provider, "claude")

    def test_rollover_args_omit_provider_when_empty(self) -> None:
        base_args = SimpleNamespace(
            terminal="none",
            await_ack_seconds=180,
        )
        result = build_rollover_action_args(base_args, rollover_provider="")
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


class TestInactivityWatchdog(unittest.TestCase):
    """Operator-authorized 2026-04-24 path 1: idle-watchdog template.

    Codex CLI sometimes idles after `task_complete` instead of exiting,
    so the supervision `while true` loop in `_supervision_loop_lines`
    never relaunches. The watchdog reaped by these tests tails the
    latest rollout mtime and SIGINTs the conductor when no new event
    has landed for ``REVIEW_CHANNEL_INACTIVITY_TIMEOUT_SECONDS``.
    """

    def _build_script(self, provider: str = "codex") -> str:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            script_path = tmp_path / f"{provider}-conductor.sh"
            build_session_script(
                provider=provider,
                repo_root=tmp_path,
                prompt="test prompt",
                role="reviewer" if provider == "codex" else "implementer",
                script_path=script_path,
                resolve_cli_path_fn=lambda _provider: "/usr/bin/true",
                interaction_mode="remote_control",
            )
            return script_path.read_text(encoding="utf-8")

    def test_codex_script_includes_watchdog_function(self) -> None:
        script = self._build_script("codex")
        self.assertIn("review_channel_inactivity_watchdog()", script)
        self.assertIn("review_channel_latest_rollout_mtime()", script)

    def test_codex_script_wraps_invocation_in_background_with_watchdog(self) -> None:
        """The conductor invocation must run in `&` so watchdog can SIGINT it."""
        script = self._build_script("codex")
        # Conductor command (built by `_provider_args`) is followed by &
        self.assertIn('"$REVIEW_CHANNEL_PROMPT" &', script)
        self.assertIn("local conductor_pid=$!", script)
        self.assertIn("review_channel_inactivity_watchdog \"$conductor_pid\"", script)
        self.assertIn('wait "$conductor_pid"', script)

    def test_watchdog_disabled_path_falls_back_to_blocking_invocation(self) -> None:
        """When REVIEW_CHANNEL_WATCHDOG_DISABLED=1, run the legacy blocking call."""
        script = self._build_script("codex")
        self.assertIn('if [[ "$REVIEW_CHANNEL_WATCHDOG_DISABLED" == "1" ]]; then', script)

    def test_inactivity_env_vars_have_defaults(self) -> None:
        """Defaults: 600s timeout, 60s grace, 30s poll."""
        script = self._build_script("codex")
        self.assertIn(
            'REVIEW_CHANNEL_INACTIVITY_TIMEOUT_SECONDS="${REVIEW_CHANNEL_INACTIVITY_TIMEOUT_SECONDS:-600}"',
            script,
        )
        self.assertIn(
            'REVIEW_CHANNEL_WATCHDOG_STARTUP_GRACE_SECONDS="${REVIEW_CHANNEL_WATCHDOG_STARTUP_GRACE_SECONDS:-60}"',
            script,
        )
        self.assertIn(
            'REVIEW_CHANNEL_WATCHDOG_POLL_SECONDS="${REVIEW_CHANNEL_WATCHDOG_POLL_SECONDS:-30}"',
            script,
        )

    def test_watchdog_provider_label_appears_in_log_message(self) -> None:
        """Each provider's watchdog must self-identify in its SIGINT log line."""
        codex_script = self._build_script("codex")
        claude_script = self._build_script("claude")
        self.assertIn("[review-channel] codex inactivity-watchdog", codex_script)
        self.assertIn("[review-channel] claude inactivity-watchdog", claude_script)

    def test_watchdog_polls_codex_sessions_root(self) -> None:
        """Watchdog reads ~/.codex/sessions/<date>/rollout-*.jsonl mtime."""
        script = self._build_script("codex")
        self.assertIn(
            'REVIEW_CHANNEL_CODEX_SESSIONS_ROOT="${REVIEW_CHANNEL_CODEX_SESSIONS_ROOT:-$HOME/.codex/sessions}"',
            script,
        )
        self.assertIn("rollout-*.jsonl", script)

    def test_codex_script_invokes_task_complete_handoff_guard(self) -> None:
        """Codex session-end must backstop task_complete with a typed packet."""
        script = self._build_script("codex")
        self.assertIn("review_channel_task_complete_handoff_guard()", script)
        self.assertIn(
            "python3 -m dev.scripts.devctl.review_channel.task_complete_handoff_guard",
            script,
        )
        self.assertIn(
            'review_channel_task_complete_handoff_guard "$exit_code"',
            script,
        )
        self.assertIn(
            'REVIEW_CHANNEL_HANDOFF_GUARD_EVIDENCE="${REVIEW_CHANNEL_HANDOFF_GUARD_EVIDENCE:---profile ci}"',
            script,
        )


class TestLaunchScriptCodexExecHeadlessSwitch(unittest.TestCase):
    """Finding D regression guards: headless codex uses non-interactive `codex exec`.

    The interactive `codex` CLI checks isatty(0) at startup and exits with
    `Error: stdin is not a terminal` when launched from a backgrounded
    `script -q -F` pty whose own stdin came from a non-tty parent. Headless
    launches must use the `codex exec` subcommand which is non-interactive
    by design and does not gate on isatty.
    """

    def _build_codex_script(
        self,
        *,
        headless: bool,
        interaction_mode: str = "",
    ) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            script_path = root / "conductor.sh"
            build_session_script(
                provider="codex",
                repo_root=root,
                prompt="test prompt",
                script_path=script_path,
                resolve_cli_path_fn=lambda _p: "/opt/homebrew/bin/codex",
                headless=headless,
                interaction_mode=interaction_mode,
                approval_mode="balanced",
            )
            return script_path.read_text(encoding="utf-8")

    def test_headless_codex_uses_exec_subcommand(self) -> None:
        script = self._build_codex_script(headless=True)
        self.assertIn("/opt/homebrew/bin/codex exec ", script)

    def test_remote_control_forces_codex_exec(self) -> None:
        script = self._build_codex_script(
            headless=False,
            interaction_mode="remote_control",
        )
        self.assertIn("/opt/homebrew/bin/codex exec ", script)

    def test_non_headless_codex_uses_interactive(self) -> None:
        script = self._build_codex_script(headless=False)
        # Interactive codex appears WITHOUT the `exec` subcommand.
        # The space disambiguates it from "codex execute" or similar.
        self.assertNotIn("/opt/homebrew/bin/codex exec ", script)
        self.assertIn("/opt/homebrew/bin/codex ", script)

    def test_headless_codex_strips_ask_for_approval(self) -> None:
        script = self._build_codex_script(headless=True)
        # `codex exec` is non-interactive; the interactive
        # `--ask-for-approval` flag is invalid there and would crash codex
        # at parse time. Filter it out.
        self.assertNotIn("--ask-for-approval", script.split("codex exec ", 1)[1].split("\n", 1)[0])

    def test_trusted_codex_requires_active_bypass_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaises(BypassLifecycleRequired):
                build_session_script(
                    provider="codex",
                    repo_root=root,
                    prompt="test prompt",
                    script_path=root / "conductor.sh",
                    resolve_cli_path_fn=lambda _p: "/opt/homebrew/bin/codex",
                    approval_mode="trusted",
                )

    def test_trusted_codex_uses_typed_bypass_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            script_path = root / "conductor.sh"
            build_session_script(
                provider="codex",
                repo_root=root,
                prompt="test prompt",
                script_path=script_path,
                resolve_cli_path_fn=lambda _p: "/opt/homebrew/bin/codex",
                approval_mode="trusted",
                bypass_lifecycle=_active_bypass_lifecycle(),
            )
            script = script_path.read_text(encoding="utf-8")
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", script)

    def test_headless_claude_does_not_use_exec(self) -> None:
        # The codex-exec switch must be codex-specific. Claude headless
        # already works without isatty issues and has no `claude exec`
        # subcommand; the switch must not affect the claude lane.
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            script_path = root / "conductor.sh"
            build_session_script(
                provider="claude",
                repo_root=root,
                prompt="test prompt",
                script_path=script_path,
                resolve_cli_path_fn=lambda _p: "/usr/local/bin/claude",
                headless=True,
            )
            script = script_path.read_text(encoding="utf-8")
        self.assertNotIn("/usr/local/bin/claude exec ", script)


class TestStripInteractiveOnlyArgs(unittest.TestCase):
    """Unit tests for the `--ask-for-approval` filtering helper."""

    def test_strips_space_separated_form(self) -> None:
        from dev.scripts.devctl.review_channel.launch_script import (
            _strip_interactive_only_args,
        )
        result = _strip_interactive_only_args(
            ["-C", "/repo", "--ask-for-approval", "on-request", "--sandbox", "workspace-write"]
        )
        self.assertEqual(
            result, ["-C", "/repo", "--sandbox", "workspace-write"]
        )

    def test_strips_equals_form(self) -> None:
        from dev.scripts.devctl.review_channel.launch_script import (
            _strip_interactive_only_args,
        )
        result = _strip_interactive_only_args(
            ["-C", "/repo", "--ask-for-approval=on-request", "--sandbox", "workspace-write"]
        )
        self.assertEqual(
            result, ["-C", "/repo", "--sandbox", "workspace-write"]
        )

    def test_no_op_when_flag_absent(self) -> None:
        from dev.scripts.devctl.review_channel.launch_script import (
            _strip_interactive_only_args,
        )
        args = ["-C", "/repo", "--sandbox", "workspace-write"]
        self.assertEqual(_strip_interactive_only_args(args), args)


if __name__ == "__main__":
    unittest.main()
