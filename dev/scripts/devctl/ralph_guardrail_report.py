"""Build structured guardrail reports for the Ralph AI fix loop.

Produces per-finding status tracking, aggregate analytics, and
markdown/JSON report output for operator review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .time_utils import utc_timestamp

GUARDRAILS_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "dev"
    / "config"
    / "ralph_guardrails.json"
)


def load_guardrails_config(
    path: Path | None = None,
) -> dict[str, Any]:
    """Load the ralph_guardrails.json standards registry."""
    resolved = path or GUARDRAILS_CONFIG_PATH
    if not resolved.exists():
        return {"schema_version": 1, "standards": {}, "fix_skills": {}}
    with open(resolved, encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_standard(
    finding: dict[str, Any],
    standards: dict[str, Any],
) -> dict[str, Any]:
    """Match a finding to its guardrails standard entry."""
    category = str(finding.get("category", "")).lower().strip()
    guard = str(finding.get("guard", "")).lower().strip()
    # Try direct key match on guard name (strip -guard suffix)
    key = guard.removesuffix("-guard") if guard else category
    if key in standards:
        return standards[key]
    # Fallback: scan standards for matching guard_name
    for _std_key, std in standards.items():
        if std.get("guard_name") == guard:
            return std
    return {}


def _build_finding_entry(
    finding: dict[str, Any],
    fix_result: dict[str, Any] | None,
    standards: dict[str, Any],
) -> dict[str, Any]:
    """Build a single finding entry with status and standard refs."""
    standard = _resolve_standard(finding, standards)
    status = "pending"
    fix_skill_used = ""
    if fix_result:
        status = str(fix_result.get("status", "pending"))
        fix_skill_used = str(fix_result.get("fix_skill", ""))
    return {
        "summary": str(finding.get("summary", "")),
        "file": str(finding.get("file", "")),
        "severity": str(finding.get("severity", "unknown")),
        "category": str(finding.get("category", "")),
        "status": status,
        "fix_skill_used": fix_skill_used,
        "probe_guidance_attached": bool(
            (fix_result or {}).get("probe_guidance_attached", False)
        ),
        "guidance_disposition": str(
            (fix_result or {}).get("guidance_disposition", "not_applicable")
        ),
        "guidance_waiver_reason": str(
            (fix_result or {}).get("guidance_waiver_reason", "")
        ),
        "fix_accepted": bool((fix_result or {}).get("fix_accepted", False)),
        "agents_md_section": str(standard.get("agents_md_section", "")),
        "doc_links": standard.get("doc_links", []),
        "standard_description": str(standard.get("description", "")),
    }


def _compute_aggregates(
    entries: list[dict[str, Any]],
    category_to_arch: dict[str, str],
) -> dict[str, Any]:
    """Compute aggregate analytics from processed finding entries."""
    total = len(entries)
    if total == 0:
        return {
            "total": 0,
            "fixed": 0,
            "false_positive": 0,
            "pending": 0,
            "fix_rate_pct": 0.0,
            "false_positive_rate_pct": 0.0,
            "by_architecture": {},
            "by_severity": {},
            "guidance_attached": 0,
            "guidance_used": 0,
            "guidance_waived": 0,
            "guidance_unreported": 0,
            "guidance_fix_accepted": 0,
        }
    fixed = sum(1 for e in entries if e["status"] == "fixed")
    false_pos = sum(1 for e in entries if e["status"] == "false-positive")
    pending = total - fixed - false_pos

    by_arch: dict[str, int] = {}
    for entry in entries:
        arch = category_to_arch.get(entry["category"].lower(), "unknown")
        by_arch[arch] = by_arch.get(arch, 0) + 1

    by_severity: dict[str, int] = {}
    for entry in entries:
        sev = entry["severity"].lower() or "unknown"
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "total": total,
        "fixed": fixed,
        "false_positive": false_pos,
        "pending": pending,
        "fix_rate_pct": round((fixed / total) * 100, 1) if total else 0.0,
        "false_positive_rate_pct": round((false_pos / total) * 100, 1) if total else 0.0,
        "by_architecture": by_arch,
        "by_severity": by_severity,
        "guidance_attached": sum(1 for e in entries if e["probe_guidance_attached"]),
        "guidance_used": sum(1 for e in entries if e["guidance_disposition"] == "used"),
        "guidance_waived": sum(1 for e in entries if e["guidance_disposition"] == "waived"),
        "guidance_unreported": sum(
            1 for e in entries if e["guidance_disposition"] == "unreported"
        ),
        "guidance_fix_accepted": sum(
            1
            for e in entries
            if e["probe_guidance_attached"] and e["fix_accepted"]
        ),
    }


def build_guardrail_report(
    findings: list[dict],
    fix_results: list[dict],
    guardrails_config: dict,
    attempt: int,
    repo: str,
    branch: str,
) -> dict:
    """Build structured guardrail report from findings and fix results."""
    standards = guardrails_config.get("standards", {})
    category_to_arch = guardrails_config.get("category_to_architecture", {})

    # Index fix_results by finding summary for lookup
    fix_index: dict[str, dict] = {}
    for fr in fix_results:
        key = str(fr.get("summary", ""))
        if key:
            fix_index[key] = fr

    entries = []
    for finding in findings:
        summary = str(finding.get("summary", ""))
        fix_result = fix_index.get(summary)
        entry = _build_finding_entry(finding, fix_result, standards)
        entries.append(entry)

    aggregates = _compute_aggregates(entries, category_to_arch)

    return {
        "schema_version": 1,
        "report_type": "ralph-guardrail",
        "generated_at": utc_timestamp(),
        "attempt": attempt,
        "repo": repo,
        "branch": branch,
        "aggregates": aggregates,
        "findings": entries,
    }


def _render_findings_table(entries: list[dict[str, Any]]) -> list[str]:
    """Render the findings detail table as markdown lines."""
    lines = [
        "| # | Severity | Category | Status | Fix Skill | Summary |",
        "|--:|:---------|:---------|:-------|:----------|:--------|",
    ]
    for idx, entry in enumerate(entries, start=1):
        summary = entry["summary"][:80]
        lines.append(
            f"| {idx} "
            f"| {entry['severity']} "
            f"| {entry['category']} "
            f"| {entry['status']} "
            f"| {entry['fix_skill_used'] or '-'} "
            f"| {summary} |"
        )
    return lines


def _render_arch_table(by_arch: dict[str, int]) -> list[str]:
    """Render the architecture breakdown table."""
    lines = [
        "| Architecture | Count |",
        "|:-------------|------:|",
    ]
    for arch in sorted(by_arch):
        lines.append(f"| {arch} | {by_arch[arch]} |")
    return lines


def _render_severity_table(by_severity: dict[str, int]) -> list[str]:
    """Render the severity breakdown table."""
    lines = [
        "| Severity | Count |",
        "|:---------|------:|",
    ]
    for sev in sorted(by_severity):
        lines.append(f"| {sev} | {by_severity[sev]} |")
    return lines


def render_report_markdown(report: dict) -> str:
    """Render guardrail report as markdown with tables."""
    agg = report.get("aggregates", {})
    lines = [
        "# Ralph Guardrail Report",
        "",
        f"- attempt: {report.get('attempt')}",
        f"- repo: {report.get('repo')}",
        f"- branch: {report.get('branch')}",
        f"- generated_at: {report.get('generated_at')}",
        "",
        "## Summary",
        "",
        f"- total findings: {agg.get('total', 0)}",
        f"- fixed: {agg.get('fixed', 0)}",
        f"- false positives: {agg.get('false_positive', 0)}",
        f"- pending: {agg.get('pending', 0)}",
        f"- fix rate: {agg.get('fix_rate_pct', 0.0)}%",
        f"- false positive rate: {agg.get('false_positive_rate_pct', 0.0)}%",
        f"- guidance attached: {agg.get('guidance_attached', 0)}",
        f"- guidance used: {agg.get('guidance_used', 0)}",
        f"- guidance waived: {agg.get('guidance_waived', 0)}",
        f"- guidance unreported: {agg.get('guidance_unreported', 0)}",
        f"- guidance fix accepted: {agg.get('guidance_fix_accepted', 0)}",
        "",
    ]

    by_arch = agg.get("by_architecture", {})
    if by_arch:
        lines.append("## By Architecture")
        lines.append("")
        lines.extend(_render_arch_table(by_arch))
        lines.append("")

    by_severity = agg.get("by_severity", {})
    if by_severity:
        lines.append("## By Severity")
        lines.append("")
        lines.extend(_render_severity_table(by_severity))
        lines.append("")

    entries = report.get("findings", [])
    if entries:
        lines.append("## Findings Detail")
        lines.append("")
        lines.extend(_render_findings_table(entries))
        lines.append("")

    return "\n".join(lines)


def render_report_json(report: dict) -> str:
    """Render guardrail report as formatted JSON."""
    return json.dumps(report, indent=2)
