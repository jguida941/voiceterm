"""Markdown / doctor / display rendering for remote-control reports.

Extracted from ``command.py`` to keep that module under the shape budget.
The ``run`` controller composes report dicts; this module owns the
display projection of those dicts and is intentionally pure (no I/O,
no state). When new typed fields land in the report (per rev_pkt_3002
axis-split work), update the renderer here so the controller stays
focused on lifecycle logic.
"""

from __future__ import annotations

from typing import Any


def doctor_payload(report: dict[str, Any]) -> dict[str, Any]:
    """Render the typed ``doctor`` block for a status/doctor lifecycle call."""
    if bool(report.get("attachment_active")):
        return {
            "status": "ready",
            "next_command": (
                "python3 dev/scripts/devctl.py remote-control heartbeat "
                "--provider claude --format md"
            ),
            "local_gui_available": False,
        }
    return {
        "status": "inactive",
        "next_command": (
            "run /project:typed-remote-control inside Claude, then confirm "
            "Claude built-in /remote-control is active"
        ),
        "local_gui_available": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render the typed report dict as the operator-facing markdown view."""
    lines = ["# devctl remote-control", ""]
    lines.append(f"- action: `{report.get('action')}`")
    lines.append(f"- ok: `{report.get('ok')}`")
    lines.append(
        f"- operator_interaction_mode: `{report.get('operator_interaction_mode')}`"
    )
    lines.append(f"- attachment_active: `{report.get('attachment_active')}`")
    lines.append(f"- attachment_expired: `{report.get('attachment_expired')}`")
    lines.append(
        f"- heartbeat_ttl_seconds: `{report.get('heartbeat_ttl_seconds')}`"
    )
    lines.append(
        f"- launcher_command: `{command_display(report.get('launcher_command'))}`"
    )
    if report.get("provider_remote_control_command"):
        lines.append(
            "- provider_remote_control_command: "
            f"`{report.get('provider_remote_control_command')}`"
        )
    if report.get("state_change"):
        lines.append(f"- state_change: `{report.get('state_change')}`")
    if report.get("artifact_path"):
        lines.append(f"- artifact_path: `{report.get('artifact_path')}`")
    doctor = report.get("doctor")
    if isinstance(doctor, dict):
        lines.extend(["", "## Doctor"])
        lines.append(f"- status: `{doctor.get('status')}`")
        lines.append(f"- next_command: `{doctor.get('next_command')}`")
    warnings = report.get("warnings") or []
    if warnings:
        lines.extend(["", "## Warnings"])
        for warning in warnings:
            lines.append(f"- {warning}")
    errors = report.get("errors") or []
    if errors:
        lines.extend(["", "## Errors"])
        for error in errors:
            lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def command_display(value: object) -> str:
    """Render a launcher-command value (list or scalar) as a single string."""
    if isinstance(value, list):
        return " ".join(str(part) for part in value)
    return str(value or "")


__all__ = ["command_display", "doctor_payload", "render_markdown"]
