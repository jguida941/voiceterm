"""Payload and text rendering for findings-priority."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from ..time_utils import utc_timestamp
from .findings_priority_models import AccumulatedFinding, RankedFinding


def build_priority_payload(
    *,
    source_path: Path,
    findings: Sequence[AccumulatedFinding],
    ranked: Sequence[RankedFinding],
    include_resolved: bool,
) -> dict[str, Any]:
    """Render the command payload for machine or markdown output."""
    resolution_counts = _count_by_resolution(findings)
    severity_counts = _count_by_severity(findings)
    return dict(
        command="findings-priority",
        generated_at=utc_timestamp(),
        source_path=str(source_path),
        include_resolved=include_resolved,
        summary=dict(
            parsed_findings=len(findings),
            ranked_findings=len(ranked),
            resolution_counts=resolution_counts,
            severity_counts=severity_counts,
        ),
        ranked_findings=[row.to_dict() for row in ranked],
    )


def render_priority_markdown(payload: dict[str, Any]) -> str:
    """Render a concise markdown view for the ranked findings payload."""
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    ranked = payload.get("ranked_findings") if isinstance(payload, dict) else []
    lines = ["# Findings Priority", ""]
    lines.append(f"- source_path: {payload.get('source_path')}")
    lines.append(f"- include_resolved: {bool(payload.get('include_resolved', False))}")
    lines.append(f"- parsed_findings: {summary.get('parsed_findings', 0)}")
    lines.append(f"- ranked_findings: {summary.get('ranked_findings', 0)}")
    resolution_counts = summary.get("resolution_counts", {})
    lines.append(
        "- resolution_counts: "
        f"open={resolution_counts.get('open', 0)}, "
        f"resolved={resolution_counts.get('resolved', 0)}, "
        f"superseded={resolution_counts.get('superseded', 0)}"
    )
    if not isinstance(ranked, list) or not ranked:
        lines.append("- ranked_findings: none")
        return "\n".join(lines)
    lines.append("")
    lines.append("## Ranked Findings")
    for row in ranked:
        if not isinstance(row, dict):
            continue
        heading = str(row.get("heading") or "").strip()
        primary = str(row.get("primary_file") or "(no source-file match)")
        lines.append(
            f"- [{row.get('severity')}] {row.get('qid')} fan_out={row.get('max_fan_out')} "
            f"primary=`{primary}` :: {heading}"
        )
    return "\n".join(lines)


def render_priority_text(payload: dict[str, Any]) -> str:
    """Render a plain-text variant of the same ranked findings payload."""
    return render_priority_markdown(payload)


def _count_by_resolution(findings: Sequence[AccumulatedFinding]) -> dict[str, int]:
    counts = {state: 0 for state in ("open", "resolved", "superseded")}
    for entry in findings:
        counts[entry.resolution_state] = counts.get(entry.resolution_state, 0) + 1
    return counts


def _count_by_severity(findings: Sequence[AccumulatedFinding]) -> dict[str, int]:
    counts = {severity: 0 for severity in ("critical", "high", "medium", "low", "info")}
    for entry in findings:
        counts[entry.severity] = counts.get(entry.severity, 0) + 1
    return counts


__all__ = [
    "build_priority_payload",
    "render_priority_markdown",
    "render_priority_text",
]
