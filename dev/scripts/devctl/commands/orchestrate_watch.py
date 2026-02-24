"""devctl orchestrate-watch command implementation."""

from __future__ import annotations

import json
from datetime import datetime, timezone

try:
    from dev.scripts.checks import check_multi_agent_sync
except ImportError:
    from checks import check_multi_agent_sync
from ..collect import collect_git_status
from ..common import pipe_output, write_output
from ..policy_gate import run_json_policy_gate
from ..script_catalog import check_script_path

ACTIVE_PLAN_SYNC_SCRIPT = check_script_path("active_plan_sync")
MULTI_AGENT_SYNC_SCRIPT = check_script_path("multi_agent_sync")
ACTIVE_STATUSES = {"in-progress", "ready-for-review", "changes-requested", "approved", "blocked"}


def _run_active_plan_sync_gate() -> dict:
    return run_json_policy_gate(ACTIVE_PLAN_SYNC_SCRIPT, "active-plan sync gate")


def _run_multi_agent_sync_gate() -> dict:
    return run_json_policy_gate(MULTI_AGENT_SYNC_SCRIPT, "multi-agent sync gate")


def _parse_utc_z(value: str) -> datetime | None:
    if not check_multi_agent_sync.UTC_Z_PATTERN.match(value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


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
    lines = ["# devctl orchestrate-watch", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- now_utc: {report['now_utc']}")
    lines.append(f"- stale_minutes: {report['stale_minutes']}")
    lines.append(f"- active_plan_sync_ok: {report['active_plan_sync_ok']}")
    lines.append(f"- multi_agent_sync_ok: {report['multi_agent_sync_ok']}")
    lines.append(f"- overdue_instruction_ack_count: {report['overdue_instruction_ack_count']}")
    lines.append(f"- stale_agent_count: {report['stale_agent_count']}")
    if report["agent_watch"]:
        lines.append("")
        lines.append("| Agent | Status | Last update (UTC) | Age minutes |")
        lines.append("|---|---|---|---:|")
        for row in report["agent_watch"]:
            lines.append(
                f"| `{row['agent']}` | {row['status']} | {row['last_update_utc']} | {row['age_minutes']} |"
            )
    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        lines.extend(f"- {message}" for message in report["warnings"])
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        lines.extend(f"- {message}" for message in report["errors"])
    return "\n".join(lines)


def run(args) -> int:
    """Evaluate orchestrator SLA timers for board updates and instruction ACKs."""
    now = datetime.now(timezone.utc)
    stale_minutes = max(1, int(args.stale_minutes))
    errors: list[str] = []
    warnings: list[str] = []

    active_plan_sync_report = _run_active_plan_sync_gate()
    multi_agent_sync_report = _run_multi_agent_sync_gate()
    active_plan_sync_ok = bool(active_plan_sync_report.get("ok", False))
    multi_agent_sync_ok = bool(multi_agent_sync_report.get("ok", False))
    errors.extend(_gate_errors("active-plan-sync", active_plan_sync_report))
    errors.extend(_gate_errors("multi-agent-sync", multi_agent_sync_report))

    git_info = collect_git_status()
    if "error" in git_info:
        errors.append(f"git-status: {git_info['error']}")

    master_text = check_multi_agent_sync.MASTER_PLAN_PATH.read_text(encoding="utf-8")
    runbook_text = check_multi_agent_sync.RUNBOOK_PATH.read_text(encoding="utf-8")
    master_rows, master_error = check_multi_agent_sync._extract_table_rows(
        master_text, check_multi_agent_sync.MASTER_BOARD_HEADING
    )
    instruction_rows, instruction_error = check_multi_agent_sync._extract_table_rows(
        runbook_text, check_multi_agent_sync.RUNBOOK_INSTRUCTION_HEADING
    )
    if master_error:
        errors.append(master_error)
    if instruction_error:
        errors.append(instruction_error)

    agent_watch: list[dict] = []
    stale_agent_count = 0
    if not master_error:
        master_by_agent = check_multi_agent_sync._rows_by_key(master_rows, "Agent")
        required_agents = check_multi_agent_sync._sorted_agents(set(master_by_agent))
        if not required_agents:
            errors.append("MASTER_PLAN board has no agent rows to watch.")
        for agent in required_agents:
            row = master_by_agent.get(agent)
            if not row:
                continue
            status = check_multi_agent_sync._normalize(str(row.get("Status", ""))).lower()
            last_update = check_multi_agent_sync._normalize(str(row.get("Last update (UTC)", "")))
            timestamp = _parse_utc_z(last_update)
            if timestamp is None:
                errors.append(f"{agent} has invalid Last update (UTC) value {last_update!r}.")
                continue
            age_minutes = int((now - timestamp).total_seconds() // 60)
            stale = age_minutes > stale_minutes
            if stale:
                stale_agent_count += 1
                if status in ACTIVE_STATUSES:
                    errors.append(
                        f"{agent} stale update: status={status!r}, age={age_minutes}m (> {stale_minutes}m)."
                    )
                else:
                    warnings.append(
                        f"{agent} stale update: status={status!r}, age={age_minutes}m (> {stale_minutes}m)."
                    )
            agent_watch.append(
                {
                    "agent": agent,
                    "status": status or "unknown",
                    "last_update_utc": last_update,
                    "age_minutes": age_minutes,
                }
            )

    overdue_instruction_ack_count = 0
    if not instruction_error:
        for row in instruction_rows:
            instruction_id = check_multi_agent_sync._normalize(str(row.get("Instruction ID", "")))
            status = check_multi_agent_sync._normalize(str(row.get("Status", ""))).lower()
            due_utc = check_multi_agent_sync._normalize(str(row.get("Due (UTC)", "")))
            ack_token = check_multi_agent_sync._normalize(str(row.get("Ack token", "")))
            if status not in {"pending", "acked"}:
                continue
            due_timestamp = _parse_utc_z(due_utc)
            if due_timestamp is None:
                warnings.append(
                    f"Instruction {instruction_id or '<missing>'} has no parseable Due (UTC); skipped SLA timer."
                )
                continue
            if now <= due_timestamp:
                continue
            is_unacked = not ack_token or ack_token.lower() == "pending"
            if is_unacked:
                overdue_instruction_ack_count += 1
                errors.append(
                    f"Instruction {instruction_id or '<missing>'} overdue without ACK "
                    f"(due {due_utc}, now {now.strftime('%Y-%m-%dT%H:%M:%SZ')})."
                )

    ok = bool(not errors and active_plan_sync_ok and multi_agent_sync_ok)
    report = {
        "command": "orchestrate-watch",
        "timestamp": datetime.now().isoformat(),
        "ok": ok,
        "now_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stale_minutes": stale_minutes,
        "active_plan_sync_ok": active_plan_sync_ok,
        "active_plan_sync_report": active_plan_sync_report,
        "multi_agent_sync_ok": multi_agent_sync_ok,
        "multi_agent_sync_report": multi_agent_sync_report,
        "stale_agent_count": stale_agent_count,
        "overdue_instruction_ack_count": overdue_instruction_ack_count,
        "agent_watch": agent_watch,
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
