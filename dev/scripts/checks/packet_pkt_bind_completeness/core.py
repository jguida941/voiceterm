"""Validate Codex task-start packets get durable PKT-BIND plan rows."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT

from dev.scripts.devctl.runtime.repo_portability import GuardMandate
from dev.scripts.devctl.runtime.repo_portability import resolve_guard_mandate

from .constants import COMMAND, DEFAULT_EVENT_LOG_REL, DEFAULT_GRACE_MINUTES
from .constants import DEFAULT_PLAN_INDEX_REL
from .models import PacketBindGap, TaskStart
from .readers import read_bound_packet_ids, read_packet_events
from .time_support import age_minutes, display_path, format_timestamp, parse_timestamp
from .time_support import text


def evaluate_packet_pkt_bind_completeness(
    *,
    repo_root: Path = REPO_ROOT,
    event_log_path: Path | None = None,
    plan_index_path: Path | None = None,
    now_utc: datetime | None = None,
    grace_minutes: int = DEFAULT_GRACE_MINUTES,
    strict_legacy: bool = False,
) -> dict[str, object]:
    """Return durable binding coverage for Codex ``task_started`` packets.

    The repo-policy mandate window is forward-enforcing. Older ``task_started``
    packets are still reported so packet debt stays visible, but only
    post-mandate packets block by default. A missing binding blocks once either
    the grace window expires or a paired ``task_produced`` packet is posted,
    whichever happens first.
    """
    resolved_event_log = event_log_path or repo_root / DEFAULT_EVENT_LOG_REL
    resolved_plan_index = plan_index_path or repo_root / DEFAULT_PLAN_INDEX_REL
    current_time = now_utc or datetime.now(UTC)
    task_starts, task_produced, event_errors = read_packet_events(
        resolved_event_log
    )
    bound_packet_ids, plan_errors = read_bound_packet_ids(resolved_plan_index)
    mandate = resolve_guard_mandate(COMMAND, repo_root=repo_root)
    violations: list[PacketBindGap] = []
    legacy_gaps: list[PacketBindGap] = []
    pending_packets: list[dict[str, object]] = []
    bound_count = 0
    enforced_count = 0
    legacy_count = 0

    for task_start in task_starts:
        enforced = _task_start_is_enforced(task_start, mandate=mandate)
        if enforced:
            enforced_count += 1
        else:
            legacy_count += 1
        if task_start.packet_id in bound_packet_ids:
            bound_count += 1
            continue
        deadline_at, deadline_reason = _binding_deadline(
            task_start=task_start,
            task_produced=task_produced,
            grace_minutes=grace_minutes,
        )
        minutes_old = age_minutes(task_start.timestamp_utc, current_time)
        if current_time < deadline_at:
            pending_packets.append(
                {
                    "line_number": task_start.line_number,
                    "packet_id": task_start.packet_id,
                    "deadline_reason": deadline_reason,
                    "deadline_at_utc": format_timestamp(deadline_at),
                    "age_minutes": minutes_old,
                }
            )
            continue
        scope = "enforced" if enforced or strict_legacy else "legacy"
        gap = PacketBindGap(
            line_number=task_start.line_number,
            packet_id=task_start.packet_id,
            scope=scope,
            deadline_reason=deadline_reason,
            age_minutes=minutes_old,
            detail=(
                "Codex task_started packets must have a durable "
                "PKT-BIND-REV-PKT-* PlanRow by the binding deadline."
            ),
        )
        if scope == "enforced":
            violations.append(gap)
        else:
            legacy_gaps.append(gap)

    errors = [*event_errors, *plan_errors]
    report = {
        "command": COMMAND,
        "schema_version": 1,
        "ok": not errors and not violations,
        "event_log_path": display_path(resolved_event_log, repo_root=repo_root),
        "plan_index_path": display_path(resolved_plan_index, repo_root=repo_root),
        "mandate_packet_id": mandate.mandate_packet_id,
        "mandate_observed_at_utc": mandate.observed_at_utc,
        "mandate_policy_path": mandate.policy_path,
        "mandate_policy_warnings": list(mandate.warnings),
        "grace_minutes": grace_minutes,
        "strict_legacy": strict_legacy,
        "task_started_count": len(task_starts),
        "enforced_task_started_count": enforced_count,
        "legacy_task_started_count": legacy_count,
        "bound_task_started_count": bound_count,
        "pending_within_grace_count": len(pending_packets),
        "violation_count": len(violations),
        "legacy_gap_count": len(legacy_gaps),
        "violations": [gap.to_dict() for gap in violations],
        "legacy_gaps": [gap.to_dict() for gap in legacy_gaps],
        "pending_within_grace": pending_packets,
        "errors": errors,
    }
    report["human_summary"] = _human_summary(report)
    return report

def _binding_deadline(
    *,
    task_start: TaskStart,
    task_produced: list[dict[str, object]],
    grace_minutes: int,
) -> tuple[datetime, str]:
    grace_deadline = task_start.timestamp_utc + timedelta(minutes=grace_minutes)
    produced_at = _paired_task_produced_at(task_start, task_produced)
    if produced_at is not None and produced_at < grace_deadline:
        return produced_at, "paired_task_produced"
    return grace_deadline, "grace_minutes"


def _paired_task_produced_at(
    task_start: TaskStart,
    task_produced: list[dict[str, object]],
) -> datetime | None:
    candidates: list[datetime] = []
    for event in task_produced:
        if not _produced_event_matches(task_start, event):
            continue
        timestamp = parse_timestamp(text(event.get("timestamp_utc")))
        if timestamp is not None and timestamp >= task_start.timestamp_utc:
            candidates.append(timestamp)
    return min(candidates) if candidates else None


def _produced_event_matches(task_start: TaskStart, event: dict[str, object]) -> bool:
    correlation_id = text(event.get("correlation_id"))
    if task_start.correlation_id and correlation_id == task_start.correlation_id:
        return True
    target_ref = text(event.get("target_ref"))
    return bool(task_start.target_ref and target_ref == task_start.target_ref)


def _task_start_is_enforced(task_start: TaskStart, *, mandate: GuardMandate) -> bool:
    if not mandate.observed_at_utc:
        return False
    return format_timestamp(task_start.timestamp_utc) >= mandate.observed_at_utc


def _human_summary(report: dict[str, object]) -> dict[str, object]:
    violation_count = int(report["violation_count"])
    enforced_count = int(report["enforced_task_started_count"])
    pending_count = int(report["pending_within_grace_count"])
    legacy_count = int(report["legacy_gap_count"])
    if violation_count:
        headline = f"FAIL - {violation_count} enforced task_started packet(s) lack PKT-BIND rows."
    elif enforced_count == 0:
        headline = "EMPTY - no post-mandate Codex task_started packets were evaluated."
    else:
        headline = f"PASS - {enforced_count} enforced task_started packet(s) have PKT-BIND coverage."
    conclusions = [
        f"Bound packets: {report['bound_task_started_count']} of {report['task_started_count']} observed Codex task_started packets.",
        f"Pending within grace: {pending_count}.",
        f"Legacy gaps: {legacy_count}.",
    ]
    recommendations: list[str] = []
    if violation_count:
        recommendations.append("Add PKT-BIND-REV-PKT-* PlanRows for violating packets.")
    elif pending_count:
        recommendations.append("Let pending packets bind before the grace deadline or task_produced closure.")
    return {
        "contract_id": "TypedOutputHumanSummary",
        "schema_version": 1,
        "headline": headline,
        "items_processed": int(report["task_started_count"]),
        "conclusions": conclusions,
        "evaluable_scopes": {
            "enforced_task_started": enforced_count,
            "legacy_task_started": int(report["legacy_task_started_count"]),
        },
        "blind_pass_warning": (
            "No post-mandate task_started packets matched the enforcement window."
            if enforced_count == 0
            else ""
        ),
        "recommendations": recommendations,
    }
