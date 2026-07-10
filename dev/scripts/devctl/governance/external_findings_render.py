"""Rendering helpers for imported external-finding summaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_external_finding_markdown(report: dict[str, Any]) -> str:
    """Render one imported external-finding report as markdown."""
    stats = report.get("stats") if isinstance(report.get("stats"), dict) else {}
    repo_rows = stats.get("by_repo") if isinstance(stats.get("by_repo"), list) else []
    check_rows = (
        stats.get("by_check_id") if isinstance(stats.get("by_check_id"), list) else []
    )

    lines = ["# devctl governance-import-findings", ""]
    lines.append(f"- log_path: {report.get('log_path')}")
    lines.append(f"- governance_review_log: {report.get('governance_review_log')}")
    lines.append(f"- generated_at_utc: {report.get('generated_at_utc')}")
    if report.get("input_path"):
        lines.append(f"- input_path: {report.get('input_path')}")
    if report.get("import_run_id"):
        lines.append(f"- import_run_id: {report.get('import_run_id')}")
    if report.get("imported_count") is not None:
        lines.append(f"- imported_count: {report.get('imported_count')}")
    lines.append(f"- total_rows: {stats.get('total_rows')}")
    lines.append(f"- total_findings: {stats.get('total_findings')}")
    lines.append(f"- unique_repo_count: {stats.get('unique_repo_count')}")
    lines.append(f"- unique_import_run_count: {stats.get('unique_import_run_count')}")
    lines.append(f"- reviewed_count: {stats.get('reviewed_count')}")
    lines.append(
        f"- adjudication_coverage_pct: {stats.get('adjudication_coverage_pct')}"
    )
    lines.append(f"- false_positive_count: {stats.get('false_positive_count')}")
    lines.append(f"- fixed_count: {stats.get('fixed_count')}")
    lines.append(f"- confirmed_issue_count: {stats.get('confirmed_issue_count')}")
    lines.append("")
    lines.append("## By Repo")
    lines.append("")
    lines.append("| Repo | Findings | Reviewed | Coverage % | False Positives | Fixed |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in repo_rows:
        lines.append(
            "| {bucket} | {total_findings} | {reviewed_count} | "
            "{adjudication_coverage_pct} | {false_positive_count} | "
            "{fixed_count} |".format(**row)
        )
    if not repo_rows:
        lines.append("| - | - | - | - | - | - |")

    lines.append("")
    lines.append("## By Check")
    lines.append("")
    lines.append("| Check | Findings | Reviewed | Coverage % | False Positives | Fixed |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in check_rows:
        lines.append(
            "| {bucket} | {total_findings} | {reviewed_count} | "
            "{adjudication_coverage_pct} | {false_positive_count} | "
            "{fixed_count} |".format(**row)
        )
    if not check_rows:
        lines.append("| - | - | - | - | - | - |")

    lines.append("")
    lines.append("## Recent Findings")
    for row in report.get("recent_findings") or []:
        location = row.get("file_path") or "(unknown)"
        if row.get("line") is not None:
            location = f"{location}:{row['line']}"
        repo_name = row.get("repo_name") or "unknown"
        check_id = row.get("check_id") or "unknown"
        title = row.get("title") or row.get("summary") or "(untitled)"
        lines.append(f"- `{repo_name}` `{check_id}` `{location}` {title}")
    if not report.get("recent_findings"):
        lines.append("- none")
    return "\n".join(lines)


def write_external_finding_summary(
    report: dict[str, Any],
    *,
    summary_root: Path,
) -> dict[str, str]:
    """Write latest imported external-finding summary artifacts."""
    summary_root.mkdir(parents=True, exist_ok=True)
    summary_json = summary_root / "external_findings_summary.json"
    summary_md = summary_root / "external_findings_summary.md"
    summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_md.write_text(
        render_external_finding_markdown(report),
        encoding="utf-8",
    )
    return {
        "summary_json": str(summary_json),
        "summary_md": str(summary_md),
    }
