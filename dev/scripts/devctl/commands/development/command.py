"""Read-only ``devctl develop`` controller surface."""

from __future__ import annotations

import json
from typing import Any

from ...common import emit_output, write_output
from .parser import DEVELOP_ACTIONS, add_parser
from .report import build_report
from .render import render_markdown


def run(args: Any) -> int:
    """Render a read-only DevelopmentLoopReport."""
    report = build_report(args)
    output = json.dumps(report.to_dict(), indent=2)
    if args.format != "json":
        output = render_markdown(report)

    return emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )


__all__ = ["DEVELOP_ACTIONS", "add_parser", "build_report", "run"]
