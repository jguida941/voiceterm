"""Read-only ``devctl develop`` controller surface."""

from __future__ import annotations

import json
from typing import Any

from ...common import emit_output, write_output
from .actions import resolve_action
from .baseline_inventory import run_baseline_inventory
from .parser import DEVELOP_ACTIONS, add_parser
from .plan_intake import run_ingest_plan
from .report import build_report
from .render import render_markdown


def run(args: Any) -> int:
    """Render a read-only DevelopmentLoopReport."""
    if resolve_action(args) == "baseline-inventory":
        return run_baseline_inventory(args)
    if resolve_action(args) in {"ingest-plan", "ingest-intent"}:
        return run_ingest_plan(args)
    report = build_report(args)
    output = json.dumps(report.to_dict(), indent=2)
    if args.format != "json":
        output = render_markdown(report)

    emit_rc = emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    if emit_rc:
        return emit_rc
    if (
        resolve_action(args) == "collaboration-profile"
        and bool(getattr(args, "validate_profile", False))
        and not report.ok
    ):
        return 1
    if _mode_chain_validation_failed(report):
        return 1
    if (
        bool(getattr(args, "enforce_final_response_gate", False))
        and not report.final_response_gate.allow_final_response
    ):
        return 1
    return 0


def _mode_chain_validation_failed(report) -> bool:
    collaboration_mode = getattr(report, "collaboration_mode", None)
    if not isinstance(collaboration_mode, dict):
        return False
    mode_chain = collaboration_mode.get("mode_chain")
    if not isinstance(mode_chain, dict):
        return False
    return bool(mode_chain.get("validation_errors"))

__all__ = ["DEVELOP_ACTIONS", "add_parser", "build_report", "run"]
