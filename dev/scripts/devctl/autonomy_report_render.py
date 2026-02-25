"""Render/chart helpers for `devctl autonomy-report`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .numeric import to_int, to_optional_float


def build_charts(
    report: dict[str, Any], chart_dir: Path
) -> tuple[list[str], str | None]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:
        return [], f"matplotlib unavailable: {exc}"

    chart_dir.mkdir(parents=True, exist_ok=True)
    chart_paths: list[str] = []

    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    bar_chart = chart_dir / "autonomy_overview.png"
    labels = ["triage_unresolved", "mutation_gap_pct", "rounds", "orchestrate_errors"]
    values = [
        to_int(metrics.get("triage_unresolved_count"), default=0),
        to_optional_float(metrics.get("mutation_score_gap_pct"), default=0.0) or 0.0,
        to_int(metrics.get("autonomy_rounds_completed"), default=0),
        to_int(metrics.get("orchestrate_errors_count"), default=0),
    ]
    figure = plt.figure(figsize=(8, 4.5))
    axis = figure.add_subplot(111)
    axis.bar(labels, values, color=["#2563eb", "#f97316", "#16a34a", "#dc2626"])
    axis.set_title("Autonomy Loop Overview")
    axis.set_ylabel("Value")
    figure.tight_layout()
    figure.savefig(bar_chart, dpi=150)
    plt.close(figure)
    chart_paths.append(str(bar_chart))

    autonomy_loop_source = {}
    sources = report.get("sources")
    if isinstance(sources, dict):
        autonomy_loop_source = (
            sources.get("autonomy_loop")
            if isinstance(sources.get("autonomy_loop"), dict)
            else {}
        )
    autonomy_loop_summary = (
        autonomy_loop_source.get("summary")
        if isinstance(autonomy_loop_source.get("summary"), dict)
        else {}
    )
    rounds = autonomy_loop_summary.get("unresolved_by_round")
    if isinstance(rounds, list) and rounds:
        round_chart = chart_dir / "autonomy_round_unresolved.png"
        figure = plt.figure(figsize=(8, 4.5))
        axis = figure.add_subplot(111)
        axis.plot(range(1, len(rounds) + 1), rounds, marker="o", color="#7c3aed")
        axis.set_title("Unresolved Count by Autonomy Round")
        axis.set_xlabel("Round")
        axis.set_ylabel("Unresolved")
        figure.tight_layout()
        figure.savefig(round_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(round_chart))

    source_names: list[str] = []
    source_freshness: list[float] = []
    rows = report.get("sources")
    if isinstance(rows, dict):
        for name, payload in rows.items():
            if (
                isinstance(payload, dict)
                and payload.get("found")
                and payload.get("freshness_hours") is not None
            ):
                source_names.append(name)
                source_freshness.append(float(payload["freshness_hours"]))
    if source_names:
        freshness_chart = chart_dir / "source_freshness_hours.png"
        figure = plt.figure(figsize=(9, 4.5))
        axis = figure.add_subplot(111)
        axis.bar(source_names, source_freshness, color="#0891b2")
        axis.set_title("Source Freshness (hours)")
        axis.set_ylabel("Hours")
        axis.tick_params(axis="x", rotation=20)
        figure.tight_layout()
        figure.savefig(freshness_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(str(freshness_chart))

    return chart_paths, None


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Autonomy Report", ""]
    lines.append(f"- generated_at: {report.get('timestamp')}")
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- run_label: {report.get('run_label')}")
    lines.append(f"- bundle_dir: {report.get('bundle_dir')}")
    lines.append(f"- source_root: {report.get('source_root')}")
    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    lines.append(f"- triage_unresolved_count: {metrics.get('triage_unresolved_count')}")
    lines.append(f"- mutation_score_gap_pct: {metrics.get('mutation_score_gap_pct')}")
    lines.append(
        f"- autonomy_rounds_completed: {metrics.get('autonomy_rounds_completed')}"
    )
    lines.append(f"- autonomy_resolved: {metrics.get('autonomy_resolved')}")
    lines.append(
        f"- orchestrate_errors_count: {metrics.get('orchestrate_errors_count')}"
    )
    lines.append(f"- stale_agent_count: {metrics.get('stale_agent_count')}")
    lines.append(f"- event_count: {metrics.get('event_count')}")

    lines.append("")
    lines.append("## Sources")
    lines.append("")
    lines.append("| Source | Found | Freshness (h) | Path |")
    lines.append("|---|---|---:|---|")
    sources = report.get("sources") if isinstance(report.get("sources"), dict) else {}
    for name in sorted(sources):
        row = sources.get(name)
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| `{name}` | {row.get('found')} | {row.get('freshness_hours')} | `{row.get('path') or 'n/a'}` |"
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
