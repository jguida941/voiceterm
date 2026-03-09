"""devctl autonomy-benchmark command implementation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ..autonomy_benchmark_helpers import (
    explicit_question,
    fallback_repo_from_origin,
    parse_swarm_counts,
    parse_tactics,
    resolve_path,
    slug,
    validate_plan_scope,
)
from ..autonomy_benchmark_matrix import BenchmarkScenario
from ..autonomy_benchmark_render import build_charts as _build_charts
from ..autonomy_benchmark_render import render_markdown as _render_markdown
from ..autonomy_benchmark_runner import leaders, run_scenario_payload
from ..autonomy_run_helpers import collect_next_steps, derive_prompt
from ..common import emit_output, pipe_output, write_output
from ..numeric import to_float, to_int

try:
    from dev.scripts.checks.coderabbit_ralph_loop_core import resolve_repo
except ModuleNotFoundError:
    from checks.coderabbit_ralph_loop_core import resolve_repo


def _timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _summarize_overall(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    swarms_total = sum(
        to_int((row.get("summary") or {}).get("swarms_total"), default=0)
        for row in scenarios
        if isinstance(row, dict)
    )
    swarms_ok = sum(
        to_int((row.get("summary") or {}).get("swarms_ok"), default=0)
        for row in scenarios
        if isinstance(row, dict)
    )
    tasks_completed_total = sum(
        to_int((row.get("summary") or {}).get("tasks_completed_total"), default=0)
        for row in scenarios
        if isinstance(row, dict)
    )
    rounds_completed_total = sum(
        to_int((row.get("summary") or {}).get("rounds_completed_total"), default=0)
        for row in scenarios
        if isinstance(row, dict)
    )
    work_output_score_total = sum(
        to_int((row.get("summary") or {}).get("work_output_score"), default=0)
        for row in scenarios
        if isinstance(row, dict)
    )
    elapsed_seconds_total = sum(
        to_float((row.get("summary") or {}).get("elapsed_seconds_total"), default=0.0)
        for row in scenarios
        if isinstance(row, dict)
    )
    return {
        "scenarios_total": len(scenarios),
        "swarms_total": swarms_total,
        "swarms_ok": swarms_ok,
        "swarms_failed": swarms_total - swarms_ok,
        "tasks_completed_total": tasks_completed_total,
        "rounds_completed_total": rounds_completed_total,
        "work_output_score_total": work_output_score_total,
        "elapsed_seconds_total": round(elapsed_seconds_total, 3),
    }


def _validate_benchmark_args(args, *, plan_doc, index_doc, master_plan_doc) -> str | None:
    for path in (plan_doc, index_doc, master_plan_doc):
        if not path.exists():
            return f"Error: missing required file: {path}"
    if int(args.next_steps_limit) < 1:
        return "Error: --next-steps-limit must be >= 1"
    if int(args.agents) < 1:
        return "Error: --agents must be >= 1"
    if int(args.parallel_workers) < 1 or int(args.max_concurrent_swarms) < 1:
        return "Error: parallel worker counts must be >= 1"
    mode = str(args.mode)
    fix_command = str(args.fix_command or "").strip()
    if mode in {"plan-then-fix", "fix-only"} and not fix_command:
        return (
            "Error: --fix-command is required when --mode is plan-then-fix/fix-only "
            "(otherwise no remediation can run)"
        )
    return None


def _resolve_benchmark_repo(args) -> str | None:
    repo = resolve_repo(args.repo)
    if repo:
        return repo
    return fallback_repo_from_origin()


def _resolve_benchmark_scenarios(args) -> tuple[list[int], list[str], list[str]]:
    swarm_counts = parse_swarm_counts(str(args.swarm_counts))
    if not swarm_counts:
        return [], [], ["Error: --swarm-counts must contain at least one positive integer"]
    tactics, tactic_warnings = parse_tactics(str(args.tactics))
    if not tactics:
        return [], tactic_warnings, ["Error: --tactics must contain at least one supported tactic"]
    return swarm_counts, tactics, tactic_warnings


def _render_benchmark_output(args, report: dict[str, Any]) -> str:
    json_payload = json.dumps(report, indent=2)
    return json_payload if args.format == "json" else _render_markdown(report)


def run(args) -> int:
    """Run swarm-size/tactic benchmark matrix and emit tradeoff metrics."""
    plan_doc = resolve_path(str(args.plan_doc))
    index_doc = resolve_path(str(args.index_doc))
    master_plan_doc = resolve_path(str(args.master_plan_doc))
    validation_error = _validate_benchmark_args(
        args,
        plan_doc=plan_doc,
        index_doc=index_doc,
        master_plan_doc=master_plan_doc,
    )
    if validation_error:
        print(validation_error)
        return 2

    swarm_counts, tactics, tactic_warnings = _resolve_benchmark_scenarios(args)
    if not swarm_counts or not tactics:
        print(
            "Error: --swarm-counts must contain at least one positive integer"
            if not swarm_counts
            else "Error: --tactics must contain at least one supported tactic"
        )
        return 2

    repo = _resolve_benchmark_repo(args)
    if not repo:
        print(
            "Error: unable to resolve repository (pass --repo or set GITHUB_REPOSITORY)."
        )
        return 2

    plan_text, _index_text, plan_rel, warnings, errors = validate_plan_scope(
        plan_doc=plan_doc,
        index_doc=index_doc,
        master_plan_doc=master_plan_doc,
        mp_scope=str(args.mp_scope),
    )
    warnings.extend(tactic_warnings)
    if errors:
        print("\n".join(f"Error: {item}" for item in errors))
        return 2

    explicit = explicit_question(args)
    next_steps = collect_next_steps(plan_text, limit=int(args.next_steps_limit))
    base_prompt = derive_prompt(
        plan_doc=plan_rel,
        mp_scope=str(args.mp_scope),
        next_steps=next_steps,
        explicit_question=explicit,
    )

    run_label = slug(
        str(
            args.run_label
            or f"autonomy-benchmark-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%SZ')}"
        ),
        fallback="autonomy-benchmark",
    )
    output_root = resolve_path(str(args.output_root))
    benchmark_dir = output_root / run_label
    charts_dir = benchmark_dir / "charts"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    scenarios: list[dict[str, Any]] = []
    for tactic in tactics:
        for swarm_count in swarm_counts:
            scenario = BenchmarkScenario(tactic=tactic, swarm_count=int(swarm_count))
            scenarios.append(
                run_scenario_payload(
                    args=args,
                    repo=repo,
                    benchmark_label=run_label,
                    scenario=scenario,
                    base_prompt=base_prompt,
                    next_steps=next_steps,
                    benchmark_dir=benchmark_dir,
                )
            )

    overall_summary = _summarize_overall(scenarios)
    overall_ok = int(overall_summary.get("swarms_failed") or 0) == 0 and not errors
    report: dict[str, Any] = {
        "command": "autonomy-benchmark",
        "timestamp": _timestamp_utc(),
        "ok": overall_ok,
        "repo": repo,
        "run_label": run_label,
        "plan_doc": plan_rel,
        "mp_scope": str(args.mp_scope),
        "benchmark_dir": str(benchmark_dir),
        "swarm_counts": swarm_counts,
        "tactics": tactics,
        "settings": {
            "mode": str(args.mode),
            "fix_command_configured": bool(str(args.fix_command or "").strip()),
            "agents_per_swarm": int(args.agents),
            "parallel_workers_per_swarm": int(args.parallel_workers),
            "max_concurrent_swarms": int(args.max_concurrent_swarms),
            "dry_run": bool(args.dry_run),
            "post_audit": bool(args.post_audit),
            "reviewer_lane": bool(args.reviewer_lane),
        },
        "base_prompt": base_prompt,
        "next_steps": next_steps,
        "scenarios": scenarios,
        "overall_summary": overall_summary,
        "leaders": leaders(scenarios),
        "warnings": warnings,
        "errors": errors,
        "charts": [],
    }

    if bool(args.charts):
        chart_paths, chart_warning = _build_charts(report, charts_dir)
        report["charts"] = chart_paths
        if chart_warning:
            report["warnings"].append(chart_warning)

    summary_json = benchmark_dir / "summary.json"
    summary_md = benchmark_dir / "summary.md"
    summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_md.write_text(_render_markdown(report), encoding="utf-8")

    json_payload = json.dumps(report, indent=2)
    output = _render_benchmark_output(args, report)
    pipe_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        additional_outputs=[(json_payload, args.json_output)] if args.json_output else None,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_code != 0:
        return pipe_code

    return 0 if overall_ok else 1
