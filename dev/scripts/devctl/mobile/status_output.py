"""Markdown/file output helpers for `devctl mobile-status`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .status_projection import (
    MobileStatusView,
    append_bullets,
    append_operator_actions,
    operator_action_rows,
    parse_mobile_status_view,
    string_rows,
)
from .status_views import actions_view, alert_view, compact_view


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

    compact = (
        view_payload_value
        if selected_view is MobileStatusView.COMPACT
        else compact_view(view_payload_value)
    )
    lines = ["## Compact View", ""]
    lines.append(f"- headline: {compact.get('headline')}")
    lines.append(f"- plan_id: {compact.get('plan_id')}")
    lines.append(f"- controller_run_id: {compact.get('controller_run_id')}")
    lines.append(f"- controller_reason: {compact.get('controller_reason')}")
    lines.append(f"- controller_risk: {compact.get('controller_risk')}")
    lines.append(f"- review_bridge_state: {compact.get('review_bridge_state')}")
    lines.append(
        f"- reviewer_poll_state: {compact.get('reviewer_poll_state') or compact.get('codex_poll_state')}"
    )
    lines.append(
        f"- last_reviewer_poll_utc: {compact.get('last_reviewer_poll_utc') or compact.get('codex_last_poll_utc') or 'n/a'}"
    )
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
    lines.append("### Implementer")
    lines.append("")
    lines.append(str(compact.get("implementer_status") or "(none)"))
    lines.append(str(compact.get("implementer_ack") or "(no ack)"))
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

    # Per Codex rev_pkt_2406/2409/2413/2427: every projection-bundle writer
    # must use atomic-replace semantics so concurrent readers never see a
    # half-written file. Mobile may share projection_dir with the canonical
    # review-channel projection root, so racing with sync-status is real.
    from ..review_channel.projection_bundle import _atomic_write_text

    _atomic_write_text(full_path, json.dumps(payload, indent=2))
    _atomic_write_text(compact_path, json.dumps(compact_payload, indent=2))
    _atomic_write_text(alert_path, json.dumps(alert_payload, indent=2))
    _atomic_write_text(actions_path, json.dumps(actions_payload, indent=2))
    _atomic_write_text(
        latest_md_path,
        _render_view_markdown(compact_payload, MobileStatusView.COMPACT),
    )
    return {
        "full_json": str(full_path),
        "compact_json": str(compact_path),
        "alert_json": str(alert_path),
        "actions_json": str(actions_path),
        "latest_md": str(latest_md_path),
    }
