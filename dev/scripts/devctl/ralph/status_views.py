"""Projection/render helpers for `devctl ralph-status`."""

from __future__ import annotations

from typing import Any


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_str(value: Any, default: str = "") -> str:
    return str(value).strip() if value else default


def render_ralph_status_markdown(report: dict[str, Any]) -> str:
    """Render a compact status view for a single ralph report."""
    lines = [
        "# Ralph Guardrail Status",
        "",
        f"- generated_at: {report.get('generated_at', 'n/a')}",
        f"- report_count: {report.get('report_count', 0)}",
        f"- report_dir: {report.get('report_dir', 'n/a')}",
        "",
    ]

    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- total_violations: {_safe_int(summary.get('total_violations'))}")
    lines.append(f"- total_fixes: {_safe_int(summary.get('total_fixes'))}")
    lines.append(f"- fix_rate_pct: {_safe_float(summary.get('fix_rate_pct')):.1f}")
    lines.append(f"- open_violations: {_safe_int(summary.get('open_violations'))}")
    lines.append("")

    breakdown = report.get("architecture_breakdown", [])
    if isinstance(breakdown, list) and breakdown:
        lines.append("## Architecture Breakdown")
        lines.append("")
        lines.append("| Layer | Violations | Fixes | Fix Rate % |")
        lines.append("|---|---:|---:|---:|")
        for row in breakdown:
            if not isinstance(row, dict):
                continue
            layer = _safe_str(row.get("layer"), "unknown")
            violations = _safe_int(row.get("violations"))
            fixes = _safe_int(row.get("fixes"))
            fix_rate = _safe_float(row.get("fix_rate_pct"))
            lines.append(f"| {layer} | {violations} | {fixes} | {fix_rate:.1f} |")
        lines.append("")

    trend = report.get("fix_rate_trend", [])
    if isinstance(trend, list) and trend:
        lines.append("## Fix Rate Trend")
        lines.append("")
        lines.append("| Report | Fix Rate % | Violations | Fixes |")
        lines.append("|---|---:|---:|---:|")
        for row in trend:
            if not isinstance(row, dict):
                continue
            label = _safe_str(row.get("label"), "?")
            fix_rate = _safe_float(row.get("fix_rate_pct"))
            violations = _safe_int(row.get("violations"))
            fixes = _safe_int(row.get("fixes"))
            lines.append(f"| {label} | {fix_rate:.1f} | {violations} | {fixes} |")
        lines.append("")

    warnings = report.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    errors = report.get("errors", [])
    if isinstance(errors, list) and errors:
        lines.append("## Errors")
        lines.append("")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    return "\n".join(lines)


def render_ralph_analytics_markdown(reports: list[dict[str, Any]]) -> str:
    """Render aggregated analytics across multiple ralph reports."""
    if not reports:
        return "# Ralph Analytics\n\nNo reports available for analytics.\n"

    lines = [
        "# Ralph Analytics",
        "",
        f"- reports_analyzed: {len(reports)}",
        "",
    ]

    total_violations = 0
    total_fixes = 0
    layer_aggregates: dict[str, dict[str, int]] = {}

    for rpt in reports:
        summary = rpt.get("summary", {})
        if not isinstance(summary, dict):
            continue
        total_violations += _safe_int(summary.get("total_violations"))
        total_fixes += _safe_int(summary.get("total_fixes"))

        breakdown = rpt.get("architecture_breakdown", [])
        if not isinstance(breakdown, list):
            continue
        for row in breakdown:
            if not isinstance(row, dict):
                continue
            layer = _safe_str(row.get("layer"), "unknown")
            if layer not in layer_aggregates:
                layer_aggregates[layer] = {"violations": 0, "fixes": 0}
            layer_aggregates[layer]["violations"] += _safe_int(row.get("violations"))
            layer_aggregates[layer]["fixes"] += _safe_int(row.get("fixes"))

    overall_fix_rate = (total_fixes / total_violations * 100) if total_violations > 0 else 0.0
    lines.append("## Aggregate Summary")
    lines.append("")
    lines.append(f"- total_violations: {total_violations}")
    lines.append(f"- total_fixes: {total_fixes}")
    lines.append(f"- overall_fix_rate_pct: {overall_fix_rate:.1f}")
    lines.append("")

    if layer_aggregates:
        lines.append("## Layer Aggregates")
        lines.append("")
        lines.append("| Layer | Violations | Fixes | Fix Rate % |")
        lines.append("|---|---:|---:|---:|")
        for layer, agg in sorted(layer_aggregates.items()):
            v = agg["violations"]
            f = agg["fixes"]
            rate = (f / v * 100) if v > 0 else 0.0
            lines.append(f"| {layer} | {v} | {f} | {rate:.1f} |")
        lines.append("")

    return "\n".join(lines)
