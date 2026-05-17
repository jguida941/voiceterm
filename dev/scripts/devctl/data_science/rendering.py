"""Rendering helpers for devctl data-science snapshots."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..numeric import to_float


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
        lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{height_px:.2f}" fill="{color}"/>')
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
    watchdog_stats: dict[str, Any],
    charts_dir: Path,
) -> None:
    command_rows = event_stats.get("commands", [])
    if isinstance(command_rows, list) and command_rows:
        top_commands = command_rows[:10]
        _write_bar_chart_svg(
            title="Command Frequency (Top 10)",
            labels=[str(row.get("command")) for row in top_commands],
            values=[to_float(row.get("count"), default=0.0) for row in top_commands],
            output_path=charts_dir / "command_frequency.svg",
            color="#4e79a7",
        )

    agent_metric_rows = agent_stats.get("rows", [])
    if isinstance(agent_metric_rows, list) and agent_metric_rows:
        _write_bar_chart_svg(
            title="Agent Recommendation Score",
            labels=[str(row.get("selected_agents")) for row in agent_metric_rows],
            values=[to_float(row.get("recommendation_score"), default=0.0) for row in agent_metric_rows],
            output_path=charts_dir / "agent_recommendation_score.svg",
            color="#f28e2b",
        )
        _write_bar_chart_svg(
            title="Tasks Per Minute by Agent Count",
            labels=[str(row.get("selected_agents")) for row in agent_metric_rows],
            values=[to_float(row.get("tasks_per_minute"), default=0.0) for row in agent_metric_rows],
            output_path=charts_dir / "agent_tasks_per_minute.svg",
            color="#59a14f",
        )

    watchdog_families = watchdog_stats.get("guard_families", [])
    if isinstance(watchdog_families, list) and watchdog_families:
        top_families = watchdog_families[:10]
        _write_bar_chart_svg(
            title="Watchdog Episodes by Guard Family",
            labels=[str(row.get("guard_family")) for row in top_families],
            values=[to_float(row.get("episodes"), default=0.0) for row in top_families],
            output_path=charts_dir / "watchdog_guard_family_frequency.svg",
            color="#e15759",
        )
        _write_bar_chart_svg(
            title="Watchdog Avg Time To Green",
            labels=[str(row.get("guard_family")) for row in top_families],
            values=[to_float(row.get("avg_time_to_green_seconds"), default=0.0) for row in top_families],
            output_path=charts_dir / "watchdog_time_to_green.svg",
            color="#76b7b2",
        )


def render_data_science_markdown(report: dict[str, Any]) -> str:
    event_stats = report.get("event_stats", {})
    agent_stats = report.get("agent_stats", {})
    watchdog_stats = report.get("watchdog_stats", {})
    governance_review_stats = report.get("governance_review_stats", {})
    external_finding_stats = report.get("external_finding_stats", {})
    rows = agent_stats.get("rows", []) if isinstance(agent_stats, dict) else []
    raw_rec = agent_stats.get("recommendation") if isinstance(agent_stats, dict) else {}
    rec = raw_rec if isinstance(raw_rec, dict) else {}
    watchdog_rows = watchdog_stats.get("guard_families", []) if isinstance(watchdog_stats, dict) else []
    governance_check_rows = (
        governance_review_stats.get("by_check_id", []) if isinstance(governance_review_stats, dict) else []
    )
    external_repo_rows = (
        external_finding_stats.get("by_repo", []) if isinstance(external_finding_stats, dict) else []
    )
    external_check_rows = (
        external_finding_stats.get("by_check_id", []) if isinstance(external_finding_stats, dict) else []
    )

    lines = [
        "# Data Science Snapshot",
        "",
        f"- generated_at: {report.get('generated_at')}",
        f"- trigger_command: {report.get('trigger_command')}",
        f"- event_log: {report.get('event_log')}",
        f"- governance_review_log: {report.get('governance_review_log')}",
        f"- external_finding_log: {report.get('external_finding_log')}",
        "",
        "## devctl Event Metrics",
        f"- total_events: {event_stats.get('total_events')}",
        f"- success_rate_pct: {event_stats.get('success_rate_pct')}",
        f"- avg_duration_seconds: {event_stats.get('avg_duration_seconds')}",
        f"- p50_duration_seconds: {event_stats.get('p50_duration_seconds')}",
        f"- p95_duration_seconds: {event_stats.get('p95_duration_seconds')}",
        f"- total_machine_output_bytes: {event_stats.get('total_machine_output_bytes')}",
        f"- total_estimated_machine_tokens: {event_stats.get('total_estimated_machine_tokens')}",
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
            "{avg_tasks_per_agent} | {tasks_per_minute} | {recommendation_score} |".format(**row)
        )
    if not rows:
        lines.append("| - | - | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## Watchdog Metrics",
            f"- total_episodes: {watchdog_stats.get('total_episodes')}",
            f"- success_rate_pct: {watchdog_stats.get('success_rate_pct')}",
            f"- avg_time_to_green_seconds: {watchdog_stats.get('avg_time_to_green_seconds')}",
            f"- p50_time_to_green_seconds: {watchdog_stats.get('p50_time_to_green_seconds')}",
            f"- avg_guard_runtime_seconds: {watchdog_stats.get('avg_guard_runtime_seconds')}",
            f"- avg_retry_count: {watchdog_stats.get('avg_retry_count')}",
            f"- avg_escaped_findings: {watchdog_stats.get('avg_escaped_findings')}",
            f"- false_positive_rate_pct: {watchdog_stats.get('false_positive_rate_pct')}",
            "",
            "## Watchdog Guard Families",
            "| Guard Family | Episodes | Success % | Avg Time To Green (s) |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in watchdog_rows:
        lines.append("| {guard_family} | {episodes} | {success_rate_pct} | {avg_time_to_green_seconds} |".format(**row))
    if not watchdog_rows:
        lines.append("| - | - | - | - |")

    lines.extend(
        [
            "",
            "## External Finding Corpus",
            f"- total_findings: {external_finding_stats.get('total_findings')}",
            f"- unique_repo_count: {external_finding_stats.get('unique_repo_count')}",
            f"- unique_import_run_count: {external_finding_stats.get('unique_import_run_count')}",
            f"- reviewed_count: {external_finding_stats.get('reviewed_count')}",
            f"- unreviewed_count: {external_finding_stats.get('unreviewed_count')}",
            f"- adjudication_coverage_pct: {external_finding_stats.get('adjudication_coverage_pct')}",
            f"- false_positive_count: {external_finding_stats.get('false_positive_count')}",
            f"- fixed_count: {external_finding_stats.get('fixed_count')}",
            "",
            "## External Findings By Repo",
            "| Repo | Findings | Reviewed | Coverage % | False Positives | Fixed |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in external_repo_rows:
        lines.append(
            "| {bucket} | {total_findings} | {reviewed_count} | "
            "{adjudication_coverage_pct} | {false_positive_count} | {fixed_count} |".format(**row)
        )
    if not external_repo_rows:
        lines.append("| - | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## External Findings By Check",
            "| Check | Findings | Reviewed | Coverage % | False Positives | Fixed |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in external_check_rows:
        lines.append(
            "| {bucket} | {total_findings} | {reviewed_count} | "
            "{adjudication_coverage_pct} | {false_positive_count} | {fixed_count} |".format(**row)
        )
    if not external_check_rows:
        lines.append("| - | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## Governance Review Metrics",
            f"- total_findings: {governance_review_stats.get('total_findings')}",
            f"- false_positive_rate_pct: {governance_review_stats.get('false_positive_rate_pct')}",
            f"- positive_finding_rate_pct: {governance_review_stats.get('positive_finding_rate_pct')}",
            f"- cleanup_rate_pct: {governance_review_stats.get('cleanup_rate_pct')}",
            f"- fixed_count: {governance_review_stats.get('fixed_count')}",
            f"- deferred_count: {governance_review_stats.get('deferred_count')}",
            f"- waived_count: {governance_review_stats.get('waived_count')}",
            "",
            "## Governance Review By Check",
            "| Check | Findings | False Positives | FP % | Fixed | Cleanup % |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in governance_check_rows:
        lines.append(
            "| {bucket} | {total_findings} | {false_positive_count} | "
            "{false_positive_rate_pct} | {fixed_count} | {cleanup_rate_pct} |".format(**row)
        )
    if not governance_check_rows:
        lines.append("| - | - | - | - | - | - |")

    return "\n".join(lines)
