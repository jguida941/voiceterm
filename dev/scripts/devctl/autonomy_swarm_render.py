"""Markdown renderer for `devctl autonomy-swarm` reports."""

from __future__ import annotations

from typing import Any


def render_swarm_markdown(report: dict[str, Any]) -> str:
    lines = ["# Autonomy Swarm Report", ""]
    lines.append(f"- generated_at: {report.get('timestamp')}")
    lines.append(f"- run_label: {report.get('run_label')}")
    lines.append(f"- ok: {report.get('ok')}")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines.append(f"- requested_agents: {summary.get('requested_agents')}")
    lines.append(f"- selected_agents: {summary.get('selected_agents')}")
    lines.append(f"- worker_agents: {summary.get('worker_agents')}")
    lines.append(f"- reviewer_lane: {summary.get('reviewer_lane')}")
    lines.append(f"- ok_count: {summary.get('ok_count')}")
    lines.append(f"- resolved_count: {summary.get('resolved_count')}")
    post_audit = (
        report.get("post_audit") if isinstance(report.get("post_audit"), dict) else {}
    )
    if post_audit:
        lines.append(f"- post_audit_enabled: {post_audit.get('enabled')}")
        lines.append(f"- post_audit_ok: {post_audit.get('ok')}")

    metadata = (
        report.get("metadata") if isinstance(report.get("metadata"), dict) else {}
    )
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- files_changed: {metadata.get('files_changed')}")
    lines.append(f"- lines_changed: {metadata.get('lines_changed')}")
    lines.append(f"- prompt_tokens: {metadata.get('prompt_tokens')}")
    lines.append(
        f"- difficulty_hits: {', '.join(metadata.get('difficulty_hits', [])) or 'none'}"
    )

    rationale = (
        report.get("allocation_rationale")
        if isinstance(report.get("allocation_rationale"), list)
        else []
    )
    if rationale:
        lines.append("")
        lines.append("## Allocation Rationale")
        for row in rationale:
            lines.append(f"- {row}")

    lines.append("")
    lines.append("## Agents")
    lines.append("")
    lines.append("| Agent | rc | ok | resolved | reason | report |")
    lines.append("|---|---:|---|---|---|---|")
    agents = report.get("agents") if isinstance(report.get("agents"), list) else []
    for row in agents:
        if not isinstance(row, dict):
            continue
        lines.append(
            f"| `{row.get('agent')}` | {row.get('returncode')} | {row.get('ok')} | {row.get('resolved')} | "
            f"`{row.get('reason')}` | `{row.get('report_json')}` |"
        )

    if post_audit:
        lines.append("")
        lines.append("## Post Audit")
        lines.append(f"- run_label: {post_audit.get('run_label')}")
        lines.append(f"- bundle_dir: `{post_audit.get('bundle_dir')}`")
        lines.append(f"- summary_json: `{post_audit.get('summary_json')}`")
        lines.append(f"- summary_md: `{post_audit.get('summary_md')}`")

    charts = report.get("charts") if isinstance(report.get("charts"), list) else []
    if charts:
        lines.append("")
        lines.append("## Charts")
        for chart in charts:
            lines.append(f"- `{chart}`")

    warnings = (
        report.get("warnings") if isinstance(report.get("warnings"), list) else []
    )
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        for row in warnings:
            lines.append(f"- {row}")

    return "\n".join(lines)
