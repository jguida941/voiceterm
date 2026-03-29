"""Markdown rendering helpers for check-router output."""

from __future__ import annotations

from .check_router_support import sample_paths


def render_markdown(report: dict) -> str:
    lines = ["# devctl check-router", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- lane: {report['lane']}")
    lines.append(f"- bundle: {report['bundle']}")
    lines.append(f"- commit_range: {report['since_ref']}...{report['head_ref']}")
    lines.append(f"- changed_paths: {len(report['changed_paths'])}")
    lines.append(f"- execute: {report['execute']}")
    lines.append(f"- risk_addons: {len(report['risk_addons'])}")
    lines.append(f"- planned_commands: {len(report['planned_commands'])}")
    if report.get("error"):
        lines.append(f"- error: {report['error']}")

    if report["reasons"]:
        lines.append("")
        lines.append("## Why This Lane")
        for reason in report["reasons"]:
            lines.append(f"- {reason}")
    rule_summary = str(report.get("rule_summary") or "").strip()
    if rule_summary:
        lines.append("")
        lines.append("## Rule Summary")
        lines.append(f"- {rule_summary}")
    match_evidence = report.get("match_evidence")
    if isinstance(match_evidence, list) and match_evidence:
        lines.append("")
        lines.append("## Match Evidence")
        for row in match_evidence:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('rule_id', 'rule')}`: {row.get('summary', '')}"
            )
            evidence = row.get("evidence")
            if isinstance(evidence, list) and evidence:
                lines.append(f"  evidence: {' | '.join(str(item) for item in evidence)}")
    rejected_rule_traces = report.get("rejected_rule_traces")
    if isinstance(rejected_rule_traces, list) and rejected_rule_traces:
        lines.append("")
        lines.append("## Rejected Rules")
        for row in rejected_rule_traces:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('rule_id', 'rule')}`: {row.get('summary', '')}"
            )
            lines.append(f"  rejected_because: {row.get('rejected_because', '')}")
            evidence = row.get("evidence")
            if isinstance(evidence, list) and evidence:
                lines.append(f"  evidence: {' | '.join(str(item) for item in evidence)}")

    if report["risk_addons"]:
        lines.append("")
        lines.append("## Risk Add-ons")
        for addon in report["risk_addons"]:
            lines.append(f"- `{addon['id']}`: {addon['label']}")
            lines.append(
                f"- `{addon['id']}` paths: {', '.join(sample_paths(addon['matched_paths']))}"
            )

    if report["planned_commands"]:
        lines.append("")
        lines.append("## Planned Commands")
        for row in report["planned_commands"]:
            lines.append(f"- `{row['source']}` -> `{row['command']}`")

    if report["steps"]:
        lines.append("")
        lines.append("## Execution Steps")
        lines.append("| Step | Source | Exit | Duration (s) |")
        lines.append("|---|---|---:|---:|")
        for step in report["steps"]:
            lines.append(
                f"| `{step['name']}` | `{step['source']}` | {step['returncode']} | {step['duration_s']} |"
            )
            failure_output = step.get("failure_output")
            if failure_output:
                escaped_output = failure_output.replace("`", "\\`")
                lines.append(f"| `{step['name']} output` | excerpt | - | - |")
                lines.append(f"|  | `{escaped_output}` | - | - |")
    return "\n".join(lines)
