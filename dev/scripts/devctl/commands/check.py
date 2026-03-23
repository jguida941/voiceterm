"""`devctl check` command — orchestrator.

Phase logic lives in check_phases.py. This module owns the public entry
point (run), the process-sweep wrappers, and release-gate command building
that other modules import.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..common import build_env
from ..config import get_repo_root, set_repo_root
from ..process_sweep.core import (
    kill_processes,
    scan_repo_hygiene_process_tree,
    split_orphaned_processes,
    split_stale_processes,
)
from ..quality_policy import resolve_quality_policy
from ..quality_scan_mode import resolve_scan_mode
from ..script_catalog import check_script_cmd
from ..steps import format_steps_md
from . import check_phases as check_phases_module
from .check_phases import (
    CheckContext,
    run_probe_phase,
    run_setup_phase,
    run_specialized_phases,
    run_test_build_phase,
)
from .check_process_sweep import (
    cleanup_host_processes,
    cleanup_orphaned_voiceterm_test_binaries,
    parse_etime_seconds_for_compat,
)
from .check_profile import resolve_profile_settings, validate_profile_flag_conflicts
from .check_progress import count_quality_steps
from .process_cleanup import build_process_cleanup_report


def build_report_and_emit(ctx: CheckContext) -> int:
    """Format the final report while preserving existing test patch paths."""
    success = all(step["returncode"] == 0 for step in ctx.steps)
    report = {
        "command": "check",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "steps": ctx.steps,
    }
    if check_phases_module.should_emit_output(ctx.args):
        if ctx.args.format == "md":
            output = "# devctl check\n\n" + format_steps_md(ctx.steps)
        else:
            output = json.dumps(report, indent=2)
        if ctx.args.output or ctx.args.format != "text":
            pipe_rc = check_phases_module.emit_output(
                output,
                output_path=ctx.args.output,
                pipe_command=ctx.args.pipe_command,
                pipe_args=ctx.args.pipe_args,
                writer=check_phases_module.write_output,
                piper=check_phases_module.pipe_output,
            )
            if pipe_rc != 0:
                return pipe_rc
    return 0 if success else 1


def _parse_etime_seconds(raw: str) -> int | None:
    return parse_etime_seconds_for_compat(raw)


def build_release_gate_commands() -> list[list[str]]:
    """Return release-gate commands required by `check --profile release`."""
    return [
        [
            "python3",
            "dev/scripts/devctl.py",
            "status",
            "--ci",
            "--require-ci",
            "--format",
            "md",
        ],
        check_script_cmd("coderabbit_gate", "--branch", "master"),
        check_script_cmd("coderabbit_ralph_gate", "--branch", "master"),
    ]


def _cleanup_orphaned_voiceterm_test_binaries(step_name: str, dry_run: bool) -> dict:
    return cleanup_orphaned_voiceterm_test_binaries(
        step_name,
        dry_run=dry_run,
        repo_root=get_repo_root(),
        scanner=scan_repo_hygiene_process_tree,
        split_orphans=split_orphaned_processes,
        split_stale=split_stale_processes,
        killer=kill_processes,
    )


def _cleanup_host_processes(step_name: str, dry_run: bool) -> dict:
    return cleanup_host_processes(
        step_name,
        dry_run=dry_run,
        repo_root=get_repo_root(),
        cleanup_report_builder=build_process_cleanup_report,
    )


def _warn_profile_conflicts(args) -> None:
    for warning in validate_profile_flag_conflicts(args):
        print(f"[check] warning: {warning}", file=sys.stderr)


def _resolve_scan_mode_or_exit(args):
    try:
        return resolve_scan_mode(
            since_ref=getattr(args, "since_ref", None),
            head_ref=getattr(args, "head_ref", "HEAD"),
            adoption_scan=bool(getattr(args, "adoption_scan", False)),
        )
    except ValueError as exc:
        print(f"[check] error: {exc}", file=sys.stderr)
        return None


def _resolve_quality_policy_with_warnings(args):
    quality_policy = resolve_quality_policy(
        policy_path=getattr(args, "quality_policy", None),
    )
    for warning in quality_policy.warnings:
        print(f"[check] warning: {warning}", file=sys.stderr)
    return quality_policy


def _apply_external_repo_rust_capability(args, repo_path, quality_policy) -> None:
    if not repo_path or quality_policy.capabilities.rust:
        return
    disabled_steps: list[str] = []
    for attr_name, label in (
        ("skip_fmt", "fmt"),
        ("skip_clippy", "clippy"),
        ("skip_tests", "test"),
        ("skip_build", "build"),
    ):
        if getattr(args, attr_name):
            continue
        setattr(args, attr_name, True)
        disabled_steps.append(label)
    if disabled_steps:
        joined_steps = ", ".join(disabled_steps)
        print(
            "[check] warning: external repo scan detected no Rust capability; "
            f"skipping Rust-only steps ({joined_steps})",
            file=sys.stderr,
        )


def _build_check_context(args, quality_policy, scan_mode) -> CheckContext:
    settings, clippy_cmd = resolve_profile_settings(args)
    return CheckContext(
        args=args,
        env=build_env(args),
        settings=settings,
        clippy_cmd=clippy_cmd,
        ai_guard_checks=quality_policy.ai_guard_checks,
        review_probe_checks=quality_policy.review_probe_checks,
        scan_mode=scan_mode.mode,
        scan_since_ref=scan_mode.since_ref,
        scan_head_ref=scan_mode.head_ref,
        parallel_enabled=not getattr(args, "no_parallel", False),
        parallel_workers=max(1, int(getattr(args, "parallel_workers", 4))),
        total_quality_steps=count_quality_steps(
            args,
            settings,
            ai_guard_checks=quality_policy.ai_guard_checks,
            review_probe_checks=quality_policy.review_probe_checks,
        ),
    )


def _resolve_cleanup_flags(args, repo_path) -> tuple[bool, bool]:
    process_sweep_cleanup = not getattr(args, "no_process_sweep_cleanup", False)
    host_process_cleanup = getattr(args, "profile", None) in {"quick", "fast"} and not getattr(
        args, "no_host_process_cleanup", False
    )
    if not repo_path:
        return process_sweep_cleanup, host_process_cleanup
    if process_sweep_cleanup:
        print(
            "[check] warning: skipping local process-sweep cleanup for external repo scans",
            file=sys.stderr,
        )
    if host_process_cleanup:
        print(
            "[check] warning: skipping local host-process cleanup for external repo scans",
            file=sys.stderr,
        )
    return False, False


def _run_check_phases(ctx: CheckContext) -> None:
    run_setup_phase(ctx)
    run_test_build_phase(ctx)
    run_specialized_phases(ctx, build_release_gate_commands)
    run_probe_phase(ctx)


def _record_check_halt(ctx: CheckContext, message: str) -> None:
    if any(step.get("returncode", 0) != 0 for step in ctx.steps):
        return
    ctx.steps.append(
        {
            "name": "check-halt",
            "cmd": ["internal", "check-halt"],
            "cwd": str(get_repo_root()),
            "returncode": 1,
            "duration_s": 0.0,
            "skipped": False,
            "error": message,
        }
    )


def _append_post_run_cleanup(
    ctx: CheckContext,
    *,
    process_sweep_cleanup: bool,
    host_process_cleanup: bool,
    dry_run: bool,
) -> None:
    if process_sweep_cleanup:
        ctx.steps.append(
            _cleanup_orphaned_voiceterm_test_binaries(
                step_name="process-sweep-post",
                dry_run=dry_run,
            )
        )
    if host_process_cleanup:
        ctx.steps.append(
            _cleanup_host_processes(
                step_name="host-process-cleanup-post",
                dry_run=dry_run,
            )
        )


def run(args) -> int:
    """Run check steps for the selected profile and return an exit code."""
    repo_path = getattr(args, "repo_path", None)
    previous_root = get_repo_root()
    if repo_path:
        set_repo_root(Path(repo_path))
    try:
        _warn_profile_conflicts(args)
        scan_mode = _resolve_scan_mode_or_exit(args)
        if scan_mode is None:
            return 2

        quality_policy = _resolve_quality_policy_with_warnings(args)
        _apply_external_repo_rust_capability(args, repo_path, quality_policy)
        ctx = _build_check_context(args, quality_policy, scan_mode)
        process_sweep_cleanup, host_process_cleanup = _resolve_cleanup_flags(args, repo_path)

        if process_sweep_cleanup:
            ctx.steps.append(
                _cleanup_orphaned_voiceterm_test_binaries(
                    step_name="process-sweep-pre",
                    dry_run=args.dry_run,
                )
            )

        try:
            _run_check_phases(ctx)
        except RuntimeError as exc:
            message = str(exc) or "check halted due to runtime error"
            print(f"[check] error: {message}", file=sys.stderr)
            _record_check_halt(ctx, message)
        finally:
            _append_post_run_cleanup(
                ctx,
                process_sweep_cleanup=process_sweep_cleanup,
                host_process_cleanup=host_process_cleanup,
                dry_run=args.dry_run,
            )

        return build_report_and_emit(ctx)
    finally:
        if repo_path:
            set_repo_root(previous_root)
