"""Runtime for devctl orphan-inventory."""

from __future__ import annotations

from ...common import emit_output
from ...config import get_repo_root
from ...runtime.worktree_orphan_inventory import build_orphan_inventory_report
from .orphan_inventory_parser import DEFAULT_SCAN_SCOPE
from .orphan_inventory_render import render_report_output


def run(args) -> int:
    """Build and emit the bounded orphan inventory report."""
    report = build_orphan_inventory_report(
        repo_root=get_repo_root(),
        scan_scope=getattr(args, "scan_scope", DEFAULT_SCAN_SCOPE),
    )
    output = render_report_output(
        report,
        output_format=getattr(args, "format", "md"),
    )

    return emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
    )


__all__ = ["run"]
