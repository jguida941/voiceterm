"""Rendering and artifact helpers for dogfood coverage reports."""

from __future__ import annotations

import json
from pathlib import Path

from .dogfood_models import DogfoodReport


def render_dogfood_markdown(report: DogfoodReport) -> str:
    """Render one dogfood report as compact markdown."""
    lines = [
        "# devctl dogfood",
        "",
        f"- generated_at_utc: {report.generated_at_utc}",
        f"- log_path: {report.log_path}",
        f"- total_rows: {report.total_rows}",
    ]
    if report.latest_recorded_at_utc:
        lines.append(f"- latest_recorded_at_utc: {report.latest_recorded_at_utc}")
    lines.extend(["", "## Coverage", ""])
    lines.append("| Target | Covered | Catalog | Coverage % | Passed | Failed | Blocked | Skipped |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for bucket in report.coverage:
        lines.append(
            f"| {bucket.target_kind} | {bucket.covered_total} | {bucket.catalog_total} | "
            f"{bucket.coverage_pct:.2f} | {bucket.passed_total} | {bucket.failed_total} | "
            f"{bucket.blocked_total} | {bucket.skipped_total} |"
        )
    lines.extend(["", "## Remaining Coverage", ""])
    for bucket in report.coverage:
        preview = ", ".join(bucket.uncovered_ids[:8]) if bucket.uncovered_ids else "none"
        lines.append(f"- `{bucket.target_kind}` uncovered ({len(bucket.uncovered_ids)}): {preview}")
    lines.extend(["", "## Governance Findings", ""])
    governance = report.governance_summary
    lines.append(
        f"- dogfood findings: total={governance.total_findings}, open={governance.open_findings}, fixed={governance.fixed_findings}"
    )
    if governance.recent_findings:
        lines.append("")
        lines.append("### Recent Dogfood Findings")
        lines.append("")
        for finding in governance.recent_findings[:5]:
            summary = str(finding.get("check_id") or finding.get("finding_id") or "dogfood")
            verdict = str(finding.get("verdict") or "unknown")
            file_path = str(finding.get("file_path") or "").strip()
            detail = f" -> `{file_path}`" if file_path else ""
            lines.append(f"- `{summary}` [{verdict}]{detail}")
    lines.extend(["", "## Recent Records", ""])
    if not report.recent_records:
        lines.append("- No dogfood rows recorded yet.")
    else:
        for record in report.recent_records:
            actor = f" actor={record.actor}" if record.actor else ""
            provider = f" provider={record.provider}" if record.provider else ""
            lines.append(
                f"- `{record.timestamp_utc}` `{record.target_kind}:{record.target_id}` "
                f"status={record.status}{actor}{provider}"
            )
    return "\n".join(lines)


def write_dogfood_summary(
    report: DogfoodReport,
    *,
    summary_root: Path,
) -> dict[str, str]:
    """Persist JSON and markdown summary artifacts for the current report."""
    summary_root.mkdir(parents=True, exist_ok=True)
    summary_json = summary_root / "summary.json"
    summary_md = summary_root / "summary.md"
    summary_json.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    summary_md.write_text(
        render_dogfood_markdown(report),
        encoding="utf-8",
    )
    return {
        "summary_json": str(summary_json),
        "summary_md": str(summary_md),
    }
