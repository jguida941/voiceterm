"""devctl render-surfaces command implementation."""

from __future__ import annotations

from ...governance.surfaces import (
    build_surface_report,
    render_surface_report_markdown,
)
from .common import emit_governance_command_output


def run(args) -> int:
    """Render or validate policy-owned instruction and starter surfaces."""
    write = bool(getattr(args, "write", False))
    report = build_surface_report(
        surface_ids=tuple(getattr(args, "surface", []) or ()),
        policy_path=getattr(args, "quality_policy", None),
        write=write,
        allow_missing_local_only=not write,
    )
    return emit_governance_command_output(
        args,
        command="render-surfaces",
        json_payload=report,
        markdown_output=render_surface_report_markdown(report),
        ok=bool(report.get("ok", False)),
    )
