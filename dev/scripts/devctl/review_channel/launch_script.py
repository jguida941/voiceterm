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


@dataclass(frozen=True)
class _SessionScriptHeader:
    repo_root: Path
    prompt: str
    headless: bool
    prepared_head_sha: str
    prepared_instruction_revision: str
    prepared_session_token: str
    review_state_path: Path | None


def build_session_script(
    *,
    provider: str,
    repo_root: Path,
    prompt: str,
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
            prompt=prompt,
            headless=headless,
            prepared_head_sha=prepared_head_sha,
            prepared_instruction_revision=prepared_instruction_revision,
            prepared_session_token=prepared_session_token,
            review_state_path=review_state_path,
        )
    )
    lines.extend(_launch_authority_check_lines())
    lines.extend(_run_once_opening(repo_root=repo_root))
    lines.extend(f"  {line}" for line in _provider_shell_prelude(provider))
    lines.extend([f"  {execution_command} \"$REVIEW_CHANNEL_PROMPT\"", "}", ""])
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
        f"cd {shlex.quote(str(header.repo_root))}",
        "PROMPT=$(cat <<'EOF_PROMPT'",
        header.prompt,
        "EOF_PROMPT",
        ")",
        'export REVIEW_CHANNEL_PROMPT="$PROMPT"',
        'REVIEW_CHANNEL_RESTART_DELAY_SECONDS="${REVIEW_CHANNEL_RESTART_DELAY_SECONDS:-2}"',
        'REVIEW_CHANNEL_EXIT_ON_SUCCESS="${REVIEW_CHANNEL_EXIT_ON_SUCCESS:-0}"',
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


def _launch_authority_check_lines() -> list[str]:
    return [
        "review_channel_launch_authority_check() {",
        "  python3 - \"$REVIEW_CHANNEL_REVIEW_STATE_PATH\" \"$REVIEW_CHANNEL_PREPARED_HEAD_SHA\" \"$REVIEW_CHANNEL_PREPARED_INSTRUCTION_REVISION\" \"$REVIEW_CHANNEL_PREPARED_SESSION_TOKEN\" <<'PY_AUTHORITY'",
        "import hashlib",
        "import json",
        "import subprocess",
        "import sys",
        "",
        f"EXIT_CODE = {NON_RESTARTABLE_LAUNCH_AUTHORITY_EXIT_CODE}",
        "review_state_path, expected_head, expected_revision, expected_token = sys.argv[1:5]",
        "",
        "def fail(message):",
        "    print(f\"[review-channel] launch authority stale: {message}\", file=sys.stderr)",
        "    raise SystemExit(EXIT_CODE)",
        "",
        "def text(value):",
        "    return str(value or \"\").strip()",
        "",
        "def mapping(value):",
        "    return value if isinstance(value, dict) else {}",
        "",
        "if not any((expected_head, expected_revision, expected_token)):",
        "    raise SystemExit(0)",
        "",
        "try:",
        "    live_head = subprocess.run(",
        "        [\"git\", \"rev-parse\", \"HEAD\"],",
        "        capture_output=True,",
        "        text=True,",
        "        timeout=5,",
        "        check=False,",
        "    )",
        "except Exception as exc:",
        "    fail(f\"could not read git HEAD: {exc}\")",
        "if live_head.returncode != 0:",
        "    fail(\"could not read git HEAD\")",
        "current_head = live_head.stdout.strip()",
        "if expected_head and current_head != expected_head:",
        "    fail(f\"prepared_head_sha={expected_head} current_head_sha={current_head}\")",
        "",
        "if not review_state_path:",
        "    fail(\"review_state_path missing\")",
        "try:",
        "    with open(review_state_path, \"r\", encoding=\"utf-8\") as handle:",
        "        review_state = json.load(handle)",
        "except Exception as exc:",
        "    fail(f\"could not read typed review state {review_state_path}: {exc}\")",
        "review = mapping(review_state.get(\"review\"))",
        "bridge = mapping(review_state.get(\"bridge\"))",
        "current_session = mapping(review_state.get(\"current_session\"))",
        "current_revision = text(",
        "    current_session.get(\"current_instruction_revision\")",
        "    or bridge.get(\"current_instruction_revision\")",
        ")",
        "if expected_revision and current_revision != expected_revision:",
        "    fail(",
        "        f\"prepared_instruction_revision={expected_revision} \"",
        "        f\"current_instruction_revision={current_revision}\"",
        "    )",
        "session_id = text(review.get(\"session_id\") or \"markdown-bridge\")",
        "last_poll = text(bridge.get(\"last_codex_poll_utc\"))",
        "token_payload = \"\\0\".join(",
        "    part for part in (session_id, current_revision, last_poll) if part",
        ")",
        "current_token = (",
        "    hashlib.sha256(token_payload.encode(\"utf-8\")).hexdigest()[:16]",
        "    if token_payload",
        "    else \"\"",
        ")",
        "if expected_token and current_token != expected_token:",
        "    fail(f\"prepared_session_token={expected_token} current_session_token={current_token}\")",
        "raise SystemExit(0)",
        "PY_AUTHORITY",
        "}",
        "",
        "review_channel_exit_is_non_restartable() {",
        "  local exit_code=\"$1\"",
        "  local code",
        "  for code in ${=REVIEW_CHANNEL_NON_RESTARTABLE_EXIT_CODES}; do",
        "    if [[ \"$exit_code\" == \"$code\" ]]; then",
        "      return 0",
        "    fi",
        "  done",
        "  return 1",
        "}",
        "",
    ]


def _run_once_opening(*, repo_root: Path) -> list[str]:
    return [
        "run_review_channel_once() {",
        f"  cd {shlex.quote(str(repo_root))}",
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
