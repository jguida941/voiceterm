"""Phone-friendly autonomy status payload helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .loop_helpers import iso_z, packet_risk, utc_now
from ..phone_status_views import render_ralph_section_lines
from ..text_utils import truncate_text


@dataclass(frozen=True)
class RalphSection:
    available: bool = False
    phase: str = "idle"
    attempt: int = 0
    max_attempts: int = 0
    fix_rate_pct: float = 0.0
    total_findings: int = 0
    fixed_count: int = 0
    unresolved_count: int = 0
    branch: str | None = None
    last_run: str | None = None

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> RalphSection:
        report_path = (
            repo_root / "dev" / "reports" / "ralph" / "latest" / "ralph-report.json"
        )
        if not report_path.is_file():
            return cls()
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        total = int(data.get("total_findings") or 0)
        fixed = int(data.get("fixed_count") or 0)
        return cls(
            available=True,
            phase=str(data.get("phase") or "idle"),
            attempt=int(data.get("attempt") or 0),
            max_attempts=int(data.get("max_attempts") or 0),
            fix_rate_pct=round((fixed / total) * 100, 1) if total > 0 else 0.0,
            total_findings=total,
            fixed_count=fixed,
            unresolved_count=int(data.get("unresolved_count") or 0),
            branch=data.get("branch") or None,
            last_run=data.get("last_run") or None,
        )

    def as_payload(self) -> dict[str, Any]:
        return asdict(self)


def build_phone_status(
    *,
    plan_id: str,
    controller_run_id: str,
    repo: str,
    branch_base: str,
    mode_effective: str,
    reason: str,
    resolved: bool,
    rounds_completed: int,
    tasks_completed: int,
    max_rounds: int,
    max_tasks: int,
    current_round: int,
    latest_working_branch: str | None,
    triage_report: dict[str, Any],
    loop_packet_report: dict[str, Any],
    checkpoint_packet: dict[str, Any],
    warnings: list[str],
    errors: list[str],
    max_draft_chars: int,
    max_trace_lines: int,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    attempts = triage_report.get("attempts", [])
    attempt: dict[str, Any] = {}
    if isinstance(attempts, list):
        for row in reversed(attempts):
            if isinstance(row, dict):
                attempt = row
                break
    triage_reason = str(triage_report.get("reason") or "unknown")
    unresolved = int(triage_report.get("unresolved_count") or 0)
    risk = packet_risk(loop_packet_report, triage_report)
    next_actions = [
        str(row).strip()
        for row in (loop_packet_report.get("next_actions") or [])
        if str(row).strip()
    ]
    terminal_packet = loop_packet_report.get("terminal_packet")
    if not isinstance(terminal_packet, dict):
        terminal_packet = {}
    draft_text = truncate_text(
        terminal_packet.get("draft_text") or checkpoint_packet.get("draft_text"),
        max_draft_chars,
    )
    terminal_trace: list[str] = []
    trace_rows = checkpoint_packet.get("terminal_trace")
    if max_trace_lines > 0 and isinstance(trace_rows, list):
        for row in trace_rows:
            text = str(row).strip()
            if not text:
                continue
            terminal_trace.append(truncate_text(text, 220))
            if len(terminal_trace) >= max_trace_lines:
                break
    status_phase = "running"
    if errors:
        status_phase = "error"
    elif resolved:
        status_phase = "resolved"
    elif reason in {"max_rounds_reached", "max_tasks_reached", "max_hours_reached"}:
        status_phase = "paused"
    ralph = RalphSection.from_repo_root(repo_root) if repo_root else RalphSection()

    return {
        "schema_version": 1,
        "command": "autonomy-phone-status",
        "timestamp": iso_z(utc_now()),
        "ok": not errors,
        "phase": status_phase,
        "reason": reason,
        "controller": {
            "plan_id": plan_id,
            "controller_run_id": controller_run_id,
            "repo": repo,
            "branch_base": branch_base,
            "mode_effective": mode_effective,
            "resolved": resolved,
            "rounds_completed": rounds_completed,
            "tasks_completed": tasks_completed,
            "max_rounds": max_rounds,
            "max_tasks": max_tasks,
            "current_round": current_round,
            "latest_working_branch": latest_working_branch,
        },
        "loop": {
            "triage_reason": triage_reason,
            "unresolved_count": unresolved,
            "risk": risk,
            "next_actions": next_actions[:5],
        },
        "terminal": {
            "trace": terminal_trace,
            "draft_text": draft_text,
            "auto_send": bool(terminal_packet.get("auto_send")),
        },
        "source_run": {
            "run_id": attempt.get("run_id"),
            "run_sha": attempt.get("run_sha"),
            "run_url": attempt.get("run_url"),
            "run_conclusion": attempt.get("run_conclusion"),
            "attempt_status": attempt.get("status"),
            "attempt_message": attempt.get("message"),
        },
        "ralph": ralph.as_payload(),
        "warnings": [str(row) for row in warnings],
        "errors": [str(row) for row in errors],
    }


def render_phone_status_markdown(payload: dict[str, Any]) -> str:
    controller = payload.get("controller", {})
    loop = payload.get("loop", {})
    terminal = payload.get("terminal", {})
    source_run = payload.get("source_run", {})
    lines = ["# autonomy phone status", ""]
    lines.append(f"- phase: {payload.get('phase')}")
    lines.append(f"- reason: {payload.get('reason')}")
    lines.append(f"- plan_id: {controller.get('plan_id')}")
    lines.append(f"- run_id: {controller.get('controller_run_id')}")
    lines.append(f"- branch_base: {controller.get('branch_base')}")
    lines.append(f"- mode: {controller.get('mode_effective')}")
    lines.append(f"- resolved: {controller.get('resolved')}")
    lines.append(
        f"- progress: rounds {controller.get('rounds_completed')}/{controller.get('max_rounds')} | "
        f"tasks {controller.get('tasks_completed')}/{controller.get('max_tasks')}"
    )
    lines.append(
        f"- working_branch: {controller.get('latest_working_branch') or 'n/a'}"
    )
    lines.append(f"- unresolved_count: {loop.get('unresolved_count')}")
    lines.append(f"- risk: {loop.get('risk')}")
    lines.append(f"- triage_reason: {loop.get('triage_reason')}")
    lines.append(f"- source_run_id: {source_run.get('run_id') or 'n/a'}")
    lines.append(f"- source_run_sha: {source_run.get('run_sha') or 'n/a'}")
    lines.append(f"- source_run_url: {source_run.get('run_url') or 'n/a'}")
    lines.append("")
    lines.append("## Terminal Trace")
    lines.append("")
    trace_rows = terminal.get("trace", [])
    if isinstance(trace_rows, list) and trace_rows:
        for row in trace_rows:
            lines.append(f"- {row}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Draft")
    lines.append("")
    draft_text = str(terminal.get("draft_text") or "").strip()
    lines.append(draft_text or "(none)")
    lines.append("")
    lines.append("## Ralph Guardrail")
    lines.append("")
    ralph = payload.get("ralph", {})
    if not isinstance(ralph, dict):
        ralph = {}
    lines.extend(render_ralph_section_lines(ralph))
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    action_rows = loop.get("next_actions", [])
    if isinstance(action_rows, list) and action_rows:
        for row in action_rows:
            lines.append(f"- {row}")
    else:
        lines.append("- none")
    return "\n".join(lines)
