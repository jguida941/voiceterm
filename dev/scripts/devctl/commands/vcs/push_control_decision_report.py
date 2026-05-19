"""Rendering for governed push controller-obedience failures."""

from __future__ import annotations

import json
from typing import Any

from ...common import emit_output, pipe_output, write_output


def emit_push_control_decision_report(args: Any, report: dict[str, object]) -> None:
    output = json.dumps(report, indent=2, sort_keys=True)
    if str(getattr(args, "format", "json") or "json") == "md":
        output = render_push_control_decision_report(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
        piper=pipe_output,
    )


def render_push_control_decision_report(report: dict[str, object]) -> str:
    lines = ["# devctl push", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- reason: {report.get('reason')}")
    obedience = report.get("control_decision_obedience")
    if isinstance(obedience, dict):
        lines.extend(_obedience_lines(obedience))
    return "\n".join(lines)


def _obedience_lines(obedience: dict[str, object]) -> list[str]:
    lines = [
        f"- obedience_ok: {obedience.get('ok')}",
        f"- violation_count: {obedience.get('violation_count')}",
    ]
    violations = obedience.get("violations")
    if not isinstance(violations, list) or not violations:
        return lines
    return [*lines, "", "## Violations", "", *_violation_lines(violations)]


def _violation_lines(violations: list[object]) -> list[str]:
    lines: list[str] = []
    for violation in violations:
        if isinstance(violation, dict):
            lines.append(f"- {violation.get('reason')}: {violation.get('detail')}")
    return lines


__all__ = ["emit_push_control_decision_report", "render_push_control_decision_report"]
