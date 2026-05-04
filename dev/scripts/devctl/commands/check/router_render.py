"""Markdown rendering helpers for check-router output."""

from __future__ import annotations

from .router_support import sample_paths


def render_markdown(report: dict) -> str:
    lines = ["# devctl check-router", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- lane: {report['lane']}")
    lines.append(f"- bundle: {report['bundle']}")
    lines.append(f"- commit_range: {report['since_ref']}...{report['head_ref']}")
    lines.append(f"- changed_paths: {len(report['changed_paths'])}")
    lines.append(f"- execute: {report['execute']}")
    lines.append(
        "- parallel: "
        f"{bool(report.get('parallel_enabled', False))} "
        f"(workers={int(report.get('parallel_workers') or 1)})"
    )
    lines.append(f"- risk_addons: {len(report['risk_addons'])}")
    lines.append(f"- planned_commands: {len(report['planned_commands'])}")
    execution_plan = report.get("execution_plan")
    if isinstance(execution_plan, dict):
        lines.append(
            "- execution_plan: "
            f"serial={execution_plan.get('serial_required_command_count', 0)} "
            f"parallel_safe={execution_plan.get('parallel_safe_command_count', 0)} "
            f"phases={execution_plan.get('phase_count', 0)}"
        )
    execution_policy = report.get("execution_policy")
    if isinstance(execution_policy, dict):
        lines.append(
            "- execution_policy: "
            f"command_timeout={execution_policy.get('command_timeout_seconds', 0)}s "
            f"route_timeout={execution_policy.get('route_timeout_seconds', 0)}s"
        )
    coverage = report.get("guard_coverage")
    if isinstance(coverage, dict):
        lines.append(
            "- guard_coverage: "
            f"planned={coverage.get('planned_command_count', 0)} "
            f"executed={coverage.get('executed_command_count', 0)} "
            f"failed={coverage.get('failed_command_count', 0)} "
            f"unexecuted={coverage.get('unexecuted_command_count', 0)}"
        )
        lines.append(
            "- guard_coverage_all_executed: "
            f"{coverage.get('all_planned_commands_executed', False)}"
        )
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
            safety = row.get("parallel_safety", "parallel_safe")
            reason = row.get("parallel_reason", "")
            timeout = row.get("timeout_seconds")
            timeout_text = f", timeout={timeout}s" if timeout else ""
            suffix = (
                f" [{safety}{timeout_text}: {reason}]"
                if reason
                else f" [{safety}{timeout_text}]"
            )
            lines.append(f"- `{row['source']}` -> `{row['command']}`{suffix}")

    if report["steps"]:
        lines.append("")
        lines.append("## Execution Steps")
        lines.append("| Step | Source | Exit | Duration (s) | Timeout (s) |")
        lines.append("|---|---|---:|---:|---:|")
        for step in report["steps"]:
            lines.append(
                f"| `{step['name']}` | `{step['source']}` | {step['returncode']} | {step['duration_s']} | {step.get('timeout_seconds', '')} |"
            )
            failure_output = step.get("failure_output")
            if failure_output:
                escaped_output = failure_output.replace("`", "\\`")
                lines.append(f"| `{step['name']} output` | excerpt | - | - | - |")
                lines.append(f"|  | `{escaped_output}` | - | - | - |")
    remediation_actions = report.get("remediation_actions")
    if isinstance(remediation_actions, list) and remediation_actions:
        lines.append("")
        lines.append("## Remediation Actions")
        for action in remediation_actions:
            if not isinstance(action, dict):
                continue
            paths = action.get("required_paths")
            paths_text = ", ".join(str(path) for path in paths) if isinstance(paths, list) else ""
            lines.append(
                "- "
                + str(action.get("action_id") or "guard-remediation")
                + ": "
                + str(action.get("reason") or "guard_failed")
            )
            if paths_text:
                lines.append(f"  required_paths: {paths_text}")
            remediation = str(action.get("remediation") or "").strip()
            if remediation:
                lines.append(f"  remediation: {remediation}")
    return "\n".join(lines)
