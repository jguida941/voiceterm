#!/usr/bin/env python3
"""Analyze audit execution events and emit automation/AI assistance metrics."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOURCE_BUCKETS = ("script_only", "ai_assisted", "human_manual", "other")


@dataclass
class AuditEvent:
    """Normalized event row used for metric calculations."""

    timestamp: str
    cycle_id: str
    area: str
    step: str
    source_bucket: str
    automated: bool
    success: bool
    duration_seconds: float | None
    retries: int
    manual_reason: str | None
    repeated_workaround: bool


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _normalize_source_bucket(payload: dict[str, Any]) -> str:
    raw = str(payload.get("execution_source") or "").strip().lower()
    if raw in SOURCE_BUCKETS:
        return raw

    automated = bool(payload.get("automated", False))
    actor = str(payload.get("actor") or "").strip().lower()
    if automated and actor == "script":
        return "script_only"
    if automated and actor in {"ai", "assistant", "hybrid"}:
        return "ai_assisted"
    if not automated:
        return "human_manual"
    return "other"


def _load_events(path: Path) -> tuple[list[AuditEvent], list[str]]:
    events: list[AuditEvent] = []
    warnings: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"line {line_number}: invalid JSON ({exc})")
            continue
        if not isinstance(payload, dict):
            warnings.append(f"line {line_number}: expected object")
            continue

        events.append(
            AuditEvent(
                timestamp=str(payload.get("timestamp") or ""),
                cycle_id=str(payload.get("cycle_id") or "unknown"),
                area=str(payload.get("area") or "unspecified"),
                step=str(payload.get("step") or "unspecified"),
                source_bucket=_normalize_source_bucket(payload),
                automated=bool(payload.get("automated", False)),
                success=bool(payload.get("success", False)),
                duration_seconds=_safe_float(payload.get("duration_seconds")),
                retries=_safe_int(payload.get("retries"), default=0),
                manual_reason=(
                    str(payload.get("manual_reason")).strip()
                    if payload.get("manual_reason") is not None
                    else None
                ),
                repeated_workaround=bool(payload.get("repeated_workaround", False)),
            )
        )
    return events, warnings


def _pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _summarize(events: list[AuditEvent]) -> dict[str, Any]:
    total = len(events)
    source_counts = Counter(event.source_bucket for event in events)
    success_count = sum(1 for event in events if event.success)
    automated_count = sum(1 for event in events if event.automated)
    repeated_count = sum(1 for event in events if event.repeated_workaround)
    retry_sum = sum(event.retries for event in events)
    durations = [event.duration_seconds for event in events if event.duration_seconds is not None]
    manual_reason_counts = Counter(
        event.manual_reason for event in events if event.manual_reason and event.source_bucket == "human_manual"
    )

    area_totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "total": 0,
            "success": 0,
            "automated": 0,
            "source_counts": Counter(),
            "duration_seconds": [],
        }
    )
    for event in events:
        bucket = area_totals[event.area]
        bucket["total"] += 1
        bucket["success"] += 1 if event.success else 0
        bucket["automated"] += 1 if event.automated else 0
        bucket["source_counts"][event.source_bucket] += 1
        if event.duration_seconds is not None:
            bucket["duration_seconds"].append(event.duration_seconds)

    areas = []
    for area_name in sorted(area_totals.keys()):
        payload = area_totals[area_name]
        area_total = int(payload["total"])
        avg_duration = None
        if payload["duration_seconds"]:
            avg_duration = round(statistics.mean(payload["duration_seconds"]), 2)
        areas.append(
            {
                "area": area_name,
                "total": area_total,
                "success_rate_pct": _pct(int(payload["success"]), area_total),
                "automation_coverage_pct": _pct(int(payload["automated"]), area_total),
                "avg_duration_seconds": avg_duration,
                "source_counts": dict(payload["source_counts"]),
            }
        )

    return {
        "total_events": total,
        "automation_coverage_pct": _pct(automated_count, total),
        "script_only_pct": _pct(source_counts.get("script_only", 0), total),
        "ai_assisted_pct": _pct(source_counts.get("ai_assisted", 0), total),
        "human_manual_pct": _pct(source_counts.get("human_manual", 0), total),
        "success_rate_pct": _pct(success_count, total),
        "repeated_workaround_pct": _pct(repeated_count, total),
        "source_counts": dict(source_counts),
        "retry_total": retry_sum,
        "avg_duration_seconds": round(statistics.mean(durations), 2) if durations else None,
        "median_duration_seconds": round(statistics.median(durations), 2) if durations else None,
        "manual_reasons": dict(manual_reason_counts),
        "areas": areas,
    }


def _render_md(summary: dict[str, Any], *, input_path: Path, warnings: list[str], chart_paths: list[Path]) -> str:
    lines = ["# Audit Metrics Summary", ""]
    lines.append(f"- input: `{input_path}`")
    lines.append(f"- total_events: {summary['total_events']}")
    lines.append(f"- automation_coverage_pct: {summary['automation_coverage_pct']}")
    lines.append(f"- script_only_pct: {summary['script_only_pct']}")
    lines.append(f"- ai_assisted_pct: {summary['ai_assisted_pct']}")
    lines.append(f"- human_manual_pct: {summary['human_manual_pct']}")
    lines.append(f"- success_rate_pct: {summary['success_rate_pct']}")
    lines.append(f"- repeated_workaround_pct: {summary['repeated_workaround_pct']}")
    lines.append(f"- retry_total: {summary['retry_total']}")
    lines.append(f"- avg_duration_seconds: {summary['avg_duration_seconds']}")
    lines.append(f"- median_duration_seconds: {summary['median_duration_seconds']}")
    lines.append("")
    lines.append("## Source Breakdown")
    lines.append("")
    lines.append("| Source | Count |")
    lines.append("|---|---:|")
    for source in SOURCE_BUCKETS:
        lines.append(f"| `{source}` | {summary['source_counts'].get(source, 0)} |")
    lines.append("")
    lines.append("## Area Breakdown")
    lines.append("")
    lines.append("| Area | Total | Success % | Automation % | Avg duration (s) |")
    lines.append("|---|---:|---:|---:|---:|")
    for area in summary["areas"]:
        avg_duration = "-" if area["avg_duration_seconds"] is None else area["avg_duration_seconds"]
        lines.append(
            f"| `{area['area']}` | {area['total']} | {area['success_rate_pct']} | "
            f"{area['automation_coverage_pct']} | {avg_duration} |"
        )
    if summary["manual_reasons"]:
        lines.append("")
        lines.append("## Manual Reason Counts")
        lines.append("")
        lines.append("| Reason | Count |")
        lines.append("|---|---:|")
        for reason, count in sorted(summary["manual_reasons"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| `{reason}` | {count} |")
    if chart_paths:
        lines.append("")
        lines.append("## Charts")
        for chart_path in chart_paths:
            lines.append(f"- `{chart_path}`")
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines)


def _maybe_write(path: Path | None, content: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_charts(events: list[AuditEvent], output_dir: Path) -> tuple[list[Path], str | None]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency path
        return [], f"matplotlib unavailable: {exc}"

    output_dir.mkdir(parents=True, exist_ok=True)
    chart_paths: list[Path] = []

    source_counts = Counter(event.source_bucket for event in events)
    source_chart = output_dir / "source_breakdown.png"
    sources = list(SOURCE_BUCKETS)
    counts = [source_counts.get(item, 0) for item in sources]
    figure = plt.figure(figsize=(8, 4.5))
    ax = figure.add_subplot(111)
    ax.bar(sources, counts, color=["#1f77b4", "#ff7f0e", "#2ca02c", "#7f7f7f"])
    ax.set_title("Execution Source Breakdown")
    ax.set_ylabel("Count")
    figure.tight_layout()
    figure.savefig(source_chart, dpi=150)
    plt.close(figure)
    chart_paths.append(source_chart)

    area_source = defaultdict(Counter)
    for event in events:
        area_source[event.area][event.source_bucket] += 1
    areas = sorted(area_source.keys())
    if areas:
        stacked_chart = output_dir / "area_source_breakdown.png"
        figure = plt.figure(figsize=(10, 5))
        ax = figure.add_subplot(111)
        positions = list(range(len(areas)))
        bottoms = [0] * len(areas)
        for source in SOURCE_BUCKETS:
            series = [area_source[area].get(source, 0) for area in areas]
            ax.bar(positions, series, bottom=bottoms, label=source)
            bottoms = [left + right for left, right in zip(bottoms, series)]
        ax.set_title("Area vs Execution Source")
        ax.set_ylabel("Count")
        ax.set_xticks(positions, areas, rotation=25, ha="right")
        ax.legend()
        figure.tight_layout()
        figure.savefig(stacked_chart, dpi=150)
        plt.close(figure)
        chart_paths.append(stacked_chart)

    trend_chart = output_dir / "automation_coverage_trend.png"
    sorted_events = sorted(events, key=lambda item: item.timestamp or "")
    running_coverage = []
    automated_so_far = 0
    for index, event in enumerate(sorted_events, start=1):
        if event.automated:
            automated_so_far += 1
        running_coverage.append((index, (automated_so_far / index) * 100.0))
    figure = plt.figure(figsize=(8, 4.5))
    ax = figure.add_subplot(111)
    ax.plot([item[0] for item in running_coverage], [item[1] for item in running_coverage], marker="o")
    ax.set_title("Cumulative Automation Coverage")
    ax.set_xlabel("Event index")
    ax.set_ylabel("Automation coverage (%)")
    ax.set_ylim(0, 100)
    figure.tight_layout()
    figure.savefig(trend_chart, dpi=150)
    plt.close(figure)
    chart_paths.append(trend_chart)

    return chart_paths, None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to audit events JSONL file")
    parser.add_argument("--output-md", help="Optional markdown summary output path")
    parser.add_argument("--output-json", help="Optional JSON summary output path")
    parser.add_argument(
        "--chart-dir",
        help="Optional chart output directory. If provided, charts are generated when matplotlib is available.",
    )
    parser.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="Return non-zero when the input has no valid events.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2

    events, warnings = _load_events(input_path)
    if not events and args.fail_on_empty:
        print("error: no valid events found in input", file=sys.stderr)
        return 3

    summary = _summarize(events)
    chart_paths: list[Path] = []
    if args.chart_dir and events:
        paths, chart_warning = _build_charts(events, Path(args.chart_dir).expanduser())
        chart_paths.extend(paths)
        if chart_warning:
            warnings.append(chart_warning)

    md_output = _render_md(
        summary,
        input_path=input_path,
        warnings=warnings,
        chart_paths=chart_paths,
    )
    print(md_output)

    if args.output_md:
        _maybe_write(Path(args.output_md).expanduser(), md_output)
    if args.output_json:
        output_payload = {
            "input": str(input_path),
            "summary": summary,
            "warnings": warnings,
            "charts": [str(path) for path in chart_paths],
        }
        _maybe_write(
            Path(args.output_json).expanduser(),
            json.dumps(output_payload, indent=2),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
