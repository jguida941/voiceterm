"""Projection/render helpers for `devctl phone-status`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _truncate(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _controller(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("controller")
    return value if isinstance(value, dict) else {}


def _loop(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("loop")
    return value if isinstance(value, dict) else {}


def _source_run(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("source_run")
    return value if isinstance(value, dict) else {}


def _terminal(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("terminal")
    return value if isinstance(value, dict) else {}


def _terminal_trace(payload: dict[str, Any]) -> list[str]:
    terminal = _terminal(payload)
    trace = terminal.get("trace")
    if not isinstance(trace, list):
        return []
    rows: list[str] = []
    for row in trace:
        text = str(row).strip()
        if text:
            rows.append(text)
    return rows


def _next_actions(payload: dict[str, Any]) -> list[str]:
    loop_payload = _loop(payload)
    rows = loop_payload.get("next_actions")
    if not isinstance(rows, list):
        return []
    actions: list[str] = []
    for row in rows:
        text = str(row).strip()
        if text:
            actions.append(text)
    return actions


def compact_view(payload: dict[str, Any]) -> dict[str, Any]:
    controller = _controller(payload)
    loop_payload = _loop(payload)
    source_run = _source_run(payload)
    terminal = _terminal(payload)
    return {
        "schema_version": 1,
        "view": "compact",
        "phase": str(payload.get("phase") or "unknown"),
        "reason": str(payload.get("reason") or "unknown"),
        "plan_id": str(controller.get("plan_id") or ""),
        "controller_run_id": str(controller.get("controller_run_id") or ""),
        "branch_base": str(controller.get("branch_base") or ""),
        "mode_effective": str(controller.get("mode_effective") or "unknown"),
        "resolved": bool(controller.get("resolved", False)),
        "rounds_completed": int(controller.get("rounds_completed") or 0),
        "max_rounds": int(controller.get("max_rounds") or 0),
        "tasks_completed": int(controller.get("tasks_completed") or 0),
        "max_tasks": int(controller.get("max_tasks") or 0),
        "latest_working_branch": str(controller.get("latest_working_branch") or ""),
        "unresolved_count": int(loop_payload.get("unresolved_count") or 0),
        "risk": str(loop_payload.get("risk") or "unknown"),
        "source_run_url": str(source_run.get("run_url") or ""),
        "source_run_id": source_run.get("run_id"),
        "source_run_sha": source_run.get("run_sha"),
        "trace_lines": len(_terminal_trace(payload)),
        "draft_preview": _truncate(terminal.get("draft_text"), 240),
        "next_actions": _next_actions(payload)[:5],
        "warnings_count": len(payload.get("warnings") or []),
        "errors_count": len(payload.get("errors") or []),
    }


def trace_view(payload: dict[str, Any]) -> dict[str, Any]:
    controller = _controller(payload)
    terminal = _terminal(payload)
    return {
        "schema_version": 1,
        "view": "trace",
        "controller_run_id": str(controller.get("controller_run_id") or ""),
        "phase": str(payload.get("phase") or "unknown"),
        "reason": str(payload.get("reason") or "unknown"),
        "trace": _terminal_trace(payload),
        "draft_text": str(terminal.get("draft_text") or ""),
        "auto_send": bool(terminal.get("auto_send", False)),
    }


def actions_view(payload: dict[str, Any]) -> dict[str, Any]:
    controller = _controller(payload)
    return {
        "schema_version": 1,
        "view": "actions",
        "controller_run_id": str(controller.get("controller_run_id") or ""),
        "phase": str(payload.get("phase") or "unknown"),
        "reason": str(payload.get("reason") or "unknown"),
        "next_actions": _next_actions(payload),
        "operator_actions": [
            {
                "name": "refresh-status",
                "command": "python3 dev/scripts/devctl.py phone-status --view compact --format md",
                "kind": "read",
            },
            {
                "name": "dispatch-report-only",
                "command": "python3 dev/scripts/devctl.py triage-loop --mode report-only --format md",
                "kind": "write",
                "guard": "policy-gated",
            },
            {
                "name": "controller-report",
                "command": "python3 dev/scripts/devctl.py autonomy-report --format md",
                "kind": "read",
            },
        ],
    }


def view_payload(payload: dict[str, Any], view: str) -> dict[str, Any]:
    if view == "full":
        return payload
    if view == "trace":
        return trace_view(payload)
    if view == "actions":
        return actions_view(payload)
    return compact_view(payload)


def _render_view_markdown(view_payload: dict[str, Any], view: str) -> str:
    if view == "trace":
        lines = ["## Trace View", ""]
        lines.append(f"- phase: {view_payload.get('phase')}")
        lines.append(f"- reason: {view_payload.get('reason')}")
        lines.append(f"- controller_run_id: {view_payload.get('controller_run_id')}")
        lines.append("")
        lines.append("### Terminal Trace")
        lines.append("")
        trace = view_payload.get("trace")
        if isinstance(trace, list) and trace:
            for row in trace:
                lines.append(f"- {row}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append("### Draft")
        lines.append("")
        lines.append(str(view_payload.get("draft_text") or "(none)"))
        return "\n".join(lines)

    if view == "actions":
        lines = ["## Actions View", ""]
        lines.append(f"- phase: {view_payload.get('phase')}")
        lines.append(f"- reason: {view_payload.get('reason')}")
        lines.append("")
        lines.append("### Loop Next Actions")
        lines.append("")
        next_actions = view_payload.get("next_actions")
        if isinstance(next_actions, list) and next_actions:
            for row in next_actions:
                lines.append(f"- {row}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append("### Operator Actions")
        lines.append("")
        operator_actions = view_payload.get("operator_actions")
        if isinstance(operator_actions, list) and operator_actions:
            for row in operator_actions:
                if not isinstance(row, dict):
                    continue
                label = str(row.get("name") or "action")
                command = str(row.get("command") or "")
                kind = str(row.get("kind") or "unknown")
                guard = str(row.get("guard") or "none")
                lines.append(f"- {label} ({kind}, guard={guard}): `{command}`")
        else:
            lines.append("- none")
        return "\n".join(lines)

    compact = view_payload if view == "compact" else compact_view(view_payload)
    lines = ["## Compact View", ""]
    lines.append(f"- phase: {compact.get('phase')}")
    lines.append(f"- reason: {compact.get('reason')}")
    lines.append(f"- plan_id: {compact.get('plan_id')}")
    lines.append(f"- run_id: {compact.get('controller_run_id')}")
    lines.append(f"- branch: {compact.get('branch_base')}")
    lines.append(f"- mode: {compact.get('mode_effective')}")
    lines.append(f"- resolved: {compact.get('resolved')}")
    lines.append(
        f"- progress: rounds {compact.get('rounds_completed')}/{compact.get('max_rounds')} | "
        f"tasks {compact.get('tasks_completed')}/{compact.get('max_tasks')}"
    )
    lines.append(f"- unresolved_count: {compact.get('unresolved_count')}")
    lines.append(f"- risk: {compact.get('risk')}")
    lines.append(f"- source_run_url: {compact.get('source_run_url') or 'n/a'}")
    lines.append(f"- trace_lines: {compact.get('trace_lines')}")
    lines.append("")
    lines.append("### Next Actions")
    lines.append("")
    next_actions = compact.get("next_actions")
    if isinstance(next_actions, list) and next_actions:
        for row in next_actions:
            lines.append(f"- {row}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("### Draft Preview")
    lines.append("")
    lines.append(str(compact.get("draft_preview") or "(none)"))
    return "\n".join(lines)


def render_report_markdown(report: dict[str, Any]) -> str:
    lines = ["# devctl phone-status", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- input: {report.get('input_path')}")
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
        lines.append(_render_view_markdown(view_payload_value, str(report.get("view"))))
    return "\n".join(lines)


def write_projection_bundle(
    projection_dir: Path,
    payload: dict[str, Any],
) -> dict[str, str]:
    projection_dir.mkdir(parents=True, exist_ok=True)
    full_path = projection_dir / "full.json"
    compact_path = projection_dir / "compact.json"
    trace_path = projection_dir / "trace.ndjson"
    actions_path = projection_dir / "actions.json"
    latest_md_path = projection_dir / "latest.md"

    compact_payload = compact_view(payload)
    trace_payload = trace_view(payload)
    actions_payload = actions_view(payload)

    full_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    compact_path.write_text(json.dumps(compact_payload, indent=2), encoding="utf-8")
    actions_path.write_text(json.dumps(actions_payload, indent=2), encoding="utf-8")
    latest_md_path.write_text(
        _render_view_markdown(compact_payload, "compact"),
        encoding="utf-8",
    )

    trace_lines = trace_payload.get("trace")
    with trace_path.open("w", encoding="utf-8") as handle:
        if isinstance(trace_lines, list):
            for idx, row in enumerate(trace_lines, start=1):
                handle.write(
                    json.dumps(
                        {
                            "index": idx,
                            "line": str(row),
                            "controller_run_id": trace_payload.get("controller_run_id"),
                            "phase": trace_payload.get("phase"),
                            "reason": trace_payload.get("reason"),
                        }
                    )
                    + "\n"
                )

    return {
        "full_json": str(full_path),
        "compact_json": str(compact_path),
        "trace_ndjson": str(trace_path),
        "actions_json": str(actions_path),
        "latest_md": str(latest_md_path),
    }
