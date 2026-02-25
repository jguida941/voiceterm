"""Render/chart helpers for `devctl autonomy-benchmark`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .numeric import to_float, to_int


def build_charts(
    report: dict[str, Any], chart_dir: Path
) -> tuple[list[str], str | None]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:
        return [], f"matplotlib unavailable: {exc}"

    chart_dir.mkdir(parents=True, exist_ok=True)
    chart_paths: list[str] = []
    scenarios = (
        report.get("scenarios") if isinstance(report.get("scenarios"), list) else []
    )
    if not scenarios:
        return chart_paths, None

    labels: list[str] = []
    work_scores: list[int] = []
    tasks_per_min: list[float] = []
    success_rates: list[float] = []
    for row in scenarios:
        if not isinstance(row, dict):
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), dict) else {}
        labels.append(str(row.get("label") or "scenario"))
        work_scores.append(to_int(summary.get("work_output_score"), default=0))
        tasks_per_min.append(to_float(summary.get("tasks_per_minute"), default=0.0))
        success_rates.append(to_float(summary.get("swarm_success_pct"), default=0.0))

    if labels:
        work_chart = chart_dir / "scenario_work_output.png"
        figure = plt.figure(figsize=(11, 4.8))
        axis = figure.add_subplot(111)
        axis.bar(labels, work_scores, color="#2563eb")
        axis.set_title("Work Output Score by Scenario")
        axis.set_ylabel("tasks_completed_total + resolved_rows_total")
        axis.tick_params(axis="x", rotation=30)
        figure.tight_layout()
        figure.savefig(work_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(work_chart))

        throughput_chart = chart_dir / "scenario_tasks_per_minute.png"
        figure = plt.figure(figsize=(11, 4.8))
        axis = figure.add_subplot(111)
        axis.bar(labels, tasks_per_min, color="#16a34a")
        axis.set_title("Tasks Per Minute by Scenario")
        axis.set_ylabel("tasks/min")
        axis.tick_params(axis="x", rotation=30)
        figure.tight_layout()
        figure.savefig(throughput_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(throughput_chart))

        success_chart = chart_dir / "scenario_success_rate_pct.png"
        figure = plt.figure(figsize=(11, 4.8))
        axis = figure.add_subplot(111)
        axis.plot(labels, success_rates, marker="o", color="#ea580c")
        axis.set_title("Swarm Success Rate (%) by Scenario")
        axis.set_ylabel("success %")
        axis.set_ylim(0.0, 100.0)
        axis.tick_params(axis="x", rotation=30)
        figure.tight_layout()
        figure.savefig(success_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(success_chart))

    return chart_paths, None


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Autonomy Benchmark Report", ""]
    lines.append(f"- generated_at: {report.get('timestamp')}")
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- run_label: {report.get('run_label')}")
    lines.append(f"- benchmark_dir: {report.get('benchmark_dir')}")
    lines.append(f"- plan_doc: {report.get('plan_doc')}")
    lines.append(f"- mp_scope: {report.get('mp_scope')}")
    lines.append(f"- tactics: {', '.join(report.get('tactics', []))}")
    lines.append(
        f"- swarm_counts: {', '.join(str(value) for value in report.get('swarm_counts', []))}"
    )

    overall = (
        report.get("overall_summary")
        if isinstance(report.get("overall_summary"), dict)
        else {}
    )
    lines.append("")
    lines.append("## Overall Summary")
    lines.append(f"- scenarios_total: {overall.get('scenarios_total')}")
    lines.append(f"- swarms_total: {overall.get('swarms_total')}")
    lines.append(f"- swarms_ok: {overall.get('swarms_ok')}")
    lines.append(f"- swarms_failed: {overall.get('swarms_failed')}")
    lines.append(f"- tasks_completed_total: {overall.get('tasks_completed_total')}")
    lines.append(f"- rounds_completed_total: {overall.get('rounds_completed_total')}")
    lines.append(f"- work_output_score_total: {overall.get('work_output_score_total')}")
    lines.append(f"- elapsed_seconds_total: {overall.get('elapsed_seconds_total')}")

    lines.append("")
    lines.append("## Scenario Matrix")
    lines.append("")
    lines.append(
        "| Scenario | Tactic | Swarms | Success % | Tasks | Work score | Tasks/min | Elapsed (s) | Details |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")
    scenarios = (
        report.get("scenarios") if isinstance(report.get("scenarios"), list) else []
    )
    for row in scenarios:
        if not isinstance(row, dict):
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), dict) else {}
        lines.append(
            f"| `{row.get('label')}` | `{row.get('tactic')}` | "
            f"{summary.get('swarms_total')} | {summary.get('swarm_success_pct')} | "
            f"{summary.get('tasks_completed_total')} | {summary.get('work_output_score')} | "
            f"{summary.get('tasks_per_minute')} | {summary.get('elapsed_seconds_total')} | "
            f"`{row.get('summary_json') or row.get('scenario_dir') or 'n/a'}` |"
        )

    leaders = report.get("leaders") if isinstance(report.get("leaders"), dict) else {}
    if leaders:
        lines.append("")
        lines.append("## Leaderboard")
        for key in ("best_work_output", "best_tasks_per_minute", "best_success_rate"):
            row = leaders.get(key)
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- {key}: `{row.get('label')}` ({row.get('value')} from {row.get('metric')})"
            )

    charts = report.get("charts")
    if isinstance(charts, list) and charts:
        lines.append("")
        lines.append("## Charts")
        for chart in charts:
            lines.append(f"- `{chart}`")

    warnings = report.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.append("")
        lines.append("## Warnings")
        for row in warnings:
            lines.append(f"- {row}")

    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        lines.append("")
        lines.append("## Errors")
        for row in errors:
            lines.append(f"- {row}")

    return "\n".join(lines)
