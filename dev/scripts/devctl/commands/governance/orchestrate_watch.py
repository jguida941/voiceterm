"""devctl orchestrate-watch command implementation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from dev.scripts.checks.multi_agent_sync import api as check_multi_agent_sync

from ..orchestrate_status import (
    _gate_errors,
    _run_active_plan_sync_gate,
    _run_multi_agent_sync_gate,
)
from ...collect import collect_git_status
from ...common import emit_output, pipe_output, write_output
from ...time_utils import utc_timestamp

ACTIVE_STATUSES = {
    "in-progress",
    "ready-for-review",
    "changes-requested",
    "approved",
    "blocked",
}


@dataclass(frozen=True, slots=True)
class AgentWatchRow:
    agent: str
    status: str
    last_update_utc: str
    age_minutes: int


@dataclass(frozen=True, slots=True)
class OrchestrateWatchReport:
    command: str
    timestamp: str
    ok: bool
    now_utc: str
    stale_minutes: int
    active_plan_sync_ok: bool
    active_plan_sync_report: dict
    multi_agent_sync_ok: bool
    multi_agent_sync_report: dict
    stale_agent_count: int
    overdue_instruction_ack_count: int
    agent_watch: list[AgentWatchRow]
    errors: list[str]
    warnings: list[str]


def _parse_utc_z(value: str) -> datetime | None:
    if not check_multi_agent_sync.UTC_Z_PATTERN.match(value):
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _render_md(report: dict) -> str:
    lines = ["# devctl orchestrate-watch", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- now_utc: {report['now_utc']}")
    lines.append(f"- stale_minutes: {report['stale_minutes']}")
    lines.append(f"- active_plan_sync_ok: {report['active_plan_sync_ok']}")
    lines.append(f"- multi_agent_sync_ok: {report['multi_agent_sync_ok']}")
    lines.append(
        f"- overdue_instruction_ack_count: {report['overdue_instruction_ack_count']}"
    )
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


def _collect_agent_watch(
    *,
    now: datetime,
    stale_minutes: int,
    master_rows: list[dict],
) -> tuple[list[AgentWatchRow], int, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[AgentWatchRow] = []
    stale_agent_count = 0
    master_by_agent = check_multi_agent_sync._rows_by_key(master_rows, "Agent")
    required_agents = check_multi_agent_sync._sorted_agents(set(master_by_agent))
    if not required_agents:
        return rows, stale_agent_count, ["MASTER_PLAN board has no agent rows to watch."], warnings
    for agent in required_agents:
        row = master_by_agent.get(agent)
        if not row:
            continue
        agent_row, stale, error, warning = _build_agent_watch_row(
            now=now,
            stale_minutes=stale_minutes,
            agent=agent,
            row=row,
        )
        if error:
            errors.append(error)
            continue
        if warning:
            warnings.append(warning)
        if stale:
            stale_agent_count += 1
        rows.append(agent_row)
    return rows, stale_agent_count, errors, warnings


def _build_agent_watch_row(
    *,
    now: datetime,
    stale_minutes: int,
    agent: str,
    row: dict,
) -> tuple[AgentWatchRow, bool, str | None, str | None]:
    status = check_multi_agent_sync._normalize(str(row.get("Status", ""))).lower()
    last_update = check_multi_agent_sync._normalize(str(row.get("Last update (UTC)", "")))
    timestamp = _parse_utc_z(last_update)
    if timestamp is None:
        return (
            AgentWatchRow(agent=agent, status=status or "unknown", last_update_utc=last_update, age_minutes=0),
            False,
            f"{agent} has invalid Last update (UTC) value {last_update!r}.",
            None,
        )
    age_minutes = int((now - timestamp).total_seconds() // 60)
    stale = age_minutes > stale_minutes
    warning: str | None = None
    error: str | None = None
    if stale:
        message = (
            f"{agent} stale update: status={status!r}, age={age_minutes}m (> {stale_minutes}m)."
        )
        if status in ACTIVE_STATUSES:
            error = message
        else:
            warning = message
    return (
        AgentWatchRow(
            agent=agent,
            status=status or "unknown",
            last_update_utc=last_update,
            age_minutes=age_minutes,
        ),
        stale,
        error,
        warning,
    )


def _collect_overdue_instruction_state(
    *,
    now: datetime,
    instruction_rows: list[dict],
) -> tuple[int, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    overdue_instruction_ack_count = 0
    for row in instruction_rows:
        overdue, error, warning = _evaluate_instruction_ack(now=now, row=row)
        if warning:
            warnings.append(warning)
        if error:
            overdue_instruction_ack_count += 1
            errors.append(error)
        if overdue:
            continue
    return overdue_instruction_ack_count, errors, warnings


def _evaluate_instruction_ack(
    *,
    now: datetime,
    row: dict,
) -> tuple[bool, str | None, str | None]:
    instruction_id = check_multi_agent_sync._normalize(str(row.get("Instruction ID", "")))
    status = check_multi_agent_sync._normalize(str(row.get("Status", ""))).lower()
    if status not in {"pending", "acked"}:
        return False, None, None
    due_utc = check_multi_agent_sync._normalize(str(row.get("Due (UTC)", "")))
    due_timestamp = _parse_utc_z(due_utc)
    if due_timestamp is None:
        return (
            False,
            None,
            f"Instruction {instruction_id or '<missing>'} has no parseable Due (UTC); skipped SLA timer.",
        )
    if now <= due_timestamp:
        return False, None, None
    ack_token = check_multi_agent_sync._normalize(str(row.get("Ack token", "")))
    if ack_token and ack_token.lower() != "pending":
        return True, None, None
    return (
        True,
        f"Instruction {instruction_id or '<missing>'} overdue without ACK "
        f"(due {due_utc}, now {now.strftime('%Y-%m-%dT%H:%M:%SZ')}).",
        None,
    )


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
    for warning in multi_agent_sync_report.get("warnings", []):
        warning_text = str(warning).strip()
        if warning_text:
            warnings.append(f"multi-agent-sync: {warning_text}")

    git_info = collect_git_status()
    if "error" in git_info:
        errors.append(f"git-status: {git_info['error']}")

    master_text = check_multi_agent_sync.MASTER_PLAN_PATH.read_text(encoding="utf-8")
    runbook_text = check_multi_agent_sync.RUNBOOK_PATH.read_text(encoding="utf-8")
    master_rows, master_error = check_multi_agent_sync._extract_table_rows(
        master_text,
        check_multi_agent_sync.MASTER_BOARD_HEADING,
    )
    instruction_rows, instruction_error = check_multi_agent_sync._extract_table_rows(
        runbook_text,
        check_multi_agent_sync.RUNBOOK_INSTRUCTION_HEADING,
    )
    if master_error:
        errors.append(master_error)
    if instruction_error:
        errors.append(instruction_error)

    agent_watch: list[AgentWatchRow] = []
    stale_agent_count = 0
    if not master_error:
        agent_watch, stale_agent_count, agent_errors, agent_warnings = _collect_agent_watch(
            now=now,
            stale_minutes=stale_minutes,
            master_rows=master_rows,
        )
        errors.extend(agent_errors)
        warnings.extend(agent_warnings)

    overdue_instruction_ack_count = 0
    if not instruction_error:
        (
            overdue_instruction_ack_count,
            instruction_errors,
            instruction_warnings,
        ) = _collect_overdue_instruction_state(
            now=now,
            instruction_rows=instruction_rows,
        )
        errors.extend(instruction_errors)
        warnings.extend(instruction_warnings)

    ok = bool(not errors and active_plan_sync_ok and multi_agent_sync_ok)
    report = asdict(
        OrchestrateWatchReport(
            command="orchestrate-watch",
            timestamp=utc_timestamp(),
            ok=ok,
            now_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            stale_minutes=stale_minutes,
            active_plan_sync_ok=active_plan_sync_ok,
            active_plan_sync_report=active_plan_sync_report,
            multi_agent_sync_ok=multi_agent_sync_ok,
            multi_agent_sync_report=multi_agent_sync_report,
            stale_agent_count=stale_agent_count,
            overdue_instruction_ack_count=overdue_instruction_ack_count,
            agent_watch=agent_watch,
            errors=errors,
            warnings=warnings,
        )
    )

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = _render_md(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if ok else 1
