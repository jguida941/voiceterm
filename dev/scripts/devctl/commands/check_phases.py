"""Check phase orchestration for `devctl check`.

Each phase function takes a CheckContext and mutates its step list.
Called exclusively from check.run().
"""

from __future__ import annotations

import dataclasses

from ..common import emit_output as _emit_output
from ..common import pipe_output as _pipe_output
from ..common import run_cmd
from ..common import should_emit_output as _should_emit_output
from ..common import write_output as _write_output
from ..config import REPO_ROOT, SRC_DIR
from ..quality_policy import QualityStepSpec
from .check_phase_support import (
    SpecializedPhaseDeps,
    run_probe_phase_support,
    run_specialized_phase_support,
)
from .check_progress import emit_progress
from .check_steps import build_step_spec, run_step_specs
from .check_support import (
    build_ai_guard_cmd,
    build_clippy_high_signal_collect_cmd,
    build_clippy_high_signal_guard_cmd,
    build_clippy_pedantic_collect_cmd,
    build_probe_cmd,
    maybe_emit_ai_guard_scaffold,
    resolve_perf_log_path,
)
from .mutants import build_mutants_cmd
from .mutation_score import build_mutation_score_cmd, resolve_outcomes_path

emit_output = _emit_output
pipe_output = _pipe_output
should_emit_output = _should_emit_output
write_output = _write_output

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
    ai_guard_checks: tuple[QualityStepSpec, ...] = dataclasses.field(default_factory=tuple)
    review_probe_checks: tuple[QualityStepSpec, ...] = dataclasses.field(default_factory=tuple)
    scan_mode: str = "working-tree"
    scan_since_ref: str | None = None
    scan_head_ref: str = "HEAD"
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


def _make_step_spec(ctx: CheckContext, name: str, cmd: list[str], cwd=None, step_env=None) -> dict:
    return build_step_spec(
        name=name,
        cmd=cmd,
        default_env=ctx.env,
        cwd=cwd,
        step_env=step_env,
    )


def _add_steps(ctx: CheckContext, step_specs: list[dict], allow_parallel: bool = False) -> None:
    """Execute step specs, collect results, and handle scaffold/fail-fast."""
    if not step_specs:
        return
    use_parallel = allow_parallel and ctx.parallel_enabled
    if ctx.total_quality_steps > 0:
        emit_progress(step_specs, ctx.progress_counter, ctx.total_quality_steps, use_parallel)
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
        dry_run=ctx.args.dry_run,
        ai_guard_step_names={spec.step_name for spec in ctx.ai_guard_checks},
    )
    if scaffold_result is not None:
        ctx.steps.append(scaffold_result)
        if scaffold_result["returncode"] == 0:
            print("[check] generated remediation scaffold:" " dev/reports/audits/RUST_AUDIT_FINDINGS.md")
        else:
            print("[check] failed to generate remediation scaffold")
            if scaffold_result.get("error"):
                print(f"[check] scaffold error: {scaffold_result['error']}")

    if failed and not ctx.args.keep_going:
        failed_steps = ", ".join(result["name"] for result in results if result["returncode"] != 0)
        raise RuntimeError(f"check phase failed ({failed_steps})")


def _add_step(ctx: CheckContext, name: str, cmd: list[str], cwd=None, step_env=None) -> None:
    _add_steps(ctx, [_make_step_spec(ctx, name, cmd, cwd=cwd, step_env=step_env)])


# -------------------------------------------------------
# Phase runners
# -------------------------------------------------------


def run_setup_phase(ctx: CheckContext) -> None:
    """Lint phase: fmt, clippy, and AI-guard steps."""
    setup_specs: list[dict] = []
    followup_specs: list[dict] = []

    if not ctx.args.skip_fmt:
        if ctx.args.fix:
            setup_specs.append(_make_step_spec(ctx, "fmt", ["cargo", "fmt", "--all"], cwd=SRC_DIR))
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
        elif getattr(ctx.args, "profile", None) == "pedantic":
            setup_specs.append(
                _make_step_spec(
                    ctx,
                    "clippy",
                    build_clippy_pedantic_collect_cmd(),
                    cwd=REPO_ROOT,
                )
            )
        else:
            setup_specs.append(_make_step_spec(ctx, "clippy", ctx.clippy_cmd, cwd=SRC_DIR))

    if ctx.settings["with_ai_guard"]:
        since_ref = ctx.scan_since_ref
        head_ref = ctx.scan_head_ref
        setup_specs.extend(
            _make_step_spec(
                ctx,
                spec.step_name,
                build_ai_guard_cmd(
                    spec.script_id,
                    since_ref=since_ref,
                    head_ref=head_ref,
                    adoption_scan=ctx.scan_mode == "adoption-scan",
                    extra_args=spec.extra_args,
                ),
                cwd=REPO_ROOT,
            )
            for spec in ctx.ai_guard_checks
        )

    _add_steps(ctx, setup_specs, allow_parallel=True)
    _add_steps(ctx, followup_specs)


def run_test_build_phase(ctx: CheckContext) -> None:
    """Compile and test phase: cargo test + release build."""
    specs: list[dict] = []
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
    specialized_phase_deps = SpecializedPhaseDeps(
        resolve_perf_log_path_fn=resolve_perf_log_path,
        build_mutants_cmd_fn=build_mutants_cmd,
        resolve_outcomes_path_fn=resolve_outcomes_path,
        build_mutation_score_cmd_fn=build_mutation_score_cmd,
    )
    run_specialized_phase_support(
        ctx=ctx,
        add_step_fn=_add_step,
        release_gate_fn=release_gate_fn,
        deps=specialized_phase_deps,
    )


# -------------------------------------------------------
# Review probes (heuristic risk hints, never fail)
# -------------------------------------------------------


def run_probe_phase(ctx: CheckContext) -> None:
    """Run review probes that emit risk hints without blocking the build."""
    run_probe_phase_support(
        ctx=ctx,
        make_step_spec_fn=_make_step_spec,
        add_steps_fn=_add_steps,
        review_probe_checks=ctx.review_probe_checks,
        build_probe_cmd_fn=build_probe_cmd,
    )
