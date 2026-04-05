"""devctl view command -- thin presentation adapter over typed artifacts.

Dispatches to existing renderers based on --surface and --mode flags.
Owns "how to show it" only -- never execution or state mutation.

Currently supported surface/mode combinations:
  ai/slim       - token-efficient system overview for AI agents
  cli/summary   - compact CLI summary from existing surfaces
"""

from __future__ import annotations

import json
from typing import TypedDict

from ..common import emit_output, write_output
from ..governance.system_catalog import build_system_catalog
from ..time_utils import utc_timestamp


class ViewPayload(TypedDict, total=False):
    """Typed envelope for view command JSON output."""

    command: str
    surface: str
    mode: str
    timestamp: str
    commands: int
    guards: int
    probes: int
    surfaces: int


def add_parser(sub) -> None:
    """Register the ``view`` subcommand on *sub*."""
    from ..common import add_standard_output_arguments

    cmd = sub.add_parser(
        "view",
        help="Thin presentation adapter over typed artifacts",
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md"))
    cmd.add_argument(
        "--surface",
        choices=["ai", "cli", "phone"],
        default="cli",
        help="Target presentation surface (default: cli)",
    )
    cmd.add_argument(
        "--mode",
        choices=["slim", "summary"],
        default="summary",
        help="Rendering mode (default: summary)",
    )


def run(args) -> int:
    """Dispatch to the correct renderer for the requested surface/mode."""
    surface = getattr(args, "surface", "cli")
    mode = getattr(args, "mode", "summary")
    renderer = _RENDERERS.get((surface, mode))
    if renderer is None:
        output = _render_unsupported(surface, mode, args.format)
    else:
        output = renderer(args)

    emit_output(
        output,
        output_path=args.output,
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0


def _base_payload(catalog, surface: str, mode: str) -> ViewPayload:
    """Build the common payload envelope shared by all view renderers."""
    return ViewPayload(
        command="view",
        surface=surface,
        mode=mode,
        timestamp=utc_timestamp(),
        commands=catalog.total_commands,
        guards=catalog.total_guards,
        probes=catalog.total_probes,
        surfaces=catalog.total_surfaces,
    )


def _counts_line(catalog) -> str:
    """One-line counts string reused across markdown renderers."""
    return (
        f"Commands: {catalog.total_commands} | "
        f"Guards: {catalog.total_guards} | "
        f"Probes: {catalog.total_probes} | "
        f"Surfaces: {catalog.total_surfaces}"
    )


def _render_ai_slim(args) -> str:
    """Token-efficient system overview for AI agent bootstrap."""
    catalog = build_system_catalog()
    payload = _base_payload(catalog, "ai", "slim")
    payload["guard_ids"] = [g.script_id for g in catalog.guards]
    payload["probe_ids"] = [p.script_id for p in catalog.probes]
    if args.format == "json":
        return json.dumps(payload, indent=2)
    lines = [
        "# System View (AI Slim)", "", _counts_line(catalog), "",
        "## Guards", ", ".join(g.script_id for g in catalog.guards), "",
        "## Probes", ", ".join(p.script_id for p in catalog.probes),
    ]
    return "\n".join(lines)


def _render_cli_summary(args) -> str:
    """Compact CLI summary from existing surfaces."""
    catalog = build_system_catalog()
    payload = _base_payload(catalog, "cli", "summary")
    payload["command_names"] = [c.name for c in catalog.commands]
    if args.format == "json":
        return json.dumps(payload, indent=2)
    lines = ["# System View (CLI Summary)", "", _counts_line(catalog), "", "## Commands"]
    for cmd in catalog.commands:
        lines.append(f"- {cmd.name}")
    return "\n".join(lines)


def _render_unsupported(surface: str, mode: str, fmt: str) -> str:
    """Fallback for unregistered surface/mode combinations."""
    supported = sorted(f"{s}/{m}" for s, m in _RENDERERS)
    if fmt == "json":
        return json.dumps({
            "command": "view",
            "error": f"unsupported surface/mode: {surface}/{mode}",
            "supported": supported,
        }, indent=2)
    lines = [
        f"# Unsupported view: {surface}/{mode}",
        "",
        "Supported combinations:",
    ]
    for combo in supported:
        lines.append(f"- {combo}")
    return "\n".join(lines)


_RENDERERS: dict[tuple[str, str], object] = {
    ("ai", "slim"): _render_ai_slim,
    ("cli", "summary"): _render_cli_summary,
}
