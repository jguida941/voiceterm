"""devctl system-map command implementation."""

from __future__ import annotations

from ..commands.governance.common import emit_governance_command_output
from .system_map import build_system_map_snapshot, render_system_map_markdown


def run(args) -> int:
    """Render the generated SYSTEM_MAP connectivity snapshot."""
    snapshot = build_system_map_snapshot(
        policy_path=getattr(args, "quality_policy", None),
    )
    payload = snapshot.to_dict()
    payload["command"] = "system-map"
    return emit_governance_command_output(
        args,
        command="system-map",
        json_payload=payload,
        markdown_output=render_system_map_markdown(snapshot),
        ok=not bool(snapshot.warnings),
        summary={
            "tracked_root_count": len(snapshot.tracked_roots),
            "governed_surface_count": len(snapshot.governed_surfaces),
        },
    )
