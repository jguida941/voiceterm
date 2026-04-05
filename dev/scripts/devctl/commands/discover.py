"""devctl discover command -- static capability inventory surface.

Renders the SystemCatalog as a typed JSON or markdown inventory so
agents and operators can see what commands, guards, probes, and surfaces
exist without parsing docs or guessing. Supports --filter to narrow
the output to a specific category.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from ..common import emit_output, write_output
from ..governance.system_catalog import build_system_catalog
from ..time_utils import utc_timestamp


def add_parser(sub) -> None:
    """Register the ``discover`` subcommand on *sub*."""
    from ..common import add_standard_output_arguments

    cmd = sub.add_parser(
        "discover",
        help="Static capability inventory (commands, guards, probes, surfaces)",
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md"))
    cmd.add_argument(
        "--filter",
        default="all",
        help=(
            "Filter category: all, commands, guards, probes, surfaces, "
            "or guards-for-file:<path> for file-specific guard list"
        ),
    )


def run(args) -> int:
    """Build and emit the SystemCatalog."""
    category = getattr(args, "filter", None) or "all"

    if category.startswith("guards-for-file:"):
        return _run_guards_for_file(args, category)

    catalog = build_system_catalog()
    payload = _build_payload(catalog, category)

    if args.format == "json":
        output = json.dumps(payload, indent=2)
    else:
        output = _render_markdown(payload, category)

    emit_output(
        output,
        output_path=args.output,
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0


def _run_guards_for_file(args, category: str) -> int:
    """Handle ``--filter guards-for-file:<path>`` by returning applicable guards."""
    from ..governance.system_catalog import filter_guards_for_file

    file_path = category.split(":", 1)[1]
    guard_ids = filter_guards_for_file(file_path)
    payload = {
        "command": "discover",
        "timestamp": utc_timestamp(),
        "filter": category,
        "file_path": file_path,
        "guards": list(guard_ids),
        "total_guards": len(guard_ids),
    }

    if args.format == "json":
        output = json.dumps(payload, indent=2)
    else:
        lines = [f"# Guards for `{file_path}`", ""]
        for gid in guard_ids:
            lines.append(f"- `{gid}`")
        lines.append("")
        lines.append(f"Total: {len(guard_ids)}")
        output = "\n".join(lines)

    emit_output(
        output,
        output_path=args.output,
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0


def _build_payload(catalog, category: str) -> dict:
    """Build the discover payload, optionally filtered to one category."""
    raw = asdict(catalog)
    raw["command"] = "discover"
    raw["timestamp"] = utc_timestamp()
    if category == "all":
        return raw
    kept_keys = {"command", "timestamp", "schema_version"}
    if category in ("commands", "guards", "probes", "surfaces"):
        kept_keys.add(category)
        kept_keys.add(f"total_{category}")
    return {k: v for k, v in raw.items() if k in kept_keys}


def _render_markdown(payload: dict, category: str) -> str:
    """Render discover payload as compact markdown."""
    lines = ["# devctl discover", ""]
    if category == "all":
        lines.append(
            f"Commands: {payload.get('total_commands', 0)} | "
            f"Guards: {payload.get('total_guards', 0)} | "
            f"Probes: {payload.get('total_probes', 0)} | "
            f"Surfaces: {payload.get('total_surfaces', 0)}"
        )
        lines.append("")
    _render_category(lines, payload, "commands", category)
    _render_category(lines, payload, "guards", category)
    _render_category(lines, payload, "probes", category)
    _render_category(lines, payload, "surfaces", category)
    return "\n".join(lines)


def _render_category(
    lines: list[str],
    payload: dict,
    key: str,
    category: str,
) -> None:
    """Append one category section when it belongs in the output."""
    if category not in ("all", key):
        return
    items = payload.get(key, [])
    if not items:
        return
    lines.append(f"## {key.title()}")
    lines.append("")
    for item in items:
        if key == "commands":
            ro = " (read-only)" if item.get("read_only") else ""
            lines.append(f"- `{item['name']}`{ro}")
        elif key == "guards":
            langs = ", ".join(item.get("languages", ())) or "all"
            lines.append(f"- `{item['script_id']}` [{langs}]")
        elif key == "probes":
            lines.append(f"- `{item['script_id']}`")
        elif key == "surfaces":
            lines.append(f"- `{item['surface_id']}` ({item.get('authority', '')})")
    lines.append("")
