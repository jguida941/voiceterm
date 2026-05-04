"""Read-only progress status for long-running devctl stages."""

from __future__ import annotations

import argparse
import json
from typing import Any

from ...common import add_standard_output_arguments, emit_output, pipe_output, write_output
from ...runtime.stage_progress import read_progress_snapshot


def add_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``progress-status`` subcommand."""
    cmd = sub.add_parser(
        "progress-status",
        help="Show the latest typed progress events from long-running devctl stages",
    )
    cmd.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent progress events to include",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("md", "json"),
        default_format="md",
    )


def run(args) -> int:
    """Render the latest progress snapshot."""
    payload = read_progress_snapshot(limit=max(0, int(getattr(args, "limit", 10))))
    if args.format == "json":
        output = json.dumps(payload, indent=2, sort_keys=True)
    else:
        output = render_progress_markdown(payload)
    return emit_output(
        output,
        output_path=args.output,
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
        piper=pipe_output,
    )


def render_progress_markdown(payload: dict[str, Any]) -> str:
    """Render a compact markdown progress report."""
    lines = ["# Devctl Progress", ""]
    lines.append(f"- progress_root: `{payload.get('progress_root')}`")
    latest = payload.get("latest")
    if isinstance(latest, dict):
        lines.extend(
            [
                f"- latest_status: `{latest.get('status') or 'unknown'}`",
                f"- latest_phase: `{latest.get('phase') or 'unknown'}`",
                f"- latest_command: `{latest.get('command_name') or 'unknown'}`",
                f"- latest_elapsed_seconds: `{latest.get('elapsed_seconds') or 0}`",
            ]
        )
        detail = str(latest.get("detail") or "").strip()
        if detail:
            lines.append(f"- latest_detail: {detail}")
    else:
        lines.append("- latest_status: `no_events`")

    recent = payload.get("recent")
    if not isinstance(recent, list) or not recent:
        lines.extend(["", "No progress events recorded yet."])
        return "\n".join(lines)

    lines.extend(
        [
            "",
            "## Recent Events",
            "",
            "| time | command | phase | status | elapsed | detail |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for event in recent:
        if not isinstance(event, dict):
            continue
        lines.append(
            "| {time} | `{command}` | `{phase}` | `{status}` | {elapsed} | {detail} |".format(
                time=_cell(event.get("timestamp_utc")),
                command=_cell(event.get("command_name")),
                phase=_cell(event.get("phase")),
                status=_cell(event.get("status")),
                elapsed=_cell(event.get("elapsed_seconds")),
                detail=_cell(event.get("detail")),
            )
        )
    return "\n".join(lines)


def _cell(value: object) -> str:
    text = " ".join(str("" if value is None else value).split())
    return text.replace("|", "\\|")


__all__ = ["add_parser", "render_progress_markdown", "run"]
