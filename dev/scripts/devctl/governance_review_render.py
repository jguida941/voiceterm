"""Rendering helpers for governance review summaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_governance_review_markdown(report: dict[str, Any]) -> str:
    """Render one governance review report as markdown."""
    stats = report.get("stats") if isinstance(report.get("stats"), dict) else {}
    lines = ["# devctl governance-review", ""]
    lines.append(f"- log_path: {report.get('log_path')}")
    lines.append(f"- generated_at_utc: {report.get('generated_at_utc')}")
    lines.append(f"- total_rows: {stats.get('total_rows')}")
    lines.append(f"- total_findings: {stats.get('total_findings')}")
    lines.append(f"- false_positive_count: {stats.get('false_positive_count')}")
    lines.append(f"- false_positive_rate_pct: {stats.get('false_positive_rate_pct')}")
    lines.append(f"- positive_finding_count: {stats.get('positive_finding_count')}")
    lines.append(f"- fixed_count: {stats.get('fixed_count')}")
    lines.append(f"- cleanup_rate_pct: {stats.get('cleanup_rate_pct')}")
    lines.append("")
    lines.append("## By Check")
    lines.append("")
    lines.append("| Check | Findings | False Positives | FP % | Fixed | Cleanup % |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in stats.get("by_check_id") or []:
        lines.append(
            "| {bucket} | {total_findings} | {false_positive_count} | "
            "{false_positive_rate_pct} | {fixed_count} | {cleanup_rate_pct} |".format(**row)
        )
    if not stats.get("by_check_id"):
        lines.append("| - | - | - | - | - | - |")
    lines.append("")
    lines.append("## Recent Findings")
    for row in report.get("recent_findings") or []:
        location = row.get("file_path") or "(unknown)"
        if row.get("line") is not None:
            location = f"{location}:{row['line']}"
        verdict = row.get("verdict") or "unknown"
        check_id = row.get("check_id") or "unknown"
        lines.append(f"- `{check_id}` {verdict}: `{location}`")
    if not report.get("recent_findings"):
        lines.append("- none")
    return "\n".join(lines)


def write_governance_review_summary(
    report: dict[str, Any],
    *,
    summary_root: Path,
) -> dict[str, str]:
    """Write latest governance review summary artifacts."""
    summary_root.mkdir(parents=True, exist_ok=True)
    summary_json = summary_root / "review_summary.json"
    summary_md = summary_root / "review_summary.md"
    summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_md.write_text(render_governance_review_markdown(report), encoding="utf-8")
    return {
        "summary_json": str(summary_json),
        "summary_md": str(summary_md),
    }
