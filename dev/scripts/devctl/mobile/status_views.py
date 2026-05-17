"""Projection/render helpers for `devctl mobile-status`."""

from __future__ import annotations

from typing import Any

from .status_projection import (
    ActionsMobileStatusProjection,
    AlertMobileStatusProjection,
    CompactMobileStatusProjection,
    MobileStatusView,
    OperatorActionPayload,
    operator_action_rows,
    parse_mobile_status_view,
    string_rows,
)
from .phone_view_support import truncate_status_text
from .phone_views import actions_view as phone_actions_view
from .phone_views import compact_view as phone_compact_view
from ..runtime import ControlState, control_state_from_payload


def _controller_payload(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("controller_payload")
    return value if isinstance(value, dict) else {}


def _control_state(payload: dict[str, Any] | ControlState) -> ControlState | None:
    if isinstance(payload, ControlState):
        return payload
    return control_state_from_payload(payload)


def _fallback_compact(payload: dict[str, Any]) -> CompactMobileStatusProjection:
    controller_compact = phone_compact_view(_controller_payload(payload))
    controller_phase = str(controller_compact.get("phase") or "unknown")
    unresolved_count = int(controller_compact.get("unresolved_count") or 0)
    return CompactMobileStatusProjection(
        headline=(f"{controller_phase.upper()} | review unknown | unresolved {unresolved_count}"),
        controller_phase=controller_phase,
        controller_reason=str(controller_compact.get("reason") or "unknown"),
        controller_risk=str(controller_compact.get("risk") or "unknown"),
        plan_id=str(controller_compact.get("plan_id") or ""),
        controller_run_id=str(controller_compact.get("controller_run_id") or ""),
        review_bridge_state="unknown",
        codex_poll_state="unknown",
        reviewer_poll_state="unknown",
        codex_last_poll_utc="",
        last_reviewer_poll_utc="",
        last_worktree_hash="",
        pending_total=0,
        unresolved_count=unresolved_count,
        current_instruction="",
        open_findings="",
        claude_status="",
        claude_ack="",
        implementer_status="",
        implementer_ack="",
        codex_status="unknown",
        claude_lane_status="unknown",
        operator_status="unknown",
        source_run_url=str(controller_compact.get("source_run_url") or ""),
        approval_mode="unknown",
        approval_summary="",
        next_actions=string_rows(controller_compact.get("next_actions")),
    )


def compact_view(payload: dict[str, Any] | ControlState) -> dict[str, Any]:
    state = _control_state(payload)
    if state is None:
        fallback_payload = payload if isinstance(payload, dict) else {}
        return _fallback_compact(fallback_payload).to_dict()
    active_run = state.primary_run()
    if active_run is None:
        fallback_payload = payload if isinstance(payload, dict) else {}
        return _fallback_compact(fallback_payload).to_dict()
    bridge = state.review_bridge
    return CompactMobileStatusProjection(
        headline=(
            f"{active_run.phase.upper()} | review {bridge.overall_state} | "
            f"unresolved {active_run.unresolved_count}"
        ),
        controller_phase=active_run.phase,
        controller_reason=active_run.reason,
        controller_risk=active_run.risk,
        plan_id=active_run.plan_id,
        controller_run_id=active_run.controller_run_id,
        review_bridge_state=bridge.overall_state,
        codex_poll_state=bridge.codex_poll_state,
        reviewer_poll_state=bridge.reviewer_poll_state or bridge.codex_poll_state,
        codex_last_poll_utc=bridge.last_codex_poll_utc,
        last_reviewer_poll_utc=bridge.last_reviewer_poll_utc or bridge.last_codex_poll_utc,
        last_worktree_hash=bridge.last_worktree_hash,
        pending_total=bridge.pending_total,
        unresolved_count=active_run.unresolved_count,
        current_instruction=truncate_status_text(active_run.current_instruction, 280),
        open_findings=truncate_status_text(active_run.open_findings, 280),
        claude_status=truncate_status_text(bridge.claude_status, 220),
        claude_ack=truncate_status_text(bridge.claude_ack, 220),
        implementer_status=truncate_status_text(
            bridge.implementer_status or bridge.claude_status,
            220,
        ),
        implementer_ack=truncate_status_text(
            bridge.implementer_ack or bridge.claude_ack,
            220,
        ),
        codex_status=state.agent_status("codex"),
        claude_lane_status=state.agent_status("claude"),
        operator_status=state.agent_status("operator"),
        source_run_url=active_run.source_run_url,
        approval_mode=state.approvals.mode,
        approval_summary=state.approvals.summary,
        next_actions=list(active_run.next_actions),
    ).to_dict()


def alert_view(payload: dict[str, Any] | ControlState) -> dict[str, Any]:
    compact = compact_view(payload)
    severity = "info"
    if compact["review_bridge_state"] == "stale" or compact["controller_risk"] == "high":
        severity = "warning"
    if compact["controller_phase"] in {"failed", "blocked"}:
        severity = "critical"
    reasons: list[str] = []
    if compact["review_bridge_state"] != "fresh":
        reasons.append(f"review bridge is {compact['review_bridge_state']}")
    if compact["unresolved_count"]:
        reasons.append(f"{compact['unresolved_count']} unresolved control items")
    if compact["pending_total"]:
        reasons.append(f"{compact['pending_total']} pending review packets")
    if not reasons:
        reasons.append("controller and review state are currently aligned")
    return AlertMobileStatusProjection(
        severity=severity,
        summary=str(compact["headline"]),
        approval_mode=str(compact["approval_mode"]),
        approval_summary=str(compact["approval_summary"]),
        why=reasons,
        current_instruction=str(compact["current_instruction"]),
        next_actions=string_rows(compact.get("next_actions")),
        commands=[
            "python3 dev/scripts/devctl.py mobile-status --view compact --format md",
            "python3 dev/scripts/devctl.py phone-status --view trace --format md",
            "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md",
        ],
    ).to_dict()


def actions_view(payload: dict[str, Any] | ControlState) -> dict[str, Any]:
    controller_payload = payload if isinstance(payload, dict) else {}
    controller_actions = phone_actions_view(_controller_payload(controller_payload))
    operator_actions = [
        OperatorActionPayload(
            name="refresh-mobile-status",
            command="python3 dev/scripts/devctl.py mobile-status --view compact --format md",
            kind="read",
        ),
        OperatorActionPayload(
            name="review-status",
            command="python3 dev/scripts/devctl.py review-channel --action status --terminal none --format md",
            kind="read",
        ),
        OperatorActionPayload(
            name="phone-trace",
            command="python3 dev/scripts/devctl.py phone-status --view trace --format md",
            kind="read",
        ),
    ]
    nested_actions = controller_actions.get("operator_actions")
    operator_actions.extend(operator_action_rows(nested_actions))
    compact = compact_view(payload)
    return ActionsMobileStatusProjection(
        summary=str(compact["headline"]),
        approval_mode=str(compact["approval_mode"]),
        approval_summary=str(compact["approval_summary"]),
        next_actions=string_rows(compact.get("next_actions")),
        operator_actions=operator_actions,
    ).to_dict()


def view_payload(
    payload: dict[str, Any] | ControlState,
    view: str | MobileStatusView,
) -> dict[str, Any]:
    selected_view = parse_mobile_status_view(view)
    if selected_view is MobileStatusView.FULL:
        return payload if isinstance(payload, dict) else payload.to_dict()
    if selected_view is MobileStatusView.ALERT:
        return alert_view(payload)
    if selected_view is MobileStatusView.ACTIONS:
        return actions_view(payload)
    return compact_view(payload)
