"""Guarded local command runner with automatic post-run process hygiene."""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..common import cmd_str, emit_output, pipe_output, run_cmd, write_output
from ..config import REPO_ROOT
from ..process_sweep.core import path_is_under_repo
from ..process_sweep.config import (
    REPO_RUNTIME_CARGO_RE,
    REPO_RUNTIME_RELATIVE_TARGET_BINARY_RE,
    REPO_RUNTIME_TARGET_BINARY_RE,
)
from ..time_utils import utc_timestamp

POST_ACTIONS = {"auto", "quick", "cleanup", "none"}
SHELL_EXECUTABLES = {"bash", "zsh", "sh"}
QUICK_FOLLOWUP_CMD = [
    "python3",
    "dev/scripts/devctl.py",
    "check",
    "--profile",
    "quick",
    "--skip-fmt",
    "--skip-clippy",
    "--no-parallel",
]
CLEANUP_FOLLOWUP_CMD = [
    "python3",
    "dev/scripts/devctl.py",
    "process-cleanup",
    "--verify",
    "--format",
    "md",
]


def _normalize_command(command_args: list[str]) -> list[str]:
    command = list(command_args)
    if command and command[0] == "--":
        command = command[1:]
    return command


def _resolve_cwd(raw_cwd: str | None) -> Path:
    if not raw_cwd:
        return REPO_ROOT
    path = Path(raw_cwd).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve(strict=False)


def _is_shell_c_wrapper(command: list[str]) -> bool:
    if not command:
        return False
    executable_name = os.path.basename(command[0])
    if executable_name not in SHELL_EXECUTABLES:
        return False
    return any(
        argument == "-c" or (argument.startswith("-") and "c" in argument[1:])
        for argument in command[1:]
    )


def _resolve_post_action(command: list[str], *, requested_action: str) -> str:
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


def _post_followup_command(action: str) -> list[str] | None:
    if action == "quick":
        return list(QUICK_FOLLOWUP_CMD)
    if action == "cleanup":
        return list(CLEANUP_FOLLOWUP_CMD)
    return None


def _render_md(report: dict) -> str:
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


def build_guard_run_report(
    *,
    command_args: list[str],
    cwd: str | None,
    requested_post_action: str,
    label: str | None,
    dry_run: bool,
) -> dict:
    """Run one guarded command and always follow with the selected hygiene step."""
    errors: list[str] = []
    warnings: list[str] = []
    command = _normalize_command(command_args)
    resolved_cwd = _resolve_cwd(cwd)
    command_result: dict | None = None
    post_result: dict | None = None
    post_result_display: str | None = None

    if requested_post_action not in POST_ACTIONS:
        errors.append(
            f"Unknown post-action '{requested_post_action}'. Expected one of: {', '.join(sorted(POST_ACTIONS))}."
        )
    if not command:
        errors.append("No command provided. Pass the guarded command after `--`.")
    elif not path_is_under_repo(str(resolved_cwd)):
        errors.append(
            f"--cwd resolves outside this checkout: {resolved_cwd}. "
            "guard-run only guarantees post-run hygiene for this repository."
        )
    elif _is_shell_c_wrapper(command):
        errors.append(
            "Shell `-c` wrappers are not allowed in `guard-run`; pass the command directly or "
            "invoke an explicit script path instead."
        )

    resolved_post_action = (
        _resolve_post_action(command, requested_action=requested_post_action)
        if not errors
        else requested_post_action
    )
    post_followup_cmd = _post_followup_command(resolved_post_action)

    if not errors:
        command_result = run_cmd(
            label or "guarded-command",
            command,
            cwd=resolved_cwd,
            dry_run=dry_run,
        )
        if post_followup_cmd is not None:
            post_result_display = cmd_str(post_followup_cmd)
            post_result = run_cmd(
                "guarded-post-run-hygiene",
                post_followup_cmd,
                cwd=REPO_ROOT,
                dry_run=dry_run,
            )
        if command_result["returncode"] != 0:
            errors.append(
                "Guarded command failed. The post-run hygiene step still ran so host cleanup state "
                "is not left ambiguous."
            )
        if post_result is not None and post_result["returncode"] != 0:
            errors.append("Post-run hygiene follow-up failed.")
        if resolved_post_action == "none":
            warnings.append(
                "Post-run hygiene was disabled; use this only when the command cannot create repo-owned "
                "runtime/tooling processes."
            )

    return {
        "command": "guard-run",
        "timestamp": utc_timestamp(),
        "label": label or "guarded-command",
        "cwd": str(resolved_cwd),
        "dry_run": bool(dry_run),
        "requested_post_action": requested_post_action,
        "resolved_post_action": resolved_post_action,
        "command_args": command,
        "command_display": cmd_str(command) if command else "",
        "command_result": command_result,
        "post_result": post_result,
        "post_result_display": post_result_display,
        "warnings": warnings,
        "errors": errors,
        "ok": not errors,
    }


def run(args) -> int:
    """Run a local command with guaranteed post-run process hygiene follow-up."""
    report = build_guard_run_report(
        command_args=list(getattr(args, "guarded_command", [])),
        cwd=getattr(args, "cwd", None),
        requested_post_action=str(getattr(args, "post_action", "auto")),
        label=getattr(args, "label", None),
        dry_run=bool(getattr(args, "dry_run", False)),
    )
    output = json.dumps(report, indent=2) if args.format == "json" else _render_md(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if report["ok"] else 1
