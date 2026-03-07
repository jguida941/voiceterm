"""Check phase orchestration — setup, test/build, specialized, and reporting.

Each phase function takes a CheckContext and mutates its step list.
Called exclusively from check.run().
"""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import List

from ..common import pipe_output, run_cmd, should_emit_output, write_output
from ..config import REPO_ROOT, SRC_DIR
from ..steps import format_steps_md
from .check_progress import emit_progress
from .check_steps import build_step_spec, run_step_specs
from .check_support import (
    AI_GUARD_CHECKS,
    build_ai_guard_cmd,
    build_clippy_high_signal_collect_cmd,
    build_clippy_high_signal_guard_cmd,
    maybe_emit_ai_guard_scaffold,
    resolve_perf_log_path,
)
from .mutants import build_mutants_cmd
from .mutation_score import build_mutation_score_cmd, resolve_outcomes_path

# -------------------------------------------------------
# Shared state for a single check run
# -------------------------------------------------------


@dataclasses.dataclass
class CheckContext:
    """Mutable orchestration state threaded through check phases."""

    args: object
    env: dict
    settings: dict
    clippy_cmd: list[str]
    steps: list[dict] = dataclasses.field(default_factory=list)
    parallel_enabled: bool = True
    parallel_workers: int = 4
    total_quality_steps: int = 0
    progress_counter: int = 0
    audit_scaffold_emitted: bool = False


# -------------------------------------------------------
# Step execution helpers
# -------------------------------------------------------


def _emit_failure_summary(result: dict) -> None:
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


def _make_step_spec(
    ctx: CheckContext, name: str, cmd: List[str], cwd=None, step_env=None
) -> dict:
    return build_step_spec(
        name=name,
        cmd=cmd,
        default_env=ctx.env,
        cwd=cwd,
        step_env=step_env,
    )


def _add_steps(
    ctx: CheckContext, step_specs: List[dict], allow_parallel: bool = False
) -> None:
    """Execute step specs, collect results, and handle scaffold/fail-fast."""
    if not step_specs:
        return
    use_parallel = allow_parallel and ctx.parallel_enabled
    if ctx.total_quality_steps > 0:
        emit_progress(
            step_specs, ctx.progress_counter, ctx.total_quality_steps, use_parallel
        )
    ctx.progress_counter += len(step_specs)

    results = run_step_specs(
        step_specs,
        dry_run=ctx.args.dry_run,
        parallel_enabled=use_parallel,
        max_workers=ctx.parallel_workers,
    )

    failed = False
    failed_results = []
    for result in results:
        ctx.steps.append(result)
        if result["returncode"] != 0:
            failed = True
            failed_results.append(result)
            _emit_failure_summary(result)

    ctx.audit_scaffold_emitted, scaffold_result = maybe_emit_ai_guard_scaffold(
        with_ai_guard=ctx.settings["with_ai_guard"],
        already_emitted=ctx.audit_scaffold_emitted,
        failed_results=failed_results,
        run_cmd_fn=run_cmd,
        repo_root=REPO_ROOT,
        dry_run=ctx.args.dry_run,
    )
    if scaffold_result is not None:
        ctx.steps.append(scaffold_result)
        if scaffold_result["returncode"] == 0:
            print(
                "[check] generated remediation scaffold:"
                " dev/reports/audits/RUST_AUDIT_FINDINGS.md"
            )
        else:
            print("[check] failed to generate remediation scaffold")
            if scaffold_result.get("error"):
                print(f"[check] scaffold error: {scaffold_result['error']}")

    if failed and not ctx.args.keep_going:
        failed_steps = ", ".join(
            result["name"] for result in results if result["returncode"] != 0
        )
        raise RuntimeError(f"check phase failed ({failed_steps})")


def _add_step(
    ctx: CheckContext, name: str, cmd: List[str], cwd=None, step_env=None
) -> None:
    _add_steps(ctx, [_make_step_spec(ctx, name, cmd, cwd=cwd, step_env=step_env)])


# -------------------------------------------------------
# Phase runners
# -------------------------------------------------------


def run_setup_phase(ctx: CheckContext) -> None:
    """Lint phase: fmt, clippy, and AI-guard steps."""
    setup_specs: List[dict] = []
    followup_specs: List[dict] = []

    if not ctx.args.skip_fmt:
        if ctx.args.fix:
            setup_specs.append(
                _make_step_spec(ctx, "fmt", ["cargo", "fmt", "--all"], cwd=SRC_DIR)
            )
        else:
            setup_specs.append(
                _make_step_spec(
                    ctx,
                    "fmt-check",
                    ["cargo", "fmt", "--all", "--", "--check"],
                    cwd=SRC_DIR,
                )
            )

    if not ctx.args.skip_clippy:
        if ctx.settings.get("with_clippy_high_signal", False):
            setup_specs.append(
                _make_step_spec(
                    ctx,
                    "clippy",
                    build_clippy_high_signal_collect_cmd(),
                    cwd=REPO_ROOT,
                )
            )
            followup_specs.append(
                _make_step_spec(
                    ctx,
                    "clippy-high-signal-guard",
                    build_clippy_high_signal_guard_cmd(),
                    cwd=REPO_ROOT,
                )
            )
        else:
            setup_specs.append(
                _make_step_spec(ctx, "clippy", ctx.clippy_cmd, cwd=SRC_DIR)
            )

    if ctx.settings["with_ai_guard"]:
        since_ref = getattr(ctx.args, "since_ref", None)
        head_ref = getattr(ctx.args, "head_ref", "HEAD")
        setup_specs.extend(
            _make_step_spec(
                ctx,
                name,
                build_ai_guard_cmd(
                    script_id,
                    since_ref=since_ref,
                    head_ref=head_ref,
                    extra_args=extra_args,
                ),
                cwd=REPO_ROOT,
            )
            for name, script_id, extra_args in AI_GUARD_CHECKS
        )

    _add_steps(ctx, setup_specs, allow_parallel=True)
    _add_steps(ctx, followup_specs)


def run_test_build_phase(ctx: CheckContext) -> None:
    """Compile and test phase: cargo test + release build."""
    specs: List[dict] = []
    if not ctx.settings["skip_tests"]:
        specs.append(
            _make_step_spec(
                ctx,
                "test",
                ["cargo", "test", "--workspace", "--all-features"],
                cwd=SRC_DIR,
            )
        )
    if not ctx.settings["skip_build"]:
        specs.append(
            _make_step_spec(
                ctx,
                "build-release",
                ["cargo", "build", "--release", "--bin", "voiceterm"],
                cwd=SRC_DIR,
            )
        )
    _add_steps(ctx, specs, allow_parallel=True)


def run_specialized_phases(ctx: CheckContext, release_gate_fn) -> None:
    """Optional phases: wake guard, perf, memory, mutants, mutation score, release gates."""
    if ctx.settings["with_wake_guard"]:
        wake_env = dict(ctx.env)
        wake_env["WAKE_WORD_SOAK_ROUNDS"] = str(ctx.args.wake_soak_rounds)
        _add_step(
            ctx,
            "wake-guard",
            ["bash", "dev/scripts/tests/wake_word_guard.sh"],
            cwd=REPO_ROOT,
            step_env=wake_env,
        )

    if ctx.settings["with_perf"]:
        _add_step(
            ctx,
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
        if not ctx.args.dry_run:
            log_path = resolve_perf_log_path()
            _add_step(
                ctx,
                "perf-verify",
                ["python3", ".github/scripts/verify_perf_metrics.py", log_path],
                cwd=REPO_ROOT,
            )

    if ctx.settings["with_mem_loop"]:
        for index in range(ctx.args.mem_iterations):
            _add_step(
                ctx,
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

    if ctx.settings["with_mutants"]:
        mutants_args = SimpleNamespace(
            all=ctx.args.mutants_all,
            module=ctx.args.mutants_module,
            timeout=ctx.args.mutants_timeout,
            shard=ctx.args.mutants_shard,
            results_only=False,
            json=False,
            offline=ctx.args.mutants_offline,
            cargo_home=ctx.args.mutants_cargo_home,
            cargo_target_dir=ctx.args.mutants_cargo_target_dir,
            plot=ctx.args.mutants_plot,
            plot_scope=ctx.args.mutants_plot_scope,
            plot_top_pct=ctx.args.mutants_plot_top_pct,
            plot_output=ctx.args.mutants_plot_output,
            plot_show=ctx.args.mutants_plot_show,
            top=None,
        )
        _add_step(ctx, "mutants", build_mutants_cmd(mutants_args), cwd=REPO_ROOT)

    if ctx.settings["with_mutation_score"]:
        outcomes_path = resolve_outcomes_path(ctx.args.mutation_score_path)
        report_only = ctx.settings.get("mutation_score_report_only", False)
        if outcomes_path is None and not report_only:
            raise RuntimeError("mutation outcomes.json not found")
        _add_step(
            ctx,
            "mutation-score",
            build_mutation_score_cmd(
                outcomes_path,
                ctx.args.mutation_score_threshold,
                ctx.args.mutation_score_max_age_hours,
                ctx.args.mutation_score_warn_age_hours,
                report_only,
            ),
            cwd=REPO_ROOT,
        )

    if ctx.settings.get("with_ci_release_gate", False):
        release_cmds = release_gate_fn()
        _add_step(ctx, "ci-status-gate", release_cmds[0], cwd=REPO_ROOT)
        release_env = dict(ctx.env)
        release_env["CI"] = "1"
        _add_step(
            ctx,
            "coderabbit-release-gate",
            release_cmds[1],
            cwd=REPO_ROOT,
            step_env=release_env,
        )
        _add_step(
            ctx,
            "coderabbit-ralph-release-gate",
            release_cmds[2],
            cwd=REPO_ROOT,
            step_env=release_env,
        )


# -------------------------------------------------------
# Report
# -------------------------------------------------------


def build_report_and_emit(ctx: CheckContext) -> int:
    """Format the check report and return the exit code."""
    success = all(step["returncode"] == 0 for step in ctx.steps)
    report = {
        "command": "check",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "steps": ctx.steps,
    }

    if should_emit_output(ctx.args):
        if ctx.args.format == "md":
            output = "# devctl check\n\n" + format_steps_md(ctx.steps)
        else:
            output = json.dumps(report, indent=2)
        if ctx.args.output or ctx.args.format != "text":
            write_output(output, ctx.args.output)
        if ctx.args.pipe_command:
            pipe_rc = pipe_output(output, ctx.args.pipe_command, ctx.args.pipe_args)
            if pipe_rc != 0:
                return pipe_rc

    return 0 if success else 1
