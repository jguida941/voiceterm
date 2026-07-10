"""Pure round-state helpers for `devctl autonomy-loop`."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

from ...autonomy.loop_helpers import HARD_REASON_CODES, packet_risk, utc_now


@dataclass(frozen=True)
class StopCheck:
    started_at: datetime
    max_duration: timedelta
    tasks_completed: int
    max_tasks: int


@dataclass(frozen=True)
class RoundInfo:
    round_index: int
    working_branch: str
    loop_branch: str


@dataclass(frozen=True)
class RoundReports:
    triage_rc: int
    loop_packet_rc: int
    triage_report: dict[str, Any]
    loop_packet_report: dict[str, Any]


@dataclass(frozen=True)
class RoundSummary:
    round: int
    working_branch: str
    loop_branch: str
    triage_rc: int
    packet_rc: int
    triage_reason: str
    unresolved_count: int
    risk: str
    packet_path: str
    phone_status_json: str
    requires_approval: bool
    probe_scan: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def should_stop_before_round(stop_check: StopCheck) -> str | None:
    if utc_now() - stop_check.started_at > stop_check.max_duration:
        return "max_hours_reached"
    if stop_check.tasks_completed >= stop_check.max_tasks:
        return "max_tasks_reached"
    return None


def build_round_summary(
    *,
    round_info: RoundInfo,
    reports: RoundReports,
    checkpoint_path: str,
    round_phone_json: str,
    checkpoint_packet: dict[str, Any],
) -> dict[str, Any]:
    unresolved = int(reports.triage_report.get("unresolved_count") or 0)
    triage_reason = str(reports.triage_report.get("reason") or "unknown")
    return RoundSummary(
        round=round_info.round_index,
        working_branch=round_info.working_branch,
        loop_branch=round_info.loop_branch,
        triage_rc=reports.triage_rc,
        packet_rc=reports.loop_packet_rc,
        triage_reason=triage_reason,
        unresolved_count=unresolved,
        risk=packet_risk(reports.loop_packet_report, reports.triage_report),
        packet_path=checkpoint_path,
        phone_status_json=round_phone_json,
        requires_approval=bool(checkpoint_packet.get("requires_approval")),
        probe_scan=checkpoint_packet.get("probe_scan"),
    ).to_dict()


def resolve_round_exit(
    *,
    round_info: RoundInfo,
    reports: RoundReports,
    errors: list[str],
) -> tuple[bool, str, bool]:
    unresolved = int(reports.triage_report.get("unresolved_count") or 0)
    triage_reason = str(reports.triage_report.get("reason") or "unknown")
    if triage_reason in HARD_REASON_CODES:
        errors.append(
            f"round {round_info.round_index}: hard stop reason from triage-loop ({triage_reason})"
        )
        return True, triage_reason, False
    if reports.triage_rc not in (0, 1):
        errors.append(
            f"round {round_info.round_index}: triage-loop exited {reports.triage_rc}"
        )
        return True, "triage_loop_failed", False
    if reports.loop_packet_rc not in (0, 1):
        errors.append(
            f"round {round_info.round_index}: loop-packet exited {reports.loop_packet_rc}"
        )
        return True, "loop_packet_failed", False
    if unresolved <= 0 and triage_reason == "resolved":
        return True, "resolved", True
    return False, "max_rounds_reached", False
