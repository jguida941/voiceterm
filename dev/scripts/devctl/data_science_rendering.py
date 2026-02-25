"""Rendering helpers for devctl data-science snapshots."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _write_bar_chart_svg(
    *,
    title: str,
    labels: list[str],
    values: list[float],
    output_path: Path,
    color: str,
) -> None:
    width = 980
    height = 420
    margin_l = 90
    margin_r = 24
    margin_t = 60
    margin_b = 90
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    max_value = max(max(values), 1.0) if values else 1.0
    count = max(1, len(labels))
    group_w = plot_w / count
    bar_w = group_w * 0.6

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width/2}" y="32" text-anchor="middle" font-family="Arial" font-size="22" fill="#111">{title}</text>',
        f'<line x1="{margin_l}" y1="{margin_t + plot_h}" x2="{margin_l + plot_w}" y2="{margin_t + plot_h}" stroke="#222" stroke-width="1"/>',
        f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + plot_h}" stroke="#222" stroke-width="1"/>',
    ]
    for idx in range(6):
        ratio = idx / 5
        y = margin_t + plot_h - (plot_h * ratio)
        value = max_value * ratio
        lines.append(
            f'<line x1="{margin_l}" y1="{y:.2f}" x2="{margin_l + plot_w}" y2="{y:.2f}" stroke="#ececec" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{margin_l - 8}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial" font-size="11" fill="#555">{value:.1f}</text>'
        )

    for idx, label in enumerate(labels):
        value = values[idx]
        height_px = (value / max_value) * plot_h if max_value else 0.0
        x = margin_l + (idx + 0.5) * group_w - (bar_w / 2)
        y = margin_t + plot_h - height_px
        lines.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{height_px:.2f}" fill="{color}"/>'
        )
        lines.append(
            f'<text x="{x + bar_w/2:.2f}" y="{y - 6:.2f}" text-anchor="middle" font-family="Arial" font-size="10" fill="#1f2937">{value:.2f}</text>'
        )
        lines.append(
            f'<text x="{x + bar_w/2:.2f}" y="{margin_t + plot_h + 20:.2f}" text-anchor="middle" font-family="Arial" font-size="11" fill="#1f2937">{label}</text>'
        )

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_data_science_charts(
    *,
    event_stats: dict[str, Any],
    agent_stats: dict[str, Any],
    charts_dir: Path,
) -> None:
    command_rows = event_stats.get("commands", [])
    if isinstance(command_rows, list) and command_rows:
        top_commands = command_rows[:10]
        _write_bar_chart_svg(
            title="Command Frequency (Top 10)",
            labels=[str(row.get("command")) for row in top_commands],
            values=[_safe_float(row.get("count"), default=0.0) for row in top_commands],
            output_path=charts_dir / "command_frequency.svg",
            color="#4e79a7",
        )

    agent_metric_rows = agent_stats.get("rows", [])
    if isinstance(agent_metric_rows, list) and agent_metric_rows:
        _write_bar_chart_svg(
            title="Agent Recommendation Score",
            labels=[str(row.get("selected_agents")) for row in agent_metric_rows],
            values=[
                _safe_float(row.get("recommendation_score"), default=0.0)
                for row in agent_metric_rows
            ],
            output_path=charts_dir / "agent_recommendation_score.svg",
            color="#f28e2b",
        )
        _write_bar_chart_svg(
            title="Tasks Per Minute by Agent Count",
            labels=[str(row.get("selected_agents")) for row in agent_metric_rows],
            values=[
                _safe_float(row.get("tasks_per_minute"), default=0.0)
                for row in agent_metric_rows
            ],
            output_path=charts_dir / "agent_tasks_per_minute.svg",
            color="#59a14f",
        )


def render_data_science_markdown(report: dict[str, Any]) -> str:
    event_stats = report.get("event_stats", {})
    agent_stats = report.get("agent_stats", {})
    rows = agent_stats.get("rows", []) if isinstance(agent_stats, dict) else []
    raw_rec = agent_stats.get("recommendation") if isinstance(agent_stats, dict) else {}
    rec = raw_rec if isinstance(raw_rec, dict) else {}

    lines = [
        "# Data Science Snapshot",
        "",
        f"- generated_at: {report.get('generated_at')}",
        f"- trigger_command: {report.get('trigger_command')}",
        f"- event_log: {report.get('event_log')}",
        "",
        "## devctl Event Metrics",
        f"- total_events: {event_stats.get('total_events')}",
        f"- success_rate_pct: {event_stats.get('success_rate_pct')}",
        f"- avg_duration_seconds: {event_stats.get('avg_duration_seconds')}",
        f"- p50_duration_seconds: {event_stats.get('p50_duration_seconds')}",
        f"- p95_duration_seconds: {event_stats.get('p95_duration_seconds')}",
        "",
        "## Agent Recommendation",
        f"- recommended_agents: {rec.get('selected_agents')}",
        f"- recommendation_score: {rec.get('recommendation_score')}",
        f"- reason: {rec.get('reason')}",
        "",
        "## Agent Stats",
        "| Agents | Runs | Success % | Avg Tasks | Avg Tasks/Agent | Tasks/Min | Score |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {selected_agents} | {runs} | {success_rate_pct} | {avg_tasks_completed} | "
            "{avg_tasks_per_agent} | {tasks_per_minute} | {recommendation_score} |".format(
                **row
            )
        )
    if not rows:
        lines.append("| - | - | - | - | - | - | - |")

    return "\n".join(lines)
