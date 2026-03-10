"""`devctl check` command — orchestrator.

Phase logic lives in check_phases.py. This module owns the public entry
point (run), the process-sweep wrappers, and release-gate command building
that other modules import.
"""

from __future__ import annotations

import sys

from ..common import build_env
from ..config import REPO_ROOT
from .process_cleanup import build_process_cleanup_report
from ..process_sweep.core import (
    kill_processes,
    scan_repo_hygiene_process_tree,
    split_orphaned_processes,
    split_stale_processes,
)
from ..script_catalog import check_script_cmd
from .check_phases import (
    CheckContext,
    build_report_and_emit,
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
        repo_root=REPO_ROOT,
        scanner=scan_repo_hygiene_process_tree,
        split_orphans=split_orphaned_processes,
        split_stale=split_stale_processes,
        killer=kill_processes,
    )


def _cleanup_host_processes(step_name: str, dry_run: bool) -> dict:
    return cleanup_host_processes(
        step_name,
        dry_run=dry_run,
        repo_root=REPO_ROOT,
        cleanup_report_builder=build_process_cleanup_report,
    )


def run(args) -> int:
    """Run check steps for the selected profile and return an exit code."""
    for warning in validate_profile_flag_conflicts(args):
        print(f"[check] warning: {warning}", file=sys.stderr)

    settings, clippy_cmd = resolve_profile_settings(args)
    ctx = CheckContext(
        args=args,
        env=build_env(args),
        settings=settings,
        clippy_cmd=clippy_cmd,
        parallel_enabled=not getattr(args, "no_parallel", False),
        parallel_workers=max(1, int(getattr(args, "parallel_workers", 4))),
        total_quality_steps=count_quality_steps(args, settings),
    )
    process_sweep_cleanup = not getattr(args, "no_process_sweep_cleanup", False)
    host_process_cleanup = (
        getattr(args, "profile", None) in {"quick", "fast"}
        and not getattr(args, "no_host_process_cleanup", False)
    )

    if process_sweep_cleanup:
        ctx.steps.append(
            _cleanup_orphaned_voiceterm_test_binaries(
                step_name="process-sweep-pre",
                dry_run=args.dry_run,
            )
        )

    try:
        run_setup_phase(ctx)
        run_test_build_phase(ctx)
        run_specialized_phases(ctx, build_release_gate_commands)
    except RuntimeError as exc:
        message = str(exc) or "check halted due to runtime error"
        print(f"[check] error: {message}", file=sys.stderr)
        if not any(step.get("returncode", 0) != 0 for step in ctx.steps):
            ctx.steps.append(
                {
                    "name": "check-halt",
                    "cmd": ["internal", "check-halt"],
                    "cwd": str(REPO_ROOT),
                    "returncode": 1,
                    "duration_s": 0.0,
                    "skipped": False,
                    "error": message,
                }
            )
    finally:
        if process_sweep_cleanup:
            ctx.steps.append(
                _cleanup_orphaned_voiceterm_test_binaries(
                    step_name="process-sweep-post",
                    dry_run=args.dry_run,
                )
            )
        if host_process_cleanup:
            ctx.steps.append(
                _cleanup_host_processes(
                    step_name="host-process-cleanup-post",
                    dry_run=args.dry_run,
                )
            )

    return build_report_and_emit(ctx)
