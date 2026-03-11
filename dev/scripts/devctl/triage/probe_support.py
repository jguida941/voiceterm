"""Review-probe classification helpers for `devctl triage`."""

from __future__ import annotations

from typing import Any

PROBE_SOURCE = "devctl.status.probe_report"
PROBE_INFRA_SOURCE = f"{PROBE_SOURCE}.infra"


def _count_bucket_value(bucket: Any, key: str) -> int:
    if not isinstance(bucket, dict):
        return 0
    raw_value = bucket.get(key)
    if not isinstance(raw_value, (int, float)):
        return 0
    return int(raw_value)


def _format_probe_hotspot(summary: dict[str, Any]) -> str | None:
    priority_hotspots = summary.get("priority_hotspots")
    if isinstance(priority_hotspots, list) and priority_hotspots:
        first = priority_hotspots[0]
        if isinstance(first, dict):
            file_path = str(first.get("file") or "").strip()
            score = _count_bucket_value(first, "priority_score")
            hint_count = _count_bucket_value(first, "hint_count")
            if file_path:
                if score > 0:
                    return f"{file_path} (score={score}, hints={hint_count})"
                if hint_count > 0:
                    return f"{file_path} ({hint_count} hints)"
                return file_path
    top_files = summary.get("top_files")
    if not isinstance(top_files, list) or not top_files:
        return None
    first = top_files[0]
    if not isinstance(first, dict):
        return None
    file_path = str(first.get("file") or "").strip()
    hint_count = _count_bucket_value(first, "hint_count")
    if not file_path:
        return None
    if hint_count > 0:
        return f"{file_path} ({hint_count} hints)"
    return file_path


def classify_probe_report_issues(probe_report: object) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if probe_report is None:
        return issues
    if not isinstance(probe_report, dict):
        issues.append(
            {
                "category": "infra",
                "severity": "medium",
                "source": PROBE_INFRA_SOURCE,
                "summary": "Review probe summary unavailable: unexpected payload.",
            }
        )
        return issues
    if "error" in probe_report:
        issues.append(
            {
                "category": "infra",
                "severity": "medium",
                "source": PROBE_INFRA_SOURCE,
                "summary": f"Review probe summary unavailable: {probe_report['error']}",
            }
        )
        return issues

    errors = probe_report.get("errors")
    if isinstance(errors, list) and errors:
        issues.append(
            {
                "category": "infra",
                "severity": "medium",
                "source": PROBE_INFRA_SOURCE,
                "summary": f"Review probe run incomplete: {len(errors)} probe error(s).",
            }
        )

    summary = probe_report.get("summary")
    if not isinstance(summary, dict):
        return issues
    risk_hints = _count_bucket_value(summary, "risk_hints")
    if risk_hints <= 0:
        return issues

    files_with_hints = _count_bucket_value(summary, "files_with_hints")
    hints_by_severity = summary.get("hints_by_severity")
    high_count = _count_bucket_value(hints_by_severity, "high")
    medium_count = _count_bucket_value(hints_by_severity, "medium")
    low_count = _count_bucket_value(hints_by_severity, "low")
    severity = "high" if high_count > 0 else ("medium" if medium_count > 0 else "low")

    summary_text = (
        f"Review probes flagged {risk_hints} risk hints across "
        f"{files_with_hints} file(s)."
    )
    counts = [
        f"high={high_count}" if high_count > 0 else "",
        f"medium={medium_count}" if medium_count > 0 else "",
        f"low={low_count}" if low_count > 0 else "",
    ]
    formatted_counts = ", ".join(part for part in counts if part)
    if formatted_counts:
        summary_text = f"{summary_text[:-1]} ({formatted_counts})."
    hotspot = _format_probe_hotspot(summary)
    if hotspot:
        summary_text += f" Top hotspot: {hotspot}."

    issues.append(
        {
            "category": "quality",
            "severity": severity,
            "source": PROBE_SOURCE,
            "summary": summary_text,
        }
    )
    return issues


def issues_include_probe_signal(sources: set[str]) -> bool:
    return any(
        source == PROBE_SOURCE or source.startswith(PROBE_INFRA_SOURCE)
        for source in sources
    )
