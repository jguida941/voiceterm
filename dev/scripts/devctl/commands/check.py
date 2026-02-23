"""`devctl check` command.

This command runs local quality gates (fmt, clippy, tests, build, and optional
extra guards). It is the main pre-push/pre-release verifier for maintainers.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from types import SimpleNamespace
from typing import List

from ..common import build_env, pipe_output, run_cmd, should_emit_output, write_output
from ..config import REPO_ROOT, SRC_DIR
from ..process_sweep import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    kill_processes,
    parse_etime_seconds,
    scan_voiceterm_test_binaries,
    split_orphaned_processes,
)
from ..script_catalog import check_script_cmd
from ..steps import format_steps_md
from .check_profile import resolve_profile_settings, validate_profile_flag_conflicts
from .check_progress import count_quality_steps, emit_progress
from .check_steps import build_step_spec, run_step_specs
from .check_support import (
    AI_GUARD_CHECKS,
    maybe_emit_ai_guard_scaffold,
    resolve_perf_log_path,
)
from .mutation_score import build_mutation_score_cmd, resolve_outcomes_path
from .mutants import build_mutants_cmd

ORPHAN_TEST_MIN_AGE_SECONDS = DEFAULT_ORPHAN_MIN_AGE_SECONDS


def _parse_etime_seconds(raw: str) -> int | None:
    """Kept for test compatibility; delegates to shared process-sweep parsing."""
    return parse_etime_seconds(raw)


def _scan_orphaned_voiceterm_test_binaries() -> tuple[list[dict], list[str]]:
    rows, warnings = scan_voiceterm_test_binaries()
    orphaned, _active = split_orphaned_processes(
        rows, min_age_seconds=ORPHAN_TEST_MIN_AGE_SECONDS
    )
    return orphaned, warnings


def _cleanup_orphaned_voiceterm_test_binaries(step_name: str, dry_run: bool) -> dict:
    """Clean up detached test binaries so local runs stay stable over time."""
    start = time.time()
    if dry_run:
        return {
            "name": step_name,
            "cmd": ["internal", "process-sweep", "--dry-run"],
            "cwd": str(REPO_ROOT),
            "returncode": 0,
            "duration_s": 0.0,
            "skipped": True,
            "warnings": [],
            "killed_pids": [],
            "detected_orphans": 0,
        }

    orphaned, warnings = _scan_orphaned_voiceterm_test_binaries()
    killed_pids, kill_warnings = kill_processes(orphaned)

    for warning in warnings:
        print(f"[{step_name}] warning: {warning}")
    if orphaned:
        print(f"[{step_name}] detected {len(orphaned)} orphaned voiceterm test binaries")
    if killed_pids:
        print(f"[{step_name}] killed {len(killed_pids)} orphaned voiceterm test binaries")
    for warning in kill_warnings:
        print(f"[{step_name}] warning: {warning}")

    return {
        "name": step_name,
        "cmd": ["internal", "process-sweep", "--kill-orphans"],
        "cwd": str(REPO_ROOT),
        "returncode": 0,
        "duration_s": round(time.time() - start, 2),
        "skipped": False,
        "warnings": warnings + kill_warnings,
        "killed_pids": killed_pids,
        "detected_orphans": len(orphaned),
    }


def run(args) -> int:
    """Run check steps for the selected profile and return an exit code."""
    for warning in validate_profile_flag_conflicts(args):
        print(f"[check] warning: {warning}", file=sys.stderr)

    env = build_env(args)
    steps: List[dict] = []
    settings, clippy_cmd = resolve_profile_settings(args)
    process_sweep_cleanup = not getattr(args, "no_process_sweep_cleanup", False)
    parallel_enabled = not getattr(args, "no_parallel", False)
    parallel_workers = max(1, int(getattr(args, "parallel_workers", 4)))
    total_quality_steps = count_quality_steps(args, settings)
    progress_counter = [0]  # mutable counter accessible from inner functions
    audit_scaffold_emitted = False

    def emit_failure_summary(result: dict) -> None:
        """Show a short actionable error summary after a failed step."""
        if result["returncode"] == 0:
            return
        print(f"[check] step failed: {result['name']} (exit {result['returncode']})")
        if result.get("error"):
            print(f"[check] error: {result['error']}")
        failure_output = result.get("failure_output")
        if failure_output:
            print(f"[check] last output from {result['name']}:")
            print(failure_output)

    def make_step_spec(name: str, cmd: List[str], cwd=None, step_env=None) -> dict:
        return build_step_spec(
            name=name,
            cmd=cmd,
            default_env=env,
            cwd=cwd,
            step_env=step_env,
        )

    def add_steps(step_specs: List[dict], allow_parallel: bool = False) -> None:
        if not step_specs:
            return
        use_parallel = allow_parallel and parallel_enabled
        if total_quality_steps > 0:
            emit_progress(step_specs, progress_counter[0], total_quality_steps, use_parallel)
        progress_counter[0] += len(step_specs)

        results = run_step_specs(
            step_specs,
            dry_run=args.dry_run,
            parallel_enabled=use_parallel,
            max_workers=parallel_workers,
        )

        failed = False
        failed_results = []
        for result in results:
            steps.append(result)
            if result["returncode"] != 0:
                failed = True
                failed_results.append(result)
                emit_failure_summary(result)

        nonlocal audit_scaffold_emitted
        audit_scaffold_emitted, scaffold_result = maybe_emit_ai_guard_scaffold(
            with_ai_guard=settings["with_ai_guard"],
            already_emitted=audit_scaffold_emitted,
            failed_results=failed_results,
            run_cmd_fn=run_cmd,
            repo_root=REPO_ROOT,
            dry_run=args.dry_run,
        )
        if scaffold_result is not None:
            steps.append(scaffold_result)
            if scaffold_result["returncode"] == 0:
                print("[check] generated remediation scaffold: dev/active/RUST_AUDIT_FINDINGS.md")
            else:
                print("[check] failed to generate remediation scaffold")
                if scaffold_result.get("error"):
                    print(f"[check] scaffold error: {scaffold_result['error']}")

        if failed and not args.keep_going:
            failed_steps = ", ".join(result["name"] for result in results if result["returncode"] != 0)
            raise RuntimeError(f"check phase failed ({failed_steps})")

    def add_step(name: str, cmd: List[str], cwd=None, step_env=None) -> None:
        add_steps([make_step_spec(name, cmd, cwd=cwd, step_env=step_env)])

    if process_sweep_cleanup:
        steps.append(
            _cleanup_orphaned_voiceterm_test_binaries(
                step_name="process-sweep-pre",
                dry_run=args.dry_run,
            )
        )

    try:
        setup_phase_specs: List[dict] = []
        if not args.skip_fmt:
            if args.fix:
                setup_phase_specs.append(make_step_spec("fmt", ["cargo", "fmt", "--all"], cwd=SRC_DIR))
            else:
                setup_phase_specs.append(
                    make_step_spec(
                        "fmt-check",
                        ["cargo", "fmt", "--all", "--", "--check"],
                        cwd=SRC_DIR,
                    )
                )

        if not args.skip_clippy:
            setup_phase_specs.append(make_step_spec("clippy", clippy_cmd, cwd=SRC_DIR))

        if settings["with_ai_guard"]:
            setup_phase_specs.extend(
                make_step_spec(name, check_script_cmd(script_id), cwd=REPO_ROOT)
                for name, script_id in AI_GUARD_CHECKS
            )

        add_steps(setup_phase_specs, allow_parallel=True)

        test_build_phase_specs: List[dict] = []
        if not settings["skip_tests"]:
            test_build_phase_specs.append(
                make_step_spec(
                    "test",
                    ["cargo", "test", "--workspace", "--all-features"],
                    cwd=SRC_DIR,
                )
            )
        if not settings["skip_build"]:
            test_build_phase_specs.append(
                make_step_spec(
                    "build-release",
                    ["cargo", "build", "--release", "--bin", "voiceterm"],
                    cwd=SRC_DIR,
                )
            )
        add_steps(test_build_phase_specs, allow_parallel=True)

        if settings["with_wake_guard"]:
            wake_guard_env = dict(env)
            wake_guard_env["WAKE_WORD_SOAK_ROUNDS"] = str(args.wake_soak_rounds)
            add_step(
                "wake-guard",
                ["bash", "dev/scripts/tests/wake_word_guard.sh"],
                cwd=REPO_ROOT,
                step_env=wake_guard_env,
            )

        if settings["with_perf"]:
            add_step(
                "perf-smoke",
                [
                    "cargo",
                    "test",
                    "--no-default-features",
                    "legacy_tui::tests::perf_smoke_emits_voice_metrics",
                    "--",
                    "--nocapture",
                ],
                cwd=SRC_DIR,
            )
            if not args.dry_run:
                log_path = resolve_perf_log_path()
                add_step(
                    "perf-verify",
                    ["python3", ".github/scripts/verify_perf_metrics.py", log_path],
                    cwd=REPO_ROOT,
                )

        if settings["with_mem_loop"]:
            for index in range(args.mem_iterations):
                add_step(
                    f"mem-guard-{index + 1}",
                    [
                        "cargo",
                        "test",
                        "--no-default-features",
                        "legacy_tui::tests::memory_guard_backend_threads_drop",
                        "--",
                        "--nocapture",
                    ],
                    cwd=SRC_DIR,
                )

        if settings["with_mutants"]:
            mutants_args = SimpleNamespace(
                all=args.mutants_all,
                module=args.mutants_module,
                timeout=args.mutants_timeout,
                shard=args.mutants_shard,
                results_only=False,
                json=False,
                offline=args.mutants_offline,
                cargo_home=args.mutants_cargo_home,
                cargo_target_dir=args.mutants_cargo_target_dir,
                plot=args.mutants_plot,
                plot_scope=args.mutants_plot_scope,
                plot_top_pct=args.mutants_plot_top_pct,
                plot_output=args.mutants_plot_output,
                plot_show=args.mutants_plot_show,
                top=None,
            )
            add_step("mutants", build_mutants_cmd(mutants_args), cwd=REPO_ROOT)

        if settings["with_mutation_score"]:
            outcomes_path = resolve_outcomes_path(args.mutation_score_path)
            if outcomes_path is None:
                raise RuntimeError("mutation outcomes.json not found")
            add_step(
                "mutation-score",
                build_mutation_score_cmd(
                    outcomes_path,
                    args.mutation_score_threshold,
                    args.mutation_score_max_age_hours,
                    args.mutation_score_warn_age_hours,
                ),
                cwd=REPO_ROOT,
            )
    except RuntimeError:
        pass
    finally:
        if process_sweep_cleanup:
            steps.append(
                _cleanup_orphaned_voiceterm_test_binaries(
                    step_name="process-sweep-post",
                    dry_run=args.dry_run,
                )
            )

    success = all(step["returncode"] == 0 for step in steps)
    report = {
        "command": "check",
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "steps": steps,
    }

    if should_emit_output(args):
        if args.format == "md":
            output = "# devctl check\n\n" + format_steps_md(steps)
        else:
            output = json.dumps(report, indent=2)
        if args.output or args.format != "text":
            write_output(output, args.output)
        if args.pipe_command:
            pipe_rc = pipe_output(output, args.pipe_command, args.pipe_args)
            if pipe_rc != 0:
                return pipe_rc

    return 0 if success else 1
