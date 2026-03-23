"""Guarded local command runner with automatic post-run process hygiene."""

from __future__ import annotations

import json
import sys
import time

from ..common import cmd_str, emit_output, pipe_output, run_cmd, write_output
from ..config import REPO_ROOT
from ..guard_run_core import (
    GuardGitSnapshot,
    GuardRunRequest,
    WatchdogContext,
    build_guard_run_markdown,
    build_guard_run_probe_targets,
    capture_guard_git_snapshot,
    command_uses_shell_wrapper,
    resolve_guard_cwd,
    resolve_guard_post_action,
    watchdog_context_from_args,
)
from ..process_sweep.core import path_is_under_repo
from ..time_utils import utc_timestamp
from ..watchdog.episode import emit_guarded_coding_episode

try:
    from dev.scripts.coderabbit.probe_guidance import load_probe_guidance
    from dev.scripts.coderabbit.probe_guidance_artifacts import guidance_ref
except ModuleNotFoundError:  # broad-except: allow reason=devctl CLI runs from dev/scripts
    from coderabbit.probe_guidance import load_probe_guidance
    from coderabbit.probe_guidance_artifacts import guidance_ref

POST_ACTIONS = {"auto", "quick", "cleanup", "none"}
DEVCTL_PYTHON_EXECUTABLE = sys.executable or "python3"
QUICK_FOLLOWUP_CMD = [
    DEVCTL_PYTHON_EXECUTABLE,
    "dev/scripts/devctl.py",
    "check",
    "--profile",
    "quick",
    "--skip-fmt",
    "--skip-clippy",
    "--no-parallel",
]
CLEANUP_FOLLOWUP_CMD = [
    DEVCTL_PYTHON_EXECUTABLE,
    "dev/scripts/devctl.py",
    "process-cleanup",
    "--verify",
    "--format",
    "md",
]


def build_guard_run_report(
    request: GuardRunRequest,
    *,
    watchdog_context: WatchdogContext | None = None,
) -> dict:
    """Run one guarded command and always follow with the selected hygiene step."""
    started_at_utc = utc_timestamp()
    started_monotonic = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    command = list(request.command_args)
    if command and command[0] == "--":
        command = command[1:]
    resolved_cwd = resolve_guard_cwd(request.cwd)
    command_result: dict | None = None
    post_result: dict | None = None
    post_result_display: str | None = None
    diff_snapshot_before: GuardGitSnapshot | None = None
    diff_snapshot_after: GuardGitSnapshot | None = None
    probe_guidance: list[dict[str, object]] = []
    guidance_refs: list[str] = []

    if request.requested_post_action not in POST_ACTIONS:
        errors.append(
            f"Unknown post-action '{request.requested_post_action}'. Expected one of: {', '.join(sorted(POST_ACTIONS))}."
        )
    if not command:
        errors.append("No command provided. Pass the guarded command after `--`.")
    elif not path_is_under_repo(str(resolved_cwd)):
        errors.append(
            f"--cwd resolves outside this checkout: {resolved_cwd}. "
            "guard-run only guarantees post-run hygiene for this repository."
        )
    elif command_uses_shell_wrapper(command):
        errors.append(
            "Shell `-c` wrappers are not allowed in `guard-run`; pass the command directly or "
            "invoke an explicit script path instead."
        )

    resolved_post_action = (
        resolve_guard_post_action(
            command,
            requested_action=request.requested_post_action,
        )
        if not errors
        else request.requested_post_action
    )
    if resolved_post_action == "quick":
        post_followup_cmd = list(QUICK_FOLLOWUP_CMD)
    elif resolved_post_action == "cleanup":
        post_followup_cmd = list(CLEANUP_FOLLOWUP_CMD)
    else:
        post_followup_cmd = None

    if not errors:
        diff_snapshot_before = capture_guard_git_snapshot(resolved_cwd)
        command_result = run_cmd(
            request.label or "guarded-command",
            command,
            cwd=resolved_cwd,
            dry_run=request.dry_run,
        )
        if post_followup_cmd is not None:
            post_result_display = cmd_str(post_followup_cmd)
            post_result = run_cmd(
                "guarded-post-run-hygiene",
                post_followup_cmd,
                cwd=REPO_ROOT,
                dry_run=request.dry_run,
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
        diff_snapshot_after = capture_guard_git_snapshot(resolved_cwd)
        probe_targets = build_guard_run_probe_targets(
            diff_snapshot_before,
            diff_snapshot_after,
        )
        if probe_targets:
            probe_guidance = load_probe_guidance(probe_targets)
            for entry in probe_guidance:
                entry["guidance_id"] = guidance_ref(entry)
            guidance_refs = [
                str(entry.get("guidance_id") or "").strip()
                for entry in probe_guidance
                if str(entry.get("guidance_id") or "").strip()
            ]

    # Run probe quality scan when enabled (autonomy loops turn this on).
    probe_scan_result: dict[str, object] | None = None
    if request.run_probe_scan and not request.dry_run and diff_snapshot_after is not None:
        try:
            from ..watchdog.probe_gate import run_probe_scan as _probe_scan

            scan = _probe_scan(timeout_seconds=120)
            probe_scan_result = scan.to_dict()
        # broad-except: allow reason=probe scan must fail open fallback=emit warning and continue
        except Exception as exc:
            warnings.append(f"Probe scan skipped: {exc}")

    finished_at_utc = utc_timestamp()
    runtime_seconds = round(max(time.perf_counter() - started_monotonic, 0.0), 3)

    report: dict[str, object] = {}
    report["command"] = "guard-run"
    report["timestamp"] = finished_at_utc
    report["label"] = request.label or "guarded-command"
    report["cwd"] = str(resolved_cwd)
    report["dry_run"] = bool(request.dry_run)
    report["requested_post_action"] = request.requested_post_action
    report["resolved_post_action"] = resolved_post_action
    report["guard_started_at_utc"] = started_at_utc
    report["guard_finished_at_utc"] = finished_at_utc
    report["guard_runtime_seconds"] = runtime_seconds
    report["command_args"] = command
    report["command_display"] = cmd_str(command) if command else ""
    report["command_result"] = command_result
    report["post_result"] = post_result
    report["post_result_display"] = post_result_display
    report["diff_snapshot_before"] = diff_snapshot_before.to_dict() if diff_snapshot_before else None
    report["diff_snapshot_after"] = diff_snapshot_after.to_dict() if diff_snapshot_after else None
    report["probe_guidance"] = probe_guidance
    report["guidance_refs"] = guidance_refs
    report["guidance_adoption_required"] = bool(probe_guidance)
    report["watchdog_context"] = watchdog_context.to_dict() if watchdog_context else {}
    report["probe_scan"] = probe_scan_result
    report["warnings"] = warnings
    report["errors"] = errors
    report["ok"] = not errors
    return report


def run(args) -> int:
    """Run a local command with guaranteed post-run process hygiene follow-up."""
    request = GuardRunRequest(
        command_args=list(getattr(args, "guarded_command", [])),
        cwd=getattr(args, "cwd", None),
        requested_post_action=str(getattr(args, "post_action", "auto")),
        label=getattr(args, "label", None),
        dry_run=bool(getattr(args, "dry_run", False)),
    )
    report = build_guard_run_report(
        request,
        watchdog_context=watchdog_context_from_args(args),
    )
    should_emit_episode = report.get("command_result") is not None
    try:
        summary_path = emit_guarded_coding_episode(report) if should_emit_episode else None
    # broad-except: allow reason=watchdog artifact writes must fail open fallback=emit warning and continue
    except Exception as exc:
        report["warnings"].append(f"Watchdog episode emit skipped: {exc}")
        summary_path = None
    if summary_path:
        report["watchdog_summary_path"] = summary_path
    output = json.dumps(report, indent=2) if args.format == "json" else build_guard_run_markdown(report)
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
