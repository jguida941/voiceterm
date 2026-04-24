"""Script builders for review-channel conductor launches."""

from __future__ import annotations

import shlex
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..approval_mode import (
    DEFAULT_APPROVAL_MODE,
    normalize_approval_mode,
    provider_args_for_approval_mode,
)
from .launch_authority import NON_RESTARTABLE_LAUNCH_AUTHORITY_EXIT_CODE
from .launch_script_authority import launch_authority_check_lines as _launch_authority_check_lines
from .launch_script_watchdog import inactivity_watchdog_lines as _inactivity_watchdog_lines


@dataclass(frozen=True)
class _SessionScriptHeader:
    repo_root: Path
    workspace_root: Path
    prompt: str
    role: str
    headless: bool
    prepared_head_sha: str
    prepared_instruction_revision: str
    prepared_session_token: str
    review_state_path: Path | None


def build_session_script(
    *,
    provider: str,
    repo_root: Path,
    workspace_root: Path | None = None,
    prompt: str,
    role: str = "",
    script_path: Path,
    log_path: Path | None = None,
    resolve_cli_path_fn: Callable[[str], str],
    approval_mode: str = DEFAULT_APPROVAL_MODE,
    dangerous: bool = False,
    headless: bool = False,
    interaction_mode: str = "",
    prepared_head_sha: str = "",
    prepared_instruction_revision: str = "",
    prepared_session_token: str = "",
    review_state_path: Path | None = None,
) -> Path:
    """Write one launch script for a conductor session."""
    if interaction_mode == "remote_control":
        headless = True
    effective_workspace_root = (
        workspace_root.resolve() if workspace_root is not None else repo_root.resolve()
    )
    cli_path = resolve_cli_path_fn(provider)
    provider_args = _provider_args(
        provider=provider,
        repo_root=repo_root,
        approval_mode=approval_mode,
        dangerous=dangerous,
    )
    execution_command = shlex.join([cli_path, *provider_args])
    inner_script_command = shlex.join([str(script_path), "__review_channel_inner"])
    lines = _header_lines(
        _SessionScriptHeader(
            repo_root=repo_root,
            workspace_root=effective_workspace_root,
            prompt=prompt,
            role=str(role or "").strip().lower(),
            headless=headless,
            prepared_head_sha=prepared_head_sha,
            prepared_instruction_revision=prepared_instruction_revision,
            prepared_session_token=prepared_session_token,
            review_state_path=review_state_path,
        )
    )
    lines.extend(_launch_authority_check_lines())
    lines.extend(_inactivity_watchdog_lines(provider))
    lines.extend(_run_once_opening(workspace_root=effective_workspace_root))
    lines.extend(f"  {line}" for line in _provider_shell_prelude(provider))
    # Spawn the conductor in background, then run the inactivity watchdog
    # in parallel so SIGINT can be delivered when the conductor stalls
    # without exiting (operator-authorized 2026-04-24 path 1 fix). When
    # `REVIEW_CHANNEL_WATCHDOG_DISABLED=1`, fall back to the legacy
    # blocking invocation so anyone reproducing the prior behavior can
    # opt out.
    lines.extend(
        [
            f'  if [[ "$REVIEW_CHANNEL_WATCHDOG_DISABLED" == "1" ]]; then',
            f'    {execution_command} "$REVIEW_CHANNEL_PROMPT"',
            "    return $?",
            "  fi",
            f'  {execution_command} "$REVIEW_CHANNEL_PROMPT" &',
            "  local conductor_pid=$!",
            "  review_channel_inactivity_watchdog "
            '"$conductor_pid" '
            '"$REVIEW_CHANNEL_INACTIVITY_TIMEOUT_SECONDS" '
            '"$REVIEW_CHANNEL_WATCHDOG_STARTUP_GRACE_SECONDS" '
            '"$REVIEW_CHANNEL_WATCHDOG_POLL_SECONDS" &',
            "  local watchdog_pid=$!",
            '  wait "$conductor_pid"',
            "  local conductor_rc=$?",
            '  kill "$watchdog_pid" 2>/dev/null || true',
            '  wait "$watchdog_pid" 2>/dev/null || true',
            '  return "$conductor_rc"',
            "}",
            "",
        ]
    )
    if log_path is not None:
        lines.extend(_log_wrapper_lines(log_path, inner_script_command))
    lines.extend(_supervision_loop_lines(provider))
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("\n".join(lines), encoding="utf-8")
    script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)
    return script_path


def _header_lines(header: _SessionScriptHeader) -> list[str]:
    return [
        "#!/bin/zsh",
        "set -euo pipefail",
        "",
        f"REVIEW_CHANNEL_CONTROL_ROOT={shlex.quote(str(header.repo_root.resolve()))}",
        f"REVIEW_CHANNEL_WORKSPACE_ROOT={shlex.quote(str(header.workspace_root))}",
        f"cd {shlex.quote(str(header.workspace_root))}",
        "PROMPT=$(cat <<'EOF_PROMPT'",
        header.prompt,
        "EOF_PROMPT",
        ")",
        'export REVIEW_CHANNEL_PROMPT="$PROMPT"',
        f"REVIEW_CHANNEL_CALLER_ROLE={shlex.quote(header.role)}",
        'export REVIEW_CHANNEL_CALLER_ROLE',
        'export DEVCTL_CALLER_ROLE="${DEVCTL_CALLER_ROLE:-$REVIEW_CHANNEL_CALLER_ROLE}"',
        'REVIEW_CHANNEL_RESTART_DELAY_SECONDS="${REVIEW_CHANNEL_RESTART_DELAY_SECONDS:-2}"',
        'REVIEW_CHANNEL_EXIT_ON_SUCCESS="${REVIEW_CHANNEL_EXIT_ON_SUCCESS:-0}"',
        # Inactivity-watchdog defaults (operator-authorized 2026-04-24 path 1):
        # codex CLI sometimes idles after `task_complete` instead of exiting,
        # so the supervision `while true` loop never relaunches. The watchdog
        # tails the latest `~/.codex/sessions/<date>/rollout-*.jsonl` mtime
        # and SIGINTs codex when no new event has landed for the timeout
        # window, allowing the existing supervision loop to relaunch.
        'REVIEW_CHANNEL_INACTIVITY_TIMEOUT_SECONDS="${REVIEW_CHANNEL_INACTIVITY_TIMEOUT_SECONDS:-600}"',
        'REVIEW_CHANNEL_WATCHDOG_STARTUP_GRACE_SECONDS="${REVIEW_CHANNEL_WATCHDOG_STARTUP_GRACE_SECONDS:-60}"',
        'REVIEW_CHANNEL_WATCHDOG_POLL_SECONDS="${REVIEW_CHANNEL_WATCHDOG_POLL_SECONDS:-30}"',
        'REVIEW_CHANNEL_WATCHDOG_DISABLED="${REVIEW_CHANNEL_WATCHDOG_DISABLED:-0}"',
        'REVIEW_CHANNEL_CODEX_SESSIONS_ROOT="${REVIEW_CHANNEL_CODEX_SESSIONS_ROOT:-$HOME/.codex/sessions}"',
        f'REVIEW_CHANNEL_HEADLESS_MODE="${{REVIEW_CHANNEL_HEADLESS_MODE:-{"1" if header.headless else "0"}}}"',
        f'REVIEW_CHANNEL_NON_RESTARTABLE_EXIT_CODES="${{REVIEW_CHANNEL_NON_RESTARTABLE_EXIT_CODES:-{NON_RESTARTABLE_LAUNCH_AUTHORITY_EXIT_CODE}}}"',
        f"REVIEW_CHANNEL_PREPARED_HEAD_SHA={shlex.quote(header.prepared_head_sha)}",
        "REVIEW_CHANNEL_PREPARED_INSTRUCTION_REVISION="
        f"{shlex.quote(header.prepared_instruction_revision)}",
        f"REVIEW_CHANNEL_PREPARED_SESSION_TOKEN={shlex.quote(header.prepared_session_token)}",
        "REVIEW_CHANNEL_REVIEW_STATE_PATH="
        f"{shlex.quote(str(header.review_state_path) if header.review_state_path is not None else '')}",
        "",
    ]




def _run_once_opening(*, workspace_root: Path) -> list[str]:
    return [
        "run_review_channel_once() {",
        f"  cd {shlex.quote(str(workspace_root))}",
        "  review_channel_launch_authority_check || return $?",
    ]


def _log_wrapper_lines(log_path: Path, inner_script_command: str) -> list[str]:
    script_command = shlex.join(
        [
            "script",
            "-q",
            "-F",
            "-t",
            "0",
            str(log_path),
            "/bin/zsh",
            "-lc",
            inner_script_command,
        ]
    )
    return [
        f"mkdir -p {shlex.quote(str(log_path.parent))}",
        'if [[ "${1:-}" != "__review_channel_inner" ]] && command -v script >/dev/null 2>&1; then',
        f"  exec {script_command}",
        "fi",
    ]


def _supervision_loop_lines(provider: str) -> list[str]:
    return [
        "restart_count=0",
        "while true; do",
        "  if run_review_channel_once; then",
        "    exit_code=0",
        "  else",
        "    exit_code=$?",
        "  fi",
        '  if [[ "$exit_code" == "0" ]]; then',
        '    if [[ "$REVIEW_CHANNEL_EXIT_ON_SUCCESS" == "1" ]]; then',
        "      exit 0",
        "    fi",
        "    restart_count=$((restart_count + 1))",
        "    printf '%s\\n' "
        f"\"[review-channel] {provider} conductor exited cleanly; relaunching "
        "from repo state in ${REVIEW_CHANNEL_RESTART_DELAY_SECONDS}s "
        "(restart #${restart_count}). Set REVIEW_CHANNEL_EXIT_ON_SUCCESS=1 to "
        'disable supervised relaunch for this invocation."',
        '    sleep "$REVIEW_CHANNEL_RESTART_DELAY_SECONDS"',
        "    continue",
        "  fi",
        '  if [[ "$REVIEW_CHANNEL_HEADLESS_MODE" == "1" ]]; then',
        "    if review_channel_exit_is_non_restartable \"$exit_code\"; then",
        "      printf '%s\\n' "
        f"\"[review-channel] {provider} headless mode: conductor exited with "
        "non-restartable status ${exit_code}; leaving the session stopped so "
        'stale authority remains visible." >&2',
        '      exit "$exit_code"',
        "    fi",
        "    restart_count=$((restart_count + 1))",
        "    printf '%s\\n' "
        f"\"[review-channel] {provider} headless mode: conductor exited with "
        "status ${exit_code}; restarting in "
        '${REVIEW_CHANNEL_RESTART_DELAY_SECONDS}s (restart #${restart_count})." >&2',
        '    sleep "$REVIEW_CHANNEL_RESTART_DELAY_SECONDS"',
        "    continue",
        "  fi",
        "  printf '%s\\n' "
        f"\"[review-channel] {provider} conductor exited with status "
        "${exit_code}; leaving the session stopped so the failure stays visible.\" >&2",
        '  exit "$exit_code"',
        "done",
        "",
    ]


def _provider_shell_prelude(provider: str) -> list[str]:
    if provider == "claude":
        return [
            "# Claude Code refuses nested launches when this marker is inherited.",
            "unset CLAUDECODE || true",
        ]
    return []


def _provider_args(
    *,
    provider: str,
    repo_root: Path,
    approval_mode: str,
    dangerous: bool,
) -> list[str]:
    resolved_mode = normalize_approval_mode(
        approval_mode,
        dangerous=dangerous,
    )
    return provider_args_for_approval_mode(
        provider=provider,
        repo_root=repo_root,
        approval_mode=resolved_mode,
    )
