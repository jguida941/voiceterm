"""devctl ralph-status command implementation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..common import emit_output, pipe_output, write_output
from ..config import REPO_ROOT
from ..data_science.rendering import _write_bar_chart_svg
from ..ralph_status_views import (
    _safe_int,
    render_ralph_analytics_markdown,
    render_ralph_status_markdown,
)


_DEFAULT_REPORT_DIR = "dev/reports/ralph"


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _load_ralph_reports(report_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Load all ralph-report.json files from the given directory."""
    errors: list[str] = []
    reports: list[dict[str, Any]] = []

    if not report_dir.exists():
        return [], [f"report directory not found: {report_dir}"]
    if not report_dir.is_dir():
        return [], [f"report path is not a directory: {report_dir}"]

    json_files = sorted(report_dir.glob("ralph-report*.json"))
    if not json_files:
        json_files = sorted(report_dir.glob("*.json"))

    for fpath in json_files:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"failed to load {fpath.name}: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"expected object in {fpath.name}, got {type(data).__name__}")
            continue
        data.setdefault("_source_file", str(fpath))
        reports.append(data)

    return reports, errors


def _aggregate_reports(
    reports: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Build an aggregated summary from multiple ralph reports.

    Returns (summary_dict, architecture_breakdown, fix_rate_trend).
    """
    total_violations = 0
    total_fixes = 0
    layer_aggregates: dict[str, dict[str, int]] = {}
    fix_rate_trend: list[dict[str, Any]] = []

    for rpt in reports:
        summary = rpt.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}

        v = _safe_int(summary.get("total_violations"))
        f = _safe_int(summary.get("total_fixes"))
        total_violations += v
        total_fixes += f

        label = rpt.get("label") or rpt.get("_source_file", "?")
        fix_rate = (f / v * 100) if v > 0 else 0.0
        fix_rate_trend.append({
            "label": str(label),
            "fix_rate_pct": fix_rate,
            "violations": v,
            "fixes": f,
        })

        breakdown = rpt.get("architecture_breakdown", [])
        if not isinstance(breakdown, list):
            continue
        for row in breakdown:
            if not isinstance(row, dict):
                continue
            layer = str(row.get("layer") or "unknown").strip()
            if layer not in layer_aggregates:
                layer_aggregates[layer] = {"violations": 0, "fixes": 0}
            layer_aggregates[layer]["violations"] += _safe_int(row.get("violations"))
            layer_aggregates[layer]["fixes"] += _safe_int(row.get("fixes"))

    overall_fix_rate = (total_fixes / total_violations * 100) if total_violations > 0 else 0.0

    arch_breakdown = []
    for layer, agg in sorted(layer_aggregates.items()):
        lv = agg["violations"]
        lf = agg["fixes"]
        rate = (lf / lv * 100) if lv > 0 else 0.0
        arch_breakdown.append({
            "layer": layer,
            "violations": lv,
            "fixes": lf,
            "fix_rate_pct": rate,
        })

    return {
        "total_violations": total_violations,
        "total_fixes": total_fixes,
        "fix_rate_pct": overall_fix_rate,
        "open_violations": total_violations - total_fixes,
    }, arch_breakdown, fix_rate_trend


def _write_charts(
    *,
    arch_breakdown: list[dict[str, Any]],
    fix_rate_trend: list[dict[str, Any]],
    charts_dir: Path,
) -> list[str]:
    """Generate SVG charts for ralph analytics. Returns list of chart paths."""
    charts_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    if arch_breakdown:
        _write_bar_chart_svg(
            title="Violations by Architecture Layer",
            labels=[str(row.get("layer")) for row in arch_breakdown],
            values=[float(row.get("violations", 0)) for row in arch_breakdown],
            output_path=charts_dir / "ralph_violations_by_layer.svg",
            color="#e15759",
        )
        written.append(str(charts_dir / "ralph_violations_by_layer.svg"))

        _write_bar_chart_svg(
            title="Fix Rate by Architecture Layer",
            labels=[str(row.get("layer")) for row in arch_breakdown],
            values=[float(row.get("fix_rate_pct", 0)) for row in arch_breakdown],
            output_path=charts_dir / "ralph_fix_rate_by_layer.svg",
            color="#59a14f",
        )
        written.append(str(charts_dir / "ralph_fix_rate_by_layer.svg"))

    if fix_rate_trend:
        _write_bar_chart_svg(
            title="Fix Rate Trend Across Reports",
            labels=[str(row.get("label", "?"))[:20] for row in fix_rate_trend],
            values=[float(row.get("fix_rate_pct", 0)) for row in fix_rate_trend],
            output_path=charts_dir / "ralph_fix_rate_trend.svg",
            color="#4e79a7",
        )
        written.append(str(charts_dir / "ralph_fix_rate_trend.svg"))

    return written


def run(args) -> int:
    """Render Ralph guardrail loop analytics from report artifacts."""
    warnings: list[str] = []
    errors: list[str] = []

    report_dir_raw = args.report_dir or _DEFAULT_REPORT_DIR
    report_dir = _resolve_path(report_dir_raw)

    reports, load_errors = _load_ralph_reports(report_dir)
    errors.extend(load_errors)

    if not reports and not errors:
        warnings.append(f"no ralph reports found in {report_dir}")

    summary: dict[str, Any] = {}
    arch_breakdown: list[dict[str, Any]] = []
    fix_rate_trend: list[dict[str, Any]] = []

    if reports:
        summary, arch_breakdown, fix_rate_trend = _aggregate_reports(reports)

    chart_paths: list[str] = []
    if args.with_charts and reports:
        output_root = _resolve_path(args.output_root or "dev/reports/ralph")
        charts_dir = output_root / "charts"
        chart_paths = _write_charts(
            arch_breakdown=arch_breakdown,
            fix_rate_trend=fix_rate_trend,
            charts_dir=charts_dir,
        )

    report = {
        "command": "ralph-status",
        "generated_at": _iso_z(datetime.now(timezone.utc)),
        "ok": not errors,
        "report_dir": str(report_dir),
        "report_count": len(reports),
        "summary": summary,
        "architecture_breakdown": arch_breakdown,
        "fix_rate_trend": fix_rate_trend,
        "chart_paths": chart_paths,
        "warnings": warnings,
        "errors": errors,
    }

    json_payload = json.dumps(report, indent=2)
    output = json_payload if args.format == "json" else render_ralph_status_markdown(report)

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
    return 0 if report["ok"] else 1
