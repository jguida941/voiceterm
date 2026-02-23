"""devctl orchestrate-status command implementation."""

from __future__ import annotations

import json
from datetime import datetime

from ..collect import collect_git_status
from ..common import pipe_output, write_output
from ..policy_gate import run_json_policy_gate
from ..script_catalog import check_script_path

ACTIVE_PLAN_SYNC_SCRIPT = check_script_path("active_plan_sync")
MULTI_AGENT_SYNC_SCRIPT = check_script_path("multi_agent_sync")
MAX_CHANGED_PATHS = 20


def _run_active_plan_sync_gate() -> dict:
    return run_json_policy_gate(ACTIVE_PLAN_SYNC_SCRIPT, "active-plan sync gate")


def _run_multi_agent_sync_gate() -> dict:
    return run_json_policy_gate(MULTI_AGENT_SYNC_SCRIPT, "multi-agent sync gate")


def _gate_errors(gate_name: str, report: dict) -> list[str]:
    errors: list[str] = []
    gate_error = str(report.get("error", "")).strip()
    if gate_error:
        errors.append(f"{gate_name}: {gate_error}")
    for item in report.get("errors", []):
        text = str(item).strip()
        if text:
            errors.append(f"{gate_name}: {text}")
    return errors


def _render_md(report: dict) -> str:
    git = report["git"]
    lines = ["# devctl orchestrate-status", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- branch: {git['branch'] or 'unknown'}")
    lines.append(f"- changed_paths: {git['changed_count']}")
    lines.append(f"- active_plan_sync_ok: {report['active_plan_sync_ok']}")
    lines.append(f"- multi_agent_sync_ok: {report['multi_agent_sync_ok']}")
    lines.append(f"- errors: {len(report['errors'])}")
    if git["sample_paths"]:
        lines.append("- changed_path_sample: " + ", ".join(git["sample_paths"]))
    if report["warnings"]:
        lines.append("- warnings: " + " | ".join(report["warnings"]))

    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        for message in report["errors"]:
            lines.append(f"- {message}")
    return "\n".join(lines)


def run(args) -> int:
    """Render one-shot orchestration health for active-plan + multi-agent sync."""
    git_info = collect_git_status()
    git_error = str(git_info.get("error", "")).strip()
    changes = git_info.get("changes", []) if not git_error else []
    changed_paths = [
        str(entry.get("path", "")).strip()
        for entry in changes
        if str(entry.get("path", "")).strip()
    ]
    git_summary = {
        "branch": None if git_error else str(git_info.get("branch", "")).strip() or None,
        "changed_count": len(changed_paths),
        "sample_paths": changed_paths[:MAX_CHANGED_PATHS],
        "error": git_error or None,
    }

    active_plan_sync_report = _run_active_plan_sync_gate()
    multi_agent_sync_report = _run_multi_agent_sync_gate()
    active_plan_sync_ok = bool(active_plan_sync_report.get("ok", False))
    multi_agent_sync_ok = bool(multi_agent_sync_report.get("ok", False))

    errors: list[str] = []
    warnings: list[str] = []
    if git_error:
        errors.append(f"git-status: {git_error}")
    errors.extend(_gate_errors("active-plan-sync", active_plan_sync_report))
    errors.extend(_gate_errors("multi-agent-sync", multi_agent_sync_report))
    for warning in multi_agent_sync_report.get("warnings", []):
        warning_text = str(warning).strip()
        if warning_text:
            warnings.append(f"multi-agent-sync: {warning_text}")

    ok = bool(not errors and active_plan_sync_ok and multi_agent_sync_ok)
    report = {
        "command": "orchestrate-status",
        "timestamp": datetime.now().isoformat(),
        "ok": ok,
        "git": git_summary,
        "active_plan_sync_ok": active_plan_sync_ok,
        "active_plan_sync_report": active_plan_sync_report,
        "multi_agent_sync_ok": multi_agent_sync_ok,
        "multi_agent_sync_report": multi_agent_sync_report,
        "errors": errors,
        "warnings": warnings,
    }

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0 if ok else 1
