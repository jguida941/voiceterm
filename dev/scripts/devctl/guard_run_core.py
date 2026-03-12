"""Shared support helpers for the `devctl guard-run` command."""

from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .common import cmd_str
from .config import REPO_ROOT
from .process_sweep.config import (
    REPO_RUNTIME_CARGO_RE,
    REPO_RUNTIME_RELATIVE_TARGET_BINARY_RE,
    REPO_RUNTIME_TARGET_BINARY_RE,
)

SHELL_EXECUTABLES = {"bash", "zsh", "sh"}


@dataclass(frozen=True)
class GuardGitSnapshot:
    """Typed representation of a pre/post guard-run git worktree snapshot."""

    reviewed_worktree_hash: str = ""
    files_changed: tuple[str, ...] = ()
    file_count: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    diff_churn: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["files_changed"] = list(self.files_changed)
        return payload


@dataclass
class WatchdogContext:
    """Watchdog metadata extracted from CLI args for a guarded coding episode."""

    provider: str | None = None
    session_id: str | None = None
    peer_session_id: str | None = None
    trigger_reason: str | None = None
    retry_count: int = 0
    escaped_findings_count: int = 0
    guard_result: str | None = None
    reviewer_verdict: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GuardRunRequest:
    """Input bundle for one guarded command run."""

    command_args: list[str]
    cwd: str | None
    requested_post_action: str
    label: str | None
    dry_run: bool
    run_probe_scan: bool = False


def resolve_guard_cwd(raw_cwd: str | None) -> Path:
    """Resolve `--cwd` relative to the repository root."""
    if not raw_cwd:
        return REPO_ROOT
    path = Path(raw_cwd).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve(strict=False)


def command_uses_shell_wrapper(command: list[str]) -> bool:
    """Return whether the command hides the real workload behind `shell -c`."""
    if not command:
        return False
    executable_name = os.path.basename(command[0])
    if executable_name not in SHELL_EXECUTABLES:
        return False
    return any(argument == "-c" or (argument.startswith("-") and "c" in argument[1:]) for argument in command[1:])


def resolve_guard_post_action(command: list[str], *, requested_action: str) -> str:
    """Choose the follow-up hygiene action when `--post-action auto` is used."""
    if requested_action != "auto":
        return requested_action
    rendered = cmd_str(command)
    if (
        REPO_RUNTIME_CARGO_RE.search(rendered)
        or REPO_RUNTIME_TARGET_BINARY_RE.search(rendered)
        or REPO_RUNTIME_RELATIVE_TARGET_BINARY_RE.search(rendered)
    ):
        return "quick"
    return "cleanup"


def capture_guard_git_snapshot(cwd: Path) -> GuardGitSnapshot:
    """Capture a scoped git diff snapshot for the guarded command working tree."""
    scope = "." if cwd == REPO_ROOT else os.path.relpath(cwd, REPO_ROOT)
    head_result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    status_result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--short", "--untracked-files=all", "--", scope],
        check=False,
        capture_output=True,
        text=True,
    )
    diff_result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--numstat", "HEAD", "--", scope],
        check=False,
        capture_output=True,
        text=True,
    )

    files_changed: set[str] = set()
    if status_result.returncode == 0:
        for line in status_result.stdout.splitlines():
            text = line.rstrip()
            if len(text) < 4:
                continue
            path_text = text[3:]
            if " -> " in path_text:
                path_text = path_text.split(" -> ", 1)[1]
            if path_text:
                files_changed.add(path_text)

    lines_added = 0
    lines_removed = 0
    if diff_result.returncode == 0:
        for line in diff_result.stdout.splitlines():
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            if parts[0].isdigit():
                lines_added += int(parts[0])
            if parts[1].isdigit():
                lines_removed += int(parts[1])

    return GuardGitSnapshot(
        reviewed_worktree_hash=(head_result.stdout.strip() if head_result.returncode == 0 else ""),
        files_changed=tuple(sorted(files_changed)),
        file_count=len(files_changed),
        lines_added=lines_added,
        lines_removed=lines_removed,
        diff_churn=lines_added + lines_removed,
    )


def build_guard_run_markdown(report: dict[str, Any]) -> str:
    """Render the human-readable markdown form of a guard-run report."""
    lines = ["# devctl guard-run", ""]
    lines.append(f"- label: {report['label']}")
    lines.append(f"- cwd: {report['cwd']}")
    lines.append(f"- dry_run: {report['dry_run']}")
    lines.append(f"- requested_post_action: {report['requested_post_action']}")
    lines.append(f"- resolved_post_action: {report['resolved_post_action']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append("")
    lines.append("## Guarded Command")
    lines.append(f"- cmd: {report['command_display']}")
    if report["command_result"] is not None:
        lines.append(f"- returncode: {report['command_result']['returncode']}")
    if report["post_result"] is not None:
        lines.append("")
        lines.append("## Post-Run Hygiene")
        lines.append(f"- cmd: {report['post_result_display']}")
        lines.append(f"- returncode: {report['post_result']['returncode']}")
    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        for error in report["errors"]:
            lines.append(f"- {error}")
    return "\n".join(lines)


def watchdog_context_from_args(args: Any) -> WatchdogContext:
    """Build the watchdog context payload from parsed CLI args."""
    return WatchdogContext(
        provider=getattr(args, "provider", None),
        session_id=getattr(args, "session_id", None),
        peer_session_id=getattr(args, "peer_session_id", None),
        trigger_reason=getattr(args, "trigger_reason", None),
        retry_count=getattr(args, "retry_count", 0),
        escaped_findings_count=getattr(args, "escaped_findings_count", 0),
        guard_result=getattr(args, "guard_result", None),
        reviewer_verdict=getattr(args, "reviewer_verdict", None),
    )
