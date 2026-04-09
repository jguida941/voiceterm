"""devctl discover command -- static capability inventory surface.

Renders the SystemCatalog as a typed JSON or markdown inventory so
agents and operators can see what commands, guards, probes, and surfaces
exist without parsing docs or guessing. Supports --filter to narrow
the output to a specific category.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from ...common import emit_output, write_output
from ...governance.system_catalog import build_system_catalog
from ...time_utils import utc_timestamp


def add_parser(sub) -> None:
    """Register the ``discover`` subcommand on *sub*."""
    from ...common import add_standard_output_arguments

    cmd = sub.add_parser(
        "discover",
        help="Static capability inventory (commands, guards, probes, surfaces)",
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md"))
    cmd.add_argument(
        "--filter",
        default="all",
        help=(
            "Filter category: all, commands, guards, probes, surfaces, bootstrap_commands, "
            "or guards-for-file:<path> for file-specific guard list"
        ),
    )
    cmd.add_argument(
        "--dispatch",
        nargs="*",
        default=None,
        metavar="PATH",
        help=(
            "Show AgentDispatchPacket for changed paths. "
            "With no paths, uses current git diff."
        ),
    )


def run(args) -> int:
    """Build and emit the SystemCatalog or AgentDispatchPacket."""
    dispatch_paths = getattr(args, "dispatch", None)
    if dispatch_paths is not None:
        return _run_dispatch(args, dispatch_paths)

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


def _run_dispatch(args, paths: list[str]) -> int:
    """Handle ``--dispatch [PATH ...]`` by resolving an AgentDispatchPacket."""
    from ...governance.system_catalog import resolve_agent_dispatch

    changed = list(paths) if paths else _git_diff_paths()
    enabled = _load_enabled_checks()
    packet = resolve_agent_dispatch(changed, enabled_checks=enabled)
    payload = asdict(packet)
    payload["command"] = "discover"
    payload["dispatch"] = True
    payload["timestamp"] = utc_timestamp()

    if args.format == "json":
        output = json.dumps(payload, indent=2)
    else:
        output = _render_dispatch_markdown(payload)

    emit_output(
        output,
        output_path=args.output,
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return 0


def _load_enabled_checks() -> object | None:
    """Load EnabledChecks from ProjectGovernance, returning None on failure."""
    try:
        from ...config import REPO_ROOT
        from ...governance.draft import scan_repo_governance

        gov = scan_repo_governance(REPO_ROOT)
        return gov.enabled_checks
    except Exception:
        return None


def _git_diff_paths() -> list[str]:
    """Return repo-relative paths from ``git diff --name-only``."""
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    paths = [p.strip() for p in result.stdout.splitlines() if p.strip()]
    if not paths:
        result2 = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        paths = [p.strip() for p in result2.stdout.splitlines() if p.strip()]
    return paths


def _render_dispatch_markdown(payload: dict) -> str:
    """Render an AgentDispatchPacket as compact markdown."""
    lines = [
        "# Agent Dispatch",
        "",
        f"Lane: **{payload.get('lane', 'unknown')}**",
        f"Bundle: `{payload.get('bundle_name', '')}`",
        f"Context: {payload.get('context_level', 'standard')}",
        "",
        "## Guards",
    ]
    for guard_id in payload.get("applicable_guards", ()):
        lines.append(f"- `{guard_id}`")
    lines.append("")
    lines.append("## Probes")
    for probe_id in payload.get("applicable_probes", ()):
        lines.append(f"- `{probe_id}`")
    if payload.get("preflight_commands"):
        lines.append("")
        lines.append("## Preflight")
        for command in payload["preflight_commands"]:
            lines.append(f"- `{command}`")
    if payload.get("changed_paths"):
        lines.append("")
        lines.append(f"Changed paths: {len(payload['changed_paths'])}")
    return "\n".join(lines)


def _run_guards_for_file(args, category: str) -> int:
    """Handle ``--filter guards-for-file:<path>`` by returning applicable guards."""
    from ...governance.system_catalog import filter_guards_for_file

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
        for guard_id in guard_ids:
            lines.append(f"- `{guard_id}`")
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
    if category in ("commands", "guards", "probes", "surfaces", "bootstrap_commands"):
        kept_keys.add(category)
        kept_keys.add(f"total_{category}")
    return {key: value for key, value in raw.items() if key in kept_keys}


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
    _render_category(lines, payload, "bootstrap_commands", category)
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
            read_only = " (read-only)" if item.get("read_only") else ""
            lines.append(f"- `{item['name']}`{read_only}")
        elif key == "guards":
            lines.append(f"- `{item['id']}`")
        elif key == "probes":
            lines.append(f"- `{item['id']}`")
        elif key == "bootstrap_commands":
            lines.append(f"- **{item['label']}**: `{item['command']}`")
        else:
            lines.append(f"- `{item['name']}`")
    lines.append("")
