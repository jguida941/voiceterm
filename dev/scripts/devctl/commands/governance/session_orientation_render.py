"""Renderers for ``SessionOrientationPacket``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...common import emit_output, write_output
from .session_orientation_models import SessionOrientationPacket
from .session_orientation_runner import build_session_orientation


def emit_session_orientation(args: Any, repo_root: Path, *, role: str) -> int:
    """Run the typed orientation sequence and emit a compact report."""
    packet = build_session_orientation(args, repo_root, role=role)
    if getattr(args, "format", "md") == "json":
        output = json.dumps(packet.to_dict(), indent=2, sort_keys=True)
    else:
        output = render_orientation_markdown(packet)
    pipe_code = emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    if pipe_code:
        return pipe_code
    return 0 if packet.final.get("orientation_complete") is True else 1


def render_orientation_markdown(packet: SessionOrientationPacket) -> str:
    """Render a compact human-facing session orientation report."""
    final = packet.final
    lines = [
        "# devctl session",
        "",
        f"- role: `{packet.role}`",
        f"- generated_at_utc: `{packet.generated_at_utc}`",
        f"- branch: `{packet.branch or 'unknown'}`",
        f"- head: `{_short_sha(packet.head_sha)}`",
        f"- orientation_complete: {str(final.get('orientation_complete')).lower()}",
        f"- required_action: `{final.get('required_action') or 'unknown'}`",
        f"- root_cause: {final.get('root_cause') or 'unknown'}",
    ]
    next_command = str(final.get("next_command") or "").strip()
    if next_command:
        lines.append(f"- next_command: `{next_command}`")
        lines.append(f"- next_command_source: `{final.get('next_command_source')}`")

    lines.extend(["", "## Steps", ""])
    for step in packet.steps:
        status = "ok" if step.ok else f"exit={step.exit_code}"
        parsed = "parsed" if step.parsed else "unparsed"
        lines.append(
            f"- `{step.name}`: {status}, {parsed}, {step.duration_ms}ms"
        )
        if step.error:
            lines.append(f"  - error: {step.error}")

    _append_summary(lines, "Startup", packet.startup)
    _append_summary(lines, "Session Resume", packet.session_resume)
    _append_summary(lines, "Review Status", packet.review_status)
    _append_summary(lines, "Context Graph", packet.context_graph)
    return "\n".join(lines)


def _append_summary(
    lines: list[str],
    title: str,
    summary: dict[str, object],
) -> None:
    lines.extend(["", f"## {title}", ""])
    for key, value in summary.items():
        if isinstance(value, (dict, list, tuple)):
            compact = json.dumps(value, separators=(",", ":"), sort_keys=True)
            if len(compact) > 500:
                compact = compact[:497] + "..."
            lines.append(f"- {key}: `{compact}`")
        else:
            lines.append(f"- {key}: `{value}`")


def _short_sha(value: str) -> str:
    return value[:12] if value else "unknown"

