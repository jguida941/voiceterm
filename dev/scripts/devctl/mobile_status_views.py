"""Projection/render helpers for `devctl mobile-status`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .mobile_status_projection import (
    ActionsMobileStatusProjection,
    AlertMobileStatusProjection,
    CompactMobileStatusProjection,
    MobileStatusView,
    OperatorActionPayload,
    append_bullets,
    append_operator_actions,
    operator_action_rows,
    parse_mobile_status_view,
    string_rows,
)
from .phone_status_view_support import truncate_status_text
from .phone_status_views import (
    actions_view as phone_actions_view,
)
from .phone_status_views import (
    compact_view as phone_compact_view,
)
from .runtime import ControlState, control_state_from_payload


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
        codex_last_poll_utc="",
        last_worktree_hash="",
        pending_total=0,
        unresolved_count=unresolved_count,
        current_instruction="",
        open_findings="",
        claude_status="",
        claude_ack="",
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
        codex_last_poll_utc=bridge.last_codex_poll_utc,
        last_worktree_hash=bridge.last_worktree_hash,
        pending_total=bridge.pending_total,
        unresolved_count=active_run.unresolved_count,
        current_instruction=truncate_status_text(active_run.current_instruction, 280),
        open_findings=truncate_status_text(active_run.open_findings, 280),
        claude_status=truncate_status_text(bridge.claude_status, 220),
        claude_ack=truncate_status_text(bridge.claude_ack, 220),
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


def _render_view_markdown(
    view_payload_value: dict[str, Any],
    view: str | MobileStatusView,
) -> str:
    selected_view = parse_mobile_status_view(view)
    if selected_view is MobileStatusView.FULL:
        return "\n".join(
            [
                "## Full View",
                "",
                "```json",
                json.dumps(view_payload_value, indent=2),
                "```",
            ]
        )

    if selected_view is MobileStatusView.ALERT:
        lines = ["## Alert View", ""]
        lines.append(f"- severity: {view_payload_value.get('severity')}")
        lines.append(f"- summary: {view_payload_value.get('summary')}")
        lines.append("")
        lines.append("### Why")
        lines.append("")
        append_bullets(lines, string_rows(view_payload_value.get("why")))
        lines.append("")
        lines.append("### Current Instruction")
        lines.append("")
        lines.append(str(view_payload_value.get("current_instruction") or "(none)"))
        lines.append("")
        lines.append("### Next Actions")
        lines.append("")
        append_bullets(lines, string_rows(view_payload_value.get("next_actions")))
        return "\n".join(lines)

    if selected_view is MobileStatusView.ACTIONS:
        lines = ["## Actions View", ""]
        lines.append(f"- summary: {view_payload_value.get('summary')}")
        lines.append("")
        lines.append("### Next Actions")
        lines.append("")
        append_bullets(lines, string_rows(view_payload_value.get("next_actions")))
        lines.append("")
        lines.append("### Operator Actions")
        lines.append("")
        append_operator_actions(
            lines,
            operator_action_rows(view_payload_value.get("operator_actions")),
        )
        return "\n".join(lines)

    compact = view_payload_value if selected_view is MobileStatusView.COMPACT else compact_view(view_payload_value)
    lines = ["## Compact View", ""]
    lines.append(f"- headline: {compact.get('headline')}")
    lines.append(f"- plan_id: {compact.get('plan_id')}")
    lines.append(f"- controller_run_id: {compact.get('controller_run_id')}")
    lines.append(f"- controller_reason: {compact.get('controller_reason')}")
    lines.append(f"- controller_risk: {compact.get('controller_risk')}")
    lines.append(f"- review_bridge_state: {compact.get('review_bridge_state')}")
    lines.append(f"- codex_poll_state: {compact.get('codex_poll_state')}")
    lines.append(f"- codex_last_poll_utc: {compact.get('codex_last_poll_utc') or 'n/a'}")
    lines.append(f"- last_worktree_hash: {compact.get('last_worktree_hash') or 'n/a'}")
    lines.append(f"- pending_total: {compact.get('pending_total')}")
    lines.append(f"- unresolved_count: {compact.get('unresolved_count')}")
    lines.append(f"- codex_status: {compact.get('codex_status')}")
    lines.append(f"- claude_status: {compact.get('claude_lane_status')}")
    lines.append(f"- operator_status: {compact.get('operator_status')}")
    lines.append(f"- source_run_url: {compact.get('source_run_url') or 'n/a'}")
    lines.append(f"- approval_mode: {compact.get('approval_mode')}")
    lines.append(f"- approval_summary: {compact.get('approval_summary') or 'n/a'}")
    lines.append("")
    lines.append("### Current Instruction")
    lines.append("")
    lines.append(str(compact.get("current_instruction") or "(none)"))
    lines.append("")
    lines.append("### Open Findings")
    lines.append("")
    lines.append(str(compact.get("open_findings") or "(none)"))
    lines.append("")
    lines.append("### Next Actions")
    lines.append("")
    append_bullets(lines, string_rows(compact.get("next_actions")))
    return "\n".join(lines)


def render_report_markdown(report: dict[str, Any]) -> str:
    lines = ["# devctl mobile-status", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- phone_input: {report.get('phone_input_path')}")
    lines.append(f"- review_channel_path: {report.get('review_channel_path')}")
    lines.append(f"- bridge_path: {report.get('bridge_path')}")
    lines.append(f"- review_status_dir: {report.get('review_status_dir')}")
    lines.append(f"- approval_mode: {report.get('approval_mode')}")
    lines.append(f"- view: {report.get('view')}")
    lines.append(f"- timestamp: {report.get('timestamp')}")
    if report.get("projection_dir"):
        lines.append(f"- projection_dir: {report.get('projection_dir')}")
    lines.append("")

    warnings = report.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.append("## Warnings")
        lines.append("")
        for row in warnings:
            lines.append(f"- {row}")
        lines.append("")

    errors = report.get("errors")
    if isinstance(errors, list) and errors:
        lines.append("## Errors")
        lines.append("")
        for row in errors:
            lines.append(f"- {row}")
        lines.append("")

    view_payload_value = report.get("view_payload")
    if isinstance(view_payload_value, dict):
        lines.append(
            _render_view_markdown(
                view_payload_value,
                parse_mobile_status_view(str(report.get("view"))),
            )
        )
    return "\n".join(lines)


def write_projection_bundle(
    projection_dir: Path,
    payload: dict[str, Any],
) -> dict[str, str]:
    projection_dir.mkdir(parents=True, exist_ok=True)
    full_path = projection_dir / "full.json"
    compact_path = projection_dir / "compact.json"
    alert_path = projection_dir / "alert.json"
    actions_path = projection_dir / "actions.json"
    latest_md_path = projection_dir / "latest.md"

    compact_payload = compact_view(payload)
    alert_payload = alert_view(payload)
    actions_payload = actions_view(payload)

    full_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    compact_path.write_text(json.dumps(compact_payload, indent=2), encoding="utf-8")
    alert_path.write_text(json.dumps(alert_payload, indent=2), encoding="utf-8")
    actions_path.write_text(json.dumps(actions_payload, indent=2), encoding="utf-8")
    latest_md_path.write_text(
        _render_view_markdown(compact_payload, MobileStatusView.COMPACT),
        encoding="utf-8",
    )

    return {
        "full_json": str(full_path),
        "compact_json": str(compact_path),
        "alert_json": str(alert_path),
        "actions_json": str(actions_path),
        "latest_md": str(latest_md_path),
    }
