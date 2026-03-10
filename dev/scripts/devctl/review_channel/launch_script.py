"""Script builders for review-channel conductor launches."""

from __future__ import annotations

import shlex
import stat
from pathlib import Path
from typing import Callable

from ..approval_mode import (
    DEFAULT_APPROVAL_MODE,
    normalize_approval_mode,
    provider_args_for_approval_mode,
)


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
) -> Path:
    """Write one launch script for a conductor session."""
    cli_path = resolve_cli_path_fn(provider)
    provider_args = _provider_args(
        provider=provider,
        repo_root=repo_root,
        approval_mode=approval_mode,
        dangerous=dangerous,
    )
    execution_command = shlex.join([cli_path, *provider_args])
    inner_script_command = shlex.join([str(script_path), "__review_channel_inner"])
    lines = [
        "#!/bin/zsh",
        "set -euo pipefail",
        "",
        f"cd {shlex.quote(str(repo_root))}",
        "PROMPT=$(cat <<'EOF_PROMPT'",
        prompt,
        "EOF_PROMPT",
        ")",
        'export REVIEW_CHANNEL_PROMPT="$PROMPT"',
        'REVIEW_CHANNEL_RESTART_DELAY_SECONDS="${REVIEW_CHANNEL_RESTART_DELAY_SECONDS:-2}"',
        'REVIEW_CHANNEL_EXIT_ON_SUCCESS="${REVIEW_CHANNEL_EXIT_ON_SUCCESS:-0}"',
        "",
        "run_review_channel_once() {",
        f"  cd {shlex.quote(str(repo_root))}",
    ]
    lines.extend(f"  {line}" for line in _provider_shell_prelude(provider))
    lines.extend(
        [
            f"  {execution_command} \"$REVIEW_CHANNEL_PROMPT\"",
            "}",
            "",
        ]
    )
    if log_path is not None:
        lines.extend(
            [
                f"mkdir -p {shlex.quote(str(log_path.parent))}",
                'if [[ "${1:-}" != "__review_channel_inner" ]] && command -v script >/dev/null 2>&1; then',
                "  exec "
                + shlex.join(
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
                ),
                "fi",
            ]
        )
    lines.extend(
        [
            "restart_count=0",
            "while true; do",
            "  if run_review_channel_once; then",
            '    if [[ "$REVIEW_CHANNEL_EXIT_ON_SUCCESS" == "1" ]]; then',
            "      exit 0",
            "    fi",
            "    restart_count=$((restart_count + 1))",
            '    printf \'%s\\n\' "[review-channel] '
            + provider
            + ' conductor exited cleanly; relaunching from repo state in ${REVIEW_CHANNEL_RESTART_DELAY_SECONDS}s (restart #${restart_count}). Set REVIEW_CHANNEL_EXIT_ON_SUCCESS=1 to disable supervised relaunch for this invocation."',
            '    sleep "$REVIEW_CHANNEL_RESTART_DELAY_SECONDS"',
            "    continue",
            "  fi",
            "  exit_code=$?",
            '  printf \'%s\\n\' "[review-channel] '
            + provider
            + ' conductor exited with status ${exit_code}; leaving the session stopped so the failure stays visible." >&2',
            '  exit "$exit_code"',
            "done",
            "",
        ]
    )
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("\n".join(lines), encoding="utf-8")
    script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)
    return script_path


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
