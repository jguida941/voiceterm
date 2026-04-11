"""Section builders for the DashboardSnapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .dashboard_utils import (
    _age_seconds,
    _format_age,
)

@dataclass(frozen=True, slots=True)
class CoordinationContext:
    """Bundled inputs for the coordination section."""

    instruction_rev: str
    receipt_push: str
    session_info: dict[str, Any]
    typed_packets: list[dict[str, Any]]
    runtime_counts: dict[str, int]


@dataclass(frozen=True, slots=True)
class NowSectionContext:
    """Inputs for the dashboard NOW section.

    ``top_blocker`` and ``next_action`` are passed in from the canonical
    ``BlockerSnapshot`` (via ``ControlPlaneReadModel`` or
    ``StartupContext.blocker``) so the NOW section never re-derives
    authority strings locally. The legacy implementer-status text stays
    available via ``session`` for display-only fallback when the typed
    producer did not supply a decision.
    """

    bridge: dict[str, str]
    reviewer: dict[str, Any]
    implementer: dict[str, Any]
    session: dict[str, Any]
    instruction_text: str
    top_blocker: str
    last_change_age: int | None
    next_action_override: str = ""


from .dashboard_summary import (
    _build_one_line,
    _compile_summary,
    _is_reviewer_overdue,
)

from .dashboard_data import (
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
from .dashboard_people import (
    _build_review_section,
    _build_reviewer_activity_section,
    _build_workers_section,
    _first_meaningful_line,
)


def _build_now_section(ctx: NowSectionContext) -> dict[str, Any]:
    """Build the NOW section: who owns the loop right now and what they should do."""
    impl_state = ctx.implementer.get("job_state", "n/a")
    owner = "Implementer" if impl_state == "implementing" else "Reviewer"
    reviewer_provider = ctx.reviewer.get("provider", "n/a")
    impl_provider = ctx.implementer.get("provider", "n/a")
    owner_provider = impl_provider if owner == "Implementer" else reviewer_provider

    override = (ctx.next_action_override or "").strip()
    if override and override != "n/a":
        first_line = override.splitlines()[0].lstrip("- ").strip()
        next_action = first_line[:60] + ("..." if len(first_line) > 60 else "")
    else:
        # Legacy display-only fallback: the NOW section shows the
        # implementer's free-form status string when no typed push
        # decision was routed in. The canonical blocker/next_action
        # authority still lives in BlockerSnapshot; this branch only
        # exists so dashboards rendered without a control-plane model
        # still get a human-readable hint.
        next_action = ctx.session.get("implementer_status", "")
        if not next_action or next_action == "n/a":
            next_action = "review worker results and checkpoint"
        else:
            first_line = next_action.strip().splitlines()[0].lstrip("- ").strip()
            next_action = first_line[:60] + ("..." if len(first_line) > 60 else "")

    instr_text = (ctx.instruction_text or "").strip()
    if instr_text and instr_text != "n/a":
        first_line = instr_text.splitlines()[0].lstrip("- ").strip()
        instr_text = first_line[:100] + ("..." if len(first_line) > 100 else "")
    else:
        instr_text = "n/a"

    return {
        "owner": owner,
        "owner_provider": owner_provider,
        "next_action": next_action,
        "top_blocker": ctx.top_blocker,
        "last_change_age_s": ctx.last_change_age,
        "last_change_label": _format_age(ctx.last_change_age),
        "instruction_text": instr_text,
    }


def _find_agent_by_role(
    agents_data: dict[str, Any] | None, role: str,
) -> dict[str, Any]:
    """Find an agent entry by role, with provider-name fallback."""
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


def _build_plan_section(
    coordination: dict[str, Any] | None,
    session: dict[str, Any],
    bridge_findings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build the PLAN section from typed coordination, session, and findings."""
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
    slice_text = ""
    progress_text = ""
    if coordination:
        slice_text = str(coordination.get("current_slice") or "").strip()
        progress_text = str(
            coordination.get("ownership_status")
            or coordination.get("resolved_phase")
            or ""
        ).strip()
    if not slice_text:
        slice_text = str(session.get("current_instruction") or "n/a").strip() or "n/a"
    if not progress_text:
        progress_text = str(session.get("implementer_status") or "n/a").strip() or "n/a"
    return {
        "slice": slice_text,
        "progress": progress_text,
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
    """Build compact coordination from typed packets and session state."""
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
