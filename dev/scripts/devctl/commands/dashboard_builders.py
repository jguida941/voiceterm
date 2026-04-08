"""Section-builder functions for the DashboardSnapshot.

Each ``_build_*`` function accepts pre-loaded artifact data and returns a typed
dict for one snapshot section.  Utility functions are imported from
``dashboard_utils`` to avoid a circular import with ``dashboard``.
Summary compilation lives in ``dashboard_summary``, and publication/quality/
audit/analytics/probes builders live in ``dashboard_data``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CoordinationContext:
    """Bundled inputs for the coordination section builder."""

    instruction_rev: str
    receipt_push: str
    session_info: dict[str, Any]
    typed_packets: list[dict[str, Any]]
    runtime_counts: dict[str, int]

from .dashboard_utils import (
    _age_seconds,
    _format_age,
)

# Summary compilation re-exported so dashboard.py can import them from here
from .dashboard_summary import (  # noqa: F401
    _build_one_line,
    _compile_summary,
    _is_reviewer_overdue,
)

# Data extraction builders re-exported for backward compat
from .dashboard_data import (  # noqa: F401
    _build_analytics_section,
    _build_audit_section,
    _build_probes_section,
    _build_quality_section,
    _extract_check_details,
    _extract_cleanup_rate,
    _extract_failing_files,
    _extract_push_success_values,
    _extract_push_timers,
    _extract_top_commands,
    _publication_effective,
)


def _derive_top_blocker(
    quality: dict[str, Any], session: dict[str, Any], doctor: dict[str, Any],
) -> str:
    """Identify the single most important blocker from quality gates and findings."""
    failing = quality.get("failing", [])
    if failing:
        return f"code-shape debt in {failing[0]}"
    blocked = doctor.get("blocked_reason", "")
    if blocked and blocked != "pipeline_unavailable":
        return blocked
    findings = session.get("open_findings", "")
    if findings and findings.strip().lower() not in ("none", ""):
        first_line = findings.strip().splitlines()[0].lstrip("- ").strip()
        return first_line[:60] + ("..." if len(first_line) > 60 else "")
    return "none"


def _build_now_section(
    bridge: dict[str, str],
    reviewer: dict[str, Any],
    implementer: dict[str, Any],
    session: dict[str, Any],
    top_blocker: str,
    last_change_age: int | None,
) -> dict[str, Any]:
    """Build the NOW section: who owns the loop right now and what they should do."""
    impl_state = implementer.get("job_state", "n/a")
    owner = "Implementer" if impl_state == "implementing" else "Reviewer"
    reviewer_provider = reviewer.get("provider", "n/a")
    impl_provider = implementer.get("provider", "n/a")
    owner_provider = impl_provider if owner == "Implementer" else reviewer_provider

    next_action = session.get("implementer_status", "")
    if not next_action or next_action == "n/a":
        next_action = "review worker results and checkpoint"
    else:
        first_line = next_action.strip().splitlines()[0].lstrip("- ").strip()
        next_action = first_line[:60] + ("..." if len(first_line) > 60 else "")

    instr_full = bridge.get("instruction_full", "n/a")
    if instr_full and instr_full != "n/a":
        first_line = instr_full.strip().splitlines()[0].lstrip("- ").strip()
        instr_text = first_line[:100] + ("..." if len(first_line) > 100 else "")
    else:
        instr_text = "n/a"

    return {
        "owner": owner,
        "owner_provider": owner_provider,
        "next_action": next_action,
        "top_blocker": top_blocker,
        "last_change_age_s": last_change_age,
        "last_change_label": _format_age(last_change_age),
        "instruction_text": instr_text,
    }


def _find_agent_by_role(
    agents_data: dict[str, Any] | None, role: str,
) -> dict[str, Any]:
    """Find an agent entry by lane_title or current_job role, with name fallback.

    Tries role-based matching first (case-insensitive lane_title or current_job),
    then falls back to matching the provider name for backwards compatibility
    with older agent registries that lack role fields.
    """
    if not agents_data:
        return {}
    agents = agents_data.get("agents", [])
    role_lower = role.lower()
    for agent in agents:
        lane = (agent.get("lane_title") or "").lower()
        job = (agent.get("current_job") or "").lower()
        if lane == role_lower or job == role_lower:
            return agent
    _NAME_FALLBACK = {"reviewer": "codex", "implementer": "claude"}
    fallback_name = _NAME_FALLBACK.get(role_lower, role_lower)
    for agent in agents:
        if agent.get("provider") == fallback_name:
            return agent
    return {}


def _build_review_section(
    bridge: dict[str, str],
    reviewer: dict[str, Any],
    implementer: dict[str, Any],
    session: dict[str, Any],
) -> dict[str, Any]:
    reviewer_state = reviewer.get("job_state", "n/a")
    implementer_state = implementer.get("job_state", "n/a")
    current_turn = "Implementer" if implementer_state == "implementing" else "Reviewer"
    instruction_text = session.get("current_instruction", bridge.get("instruction", "n/a"))
    if instruction_text and len(instruction_text) > 120:
        instruction_text = instruction_text[:120] + "..."
    return {
        "reviewer_state": reviewer_state,
        "reviewer_provider": reviewer.get("provider", "n/a"),
        "implementer_state": implementer_state,
        "implementer_provider": implementer.get("provider", "n/a"),
        "current_turn": current_turn,
        "instruction": instruction_text,
        "last_poll": bridge.get("last_poll", "n/a"),
        "mode": bridge.get("reviewer_mode", "n/a"),
    }


def _build_workers_section(agents_data: dict[str, Any] | None) -> list[dict[str, str]]:
    """Build worker rows with scope, state, age, and last update summary."""
    if not agents_data:
        return []
    workers = []
    for idx, a in enumerate(agents_data.get("agents", []), start=1):
        updated = a.get("updated_at", "")
        age = _age_seconds(updated)
        workers.append({
            "id": f"W{idx}",
            "agent_id": a.get("agent_id", "unknown"),
            "scope": a.get("lane_title", a.get("current_job", "unknown")),
            "provider": a.get("provider", "unknown"),
            "state": a.get("job_state", "unknown").upper(),
            "age": _format_age(age),
            "last_update": a.get("waiting_on", ""),
        })
    return workers


def _build_plan_section(
    plan: dict[str, str],
    session: dict[str, Any],
    bridge_findings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build the PLAN section from master plan data, session findings, and bridge detail."""
    findings_text = (session.get("open_findings") or "").strip()
    finding_count = 0
    if findings_text and findings_text.lower() != "none":
        finding_count = len([
            ln for ln in findings_text.splitlines()
            if ln.strip().startswith("- F") or ln.strip().startswith("-")
        ])
    detail = bridge_findings or []
    if detail:
        finding_count = len(detail)
    return {
        "slice": plan.get("slice", "n/a"),
        "progress": plan.get("progress", "n/a"),
        "open_findings": finding_count,
        "findings_detail": detail,
        "pending": 0,
    }


def _build_coordination_section(
    session: dict[str, Any],
    bridge: dict[str, str],
    doctor: dict[str, Any],
    ctx: CoordinationContext,
) -> dict[str, Any]:
    """Build compact coordination section with dual-field layout.

    When ``ctx.typed_packets`` are supplied (from ReviewState),
    pending_packets is derived from the actual queue count.
    """
    findings = (session.get("open_findings") or "None").strip()
    finding_lines = [
        ln for ln in findings.splitlines() if ln.strip().startswith("-")
    ] if findings.lower() != "none" else []

    reviewer_age = _age_seconds(bridge.get("last_poll_utc", ""))
    pending_count = len(ctx.typed_packets) if ctx.typed_packets else 0
    doctor_status = doctor.get("status", "")
    doctor_summary = doctor.get("summary", "")
    doctor_blocked = doctor.get("blocked_reason", "")

    return {
        "pending_packets": pending_count,
        "instruction_rev": ctx.instruction_rev,
        "reviewer_age": _format_age(reviewer_age),
        "implementer_state": "current" if session.get("implementer_ack_state") == "current" else "stale",
        "pending_findings": f"{len(finding_lines)} findings" if finding_lines else "0 findings",
        "next_action": ctx.receipt_push,
        "session_age": ctx.session_info.get("session_label", "--"),
        "session_started": ctx.session_info.get("started_time", ""),
        "doctor_status": doctor_status if doctor_status else "n/a",
        "doctor_summary": doctor_summary if doctor_summary else "n/a",
        "doctor_blocked": doctor_blocked if doctor_blocked else "none",
        "active_conductors": ctx.runtime_counts.get("active_conductor_count", 0),
        "live_agents": ctx.runtime_counts.get("live_participant_count", 0),
        "live_reviewers": ctx.runtime_counts.get("live_reviewer_count", 0),
        "live_implementers": ctx.runtime_counts.get("live_implementer_count", 0),
        "running_daemons": ctx.runtime_counts.get("running_daemon_count", 0),
        "delegated_agents": ctx.runtime_counts.get("delegated_work_total", 0),
        "planned_lanes": ctx.runtime_counts.get("planned_lane_total", 0),
        "requested_worker_budget": ctx.runtime_counts.get(
            "requested_worker_budget_total", 0
        ),
    }


def _build_flow_section(
    receipt: dict[str, Any] | None,
    push_data: dict[str, Any] | None,
    session: dict[str, Any],
) -> dict[str, Any]:
    stages = {
        "review": "unknown",
        "implement": "unknown",
        "verify": "unknown",
        "checkpoint": "unknown",
        "push": "unknown",
    }
    if receipt:
        if receipt.get("push_eligible_now"):
            stages["checkpoint"] = "pass"
        if receipt.get("review_gate_allows_push"):
            stages["review"] = "pass"
        if receipt.get("safe_to_continue_editing"):
            stages["implement"] = "active"
    if push_data:
        push_ok = push_data.get("ok")
        stages["push"] = "pass" if push_ok else "blocked"
    impl_state = session.get("implementer_status", "")
    impl_ack = session.get("implementer_ack_state", "")
    if impl_state and impl_ack != "stale":
        stages["implement"] = "active"
    elif impl_state:
        stages["implement"] = "stale"
    return stages


def _build_reviewer_activity_section(
    bridge: dict[str, str],
    reviewer_agent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build reviewer activity section from bridge.md parsed fields.

    Answers the operator's core question: 'Is the reviewer doing anything?'
    The provider sublabel is derived from the actual agent data so the
    section header stays portable across reviewer providers.
    """
    poll_utc = bridge.get("last_poll_utc", "")
    poll_age = _format_age(_age_seconds(poll_utc))

    verdict_raw = bridge.get("verdict", "n/a")
    verdict_first_line = _first_meaningful_line(verdict_raw)
    verdict_summary = verdict_first_line[:80] + ("..." if len(verdict_first_line) > 80 else "")

    findings_raw = bridge.get("findings_raw", "")
    finding_lines = [
        ln for ln in findings_raw.splitlines()
        if ln.strip().startswith("- F") or ln.strip().startswith("-")
    ] if findings_raw else []
    findings_posted = len(finding_lines)

    scope_raw = bridge.get("reviewed_scope_raw", "")
    scope_lines = [
        ln for ln in scope_raw.splitlines()
        if ln.strip().startswith("- ") or ln.strip().startswith("*")
    ] if scope_raw else []
    reviewed_files = len(scope_lines)

    instr_full = bridge.get("instruction_full", "n/a")
    instr_first = _first_meaningful_line(instr_full)
    instruction_summary = instr_first[:80] + ("..." if len(instr_first) > 80 else "")

    provider = (reviewer_agent or {}).get("provider", "unknown")

    return {
        "provider": provider,
        "last_poll_age": poll_age,
        "last_verdict": verdict_summary if verdict_summary != "n/a" else "n/a",
        "reviewed_files": reviewed_files,
        "instruction_summary": instruction_summary if instruction_summary != "n/a" else "n/a",
        "findings_posted": findings_posted,
    }


def _first_meaningful_line(text: str) -> str:
    """Return the first non-empty line from text, stripping leading '- '."""
    if not text or text == "n/a":
        return "n/a"
    for line in text.splitlines():
        stripped = line.strip().lstrip("- ").strip()
        if stripped:
            return stripped
    return "n/a"
