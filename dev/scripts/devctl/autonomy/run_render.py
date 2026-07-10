"""Markdown rendering for `devctl swarm_run` reports."""

from __future__ import annotations

from typing import Any


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Autonomy Run Report", ""]
    lines.append(f"- generated_at: {report.get('timestamp')}")
    lines.append(f"- run_label: {report.get('run_label')}")
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- plan_doc: {report.get('plan_doc')}")
    lines.append(f"- mp_scope: {report.get('mp_scope')}")
    continuous = report.get("continuous", {})
    if isinstance(continuous, dict):
        lines.append(f"- continuous: {continuous.get('enabled')}")
        lines.append(f"- cycles_completed: {continuous.get('cycles_completed')}")
        lines.append(f"- stop_reason: {continuous.get('stop_reason')}")
    feedback = report.get("feedback_sizing", {})
    if isinstance(feedback, dict):
        lines.append(f"- feedback_sizing: {feedback.get('enabled')}")
        lines.append(f"- feedback_next_agents: {feedback.get('next_agents')}")
    lines.append(f"- swarm_ok: {report.get('swarm', {}).get('ok')}")
    lines.append(f"- governance_ok: {report.get('governance', {}).get('ok')}")
    lines.append(f"- plan_update_ok: {report.get('plan_update', {}).get('ok')}")
    lines.append("")
    lines.append("## Next Steps")
    for row in report.get("next_steps", []) or ["none"]:
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## Swarm")
    swarm = report.get("swarm", {})
    lines.append(f"- summary_json: `{swarm.get('summary_json')}`")
    lines.append(f"- summary_md: `{swarm.get('summary_md')}`")
    summary = swarm.get("summary", {}) if isinstance(swarm.get("summary"), dict) else {}
    lines.append(f"- selected_agents: {summary.get('selected_agents')}")
    lines.append(f"- worker_agents: {summary.get('worker_agents')}")
    lines.append(f"- reviewer_lane: {summary.get('reviewer_lane')}")
    cycle_rows = report.get("cycles")
    if isinstance(cycle_rows, list) and cycle_rows:
        lines.append("")
        lines.append("## Cycles")
        for row in cycle_rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- "
                + f"#{row.get('index')} "
                + f"label={row.get('run_label')} "
                + f"ok={row.get('ok')} "
                + f"swarm_ok={row.get('swarm_ok')} "
                + f"governance_ok={row.get('governance_ok')} "
                + f"plan_update_ok={row.get('plan_update_ok')} "
                + f"feedback={row.get('feedback_decision')} "
                + f"next_agents={row.get('feedback_next_agents')}"
            )
    lines.append("")
    lines.append("## Governance")
    lines.append("| Step | rc | ok |")
    lines.append("|---|---:|---|")
    for row in report.get("governance", {}).get("steps", []):
        lines.append(
            f"| `{row.get('name')}` | {row.get('returncode')} | {row.get('ok')} |"
        )
    warnings = report.get("warnings") or []
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        for row in warnings:
            lines.append(f"- {row}")
    errors = report.get("errors") or []
    if errors:
        lines.append("")
        lines.append("## Errors")
        for row in errors:
            lines.append(f"- {row}")
    return "\n".join(lines)
