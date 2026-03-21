"""Push report builders and render helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ...governance.push_policy import PushPolicy


@dataclass(frozen=True, slots=True)
class PushReportInputs:
    """Structured inputs for one push report payload."""

    policy: PushPolicy
    branch: str
    remote: str
    execute: bool
    skip_preflight: bool
    skip_post_push: bool
    dirty_paths: list[str]
    fetch_step: dict[str, Any] | None
    preflight_step: dict[str, Any] | None
    push_step: dict[str, Any] | None
    post_push_steps: list[dict[str, Any]]
    typed_action: dict[str, Any]
    action_result: dict[str, Any]
    warnings: list[str]
    errors: list[str]


def build_push_report(inputs: PushReportInputs) -> dict[str, Any]:
    """Build the machine-readable push report payload."""
    report: dict[str, Any] = {}
    report["command"] = "push"
    report["timestamp"] = _timestamp()
    report["ok"] = bool(inputs.action_result.get("ok"))
    report["status"] = inputs.action_result.get("status")
    report["reason"] = inputs.action_result.get("reason")
    report["policy_path"] = inputs.policy.policy_path
    report["branch"] = inputs.branch
    report["remote"] = inputs.remote
    report["execute"] = inputs.execute
    report["skip_preflight"] = inputs.skip_preflight
    report["skip_post_push"] = inputs.skip_post_push
    report["dirty_paths"] = inputs.dirty_paths
    report["fetch_step"] = inputs.fetch_step
    report["preflight_step"] = inputs.preflight_step
    report["push_step"] = inputs.push_step
    report["post_push_steps"] = inputs.post_push_steps
    report["policy"] = _build_policy_summary(inputs.policy)
    report["typed_action"] = inputs.typed_action
    report["action_result"] = inputs.action_result
    report["warnings"] = inputs.warnings
    report["errors"] = inputs.errors
    return report


def render_push_report(report: dict[str, Any]) -> str:
    """Render the human-readable markdown report."""
    lines = ["# devctl push", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- status: {report.get('status')}")
    lines.append(f"- reason: {report.get('reason')}")
    lines.append(f"- branch: {report.get('branch')}")
    lines.append(f"- remote: {report.get('remote')}")
    lines.append(f"- execute: {report.get('execute')}")
    lines.append(f"- policy_path: {report.get('policy_path')}")
    warnings = report.get("warnings") or []
    errors = report.get("errors") or []
    lines.append(f"- warnings: {len(warnings)}")
    lines.append(f"- errors: {len(errors)}")
    lines.append("")
    lines.append("## Policy")
    lines.append("")
    policy = report.get("policy") or {}
    lines.append(f"- development_branch: {policy.get('development_branch', '(unknown)')}")
    lines.append(f"- release_branch: {policy.get('release_branch', '(unknown)')}")
    lines.append("- protected_branches: " + ", ".join(policy.get("protected_branches", [])))
    lines.append(
        "- allowed_branch_prefixes: "
        + ", ".join(policy.get("allowed_branch_prefixes", []))
    )
    typed_action = report.get("typed_action") or {}
    if typed_action:
        lines.append("")
        lines.append("## Typed Action")
        lines.append("")
        for key in sorted(typed_action.keys()):
            lines.append(f"- {key}: {typed_action.get(key)}")
    action_result = report.get("action_result") or {}
    if action_result:
        lines.append("")
        lines.append("## Action Result")
        lines.append("")
        for key in sorted(action_result.keys()):
            lines.append(f"- {key}: {action_result.get(key)}")
    _append_step_section(lines, "Preflight", report.get("preflight_step"))
    _append_step_section(lines, "Push Step", report.get("push_step"))
    post_push_steps = report.get("post_push_steps") or []
    if post_push_steps:
        lines.append("")
        lines.append("## Post Push")
        lines.append("")
        for step in post_push_steps:
            lines.extend(_render_step_lines(step))
    if warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        lines.extend(f"- {warning}" for warning in warnings)
    if errors:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines)


def _append_step_section(
    lines: list[str],
    title: str,
    step: dict[str, Any] | None,
) -> None:
    if not step:
        return
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")
    lines.extend(_render_step_lines(step))


def _build_policy_summary(policy: PushPolicy) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    summary["development_branch"] = policy.development_branch
    summary["release_branch"] = policy.release_branch
    summary["protected_branches"] = list(policy.protected_branches)
    summary["allowed_branch_prefixes"] = list(policy.allowed_branch_prefixes)
    return summary


def _render_step_lines(step: dict[str, Any]) -> list[str]:
    command = " ".join(str(part) for part in step.get("cmd", []))
    lines = [f"- {step.get('name')}: rc={step.get('returncode')} cmd=`{command}`"]
    failure_output = step.get("failure_output")
    if failure_output:
        lines.append(f"  failure_output: {failure_output}")
    return lines


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
