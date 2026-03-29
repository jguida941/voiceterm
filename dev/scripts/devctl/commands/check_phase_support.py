"""Support helpers for optional `devctl check` phases and reporting."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from ..config import REPO_ROOT, SRC_DIR

StepSpec = dict[str, object]
AddStepFn = Callable[..., None]
AddStepsFn = Callable[[Any, list[StepSpec], bool], None]
MakeStepSpecFn = Callable[..., StepSpec]


@dataclass(frozen=True)
class SpecializedPhaseDeps:
    """Callback bundle for specialized check phases."""

    resolve_perf_log_path_fn: Callable[[], str]
    build_mutants_cmd_fn: Callable[[object], list[str]]
    resolve_outcomes_path_fn: Callable[[str | None], str | None]
    build_mutation_score_cmd_fn: Callable[..., list[str]]


def run_specialized_phase_support(
    *,
    ctx,
    add_step_fn: AddStepFn,
    release_gate_fn,
    deps: SpecializedPhaseDeps,
) -> None:
    """Execute optional wake/perf/memory/mutation/release phases."""
    if ctx.settings["with_wake_guard"]:
        wake_env = dict(ctx.env)
        wake_env["WAKE_WORD_SOAK_ROUNDS"] = str(ctx.args.wake_soak_rounds)
        add_step_fn(
            ctx,
            "wake-guard",
            ["bash", "dev/scripts/tests/wake_word_guard.sh"],
            cwd=REPO_ROOT,
            step_env=wake_env,
        )

    if ctx.settings["with_perf"]:
        add_step_fn(
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
            log_path = deps.resolve_perf_log_path_fn()
            add_step_fn(
                ctx,
                "perf-verify",
                ["python3", ".github/scripts/verify_perf_metrics.py", log_path],
                cwd=REPO_ROOT,
            )

    if ctx.settings["with_mem_loop"]:
        for index in range(ctx.args.mem_iterations):
            add_step_fn(
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
        add_step_fn(
            ctx,
            "mutants",
            deps.build_mutants_cmd_fn(mutants_args),
            cwd=REPO_ROOT,
        )

    if ctx.settings["with_mutation_score"]:
        outcomes_path = deps.resolve_outcomes_path_fn(ctx.args.mutation_score_path)
        report_only = ctx.settings.get("mutation_score_report_only", False)
        if outcomes_path is None and not report_only:
            raise RuntimeError("mutation outcomes.json not found")
        add_step_fn(
            ctx,
            "mutation-score",
            deps.build_mutation_score_cmd_fn(
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
        add_step_fn(ctx, "ci-status-gate", release_cmds[0], cwd=REPO_ROOT)
        release_env = dict(ctx.env)
        release_env["CI"] = "1"
        add_step_fn(
            ctx,
            "coderabbit-release-gate",
            release_cmds[1],
            cwd=REPO_ROOT,
            step_env=release_env,
        )
        add_step_fn(
            ctx,
            "coderabbit-ralph-release-gate",
            release_cmds[2],
            cwd=REPO_ROOT,
            step_env=release_env,
        )


def run_probe_phase_support(
    *,
    ctx,
    make_step_spec_fn: MakeStepSpecFn,
    add_steps_fn: AddStepsFn,
    review_probe_checks,
    build_probe_cmd_fn,
) -> None:
    """Run non-blocking review probes for the current check profile."""
    if not ctx.settings.get("with_review_probes", False):
        return

    def _field(spec, attr: str, index: int):
        if hasattr(spec, attr):
            return getattr(spec, attr)
        return spec[index]

    since_ref = getattr(ctx, "scan_since_ref", None)
    head_ref = getattr(ctx, "scan_head_ref", "HEAD")
    adoption_scan = getattr(ctx, "scan_mode", "working-tree") == "adoption-scan"
    probe_specs = [
        make_step_spec_fn(
            ctx,
            _field(spec, "step_name", 0),
            build_probe_cmd_fn(
                _field(spec, "script_id", 1),
                since_ref=since_ref,
                head_ref=head_ref,
                adoption_scan=adoption_scan,
                extra_args=_field(spec, "extra_args", 2),
            ),
            cwd=REPO_ROOT,
        )
        for spec in review_probe_checks
    ]
    add_steps_fn(ctx, probe_specs, True)


def build_report_and_emit_support(
    *,
    ctx,
    format_steps_md_fn,
    should_emit_output_fn,
    emit_output_fn,
    pipe_output_fn,
    write_output_fn,
) -> int:
    """Format the final `devctl check` report and emit it if requested."""
    success = all(step["returncode"] == 0 for step in ctx.steps)
    report = {
        "command": "check",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "steps": ctx.steps,
    }

    if should_emit_output_fn(ctx.args):
        if ctx.args.format == "md":
            output = "# devctl check\n\n" + format_steps_md_fn(ctx.steps)
        else:
            output = json.dumps(report, indent=2)
        if ctx.args.output or ctx.args.format != "text":
            pipe_rc = emit_output_fn(
                output,
                output_path=ctx.args.output,
                pipe_command=ctx.args.pipe_command,
                pipe_args=ctx.args.pipe_args,
                writer=write_output_fn,
                piper=pipe_output_fn,
            )
            if pipe_rc != 0:
                return pipe_rc

    return 0 if success else 1
