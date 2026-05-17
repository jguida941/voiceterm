"""Governed exception lifecycle command."""

from __future__ import annotations

import json
from typing import Any

from ...common import emit_output, write_output
from .close_raw_git_exceptions import close_raw_git_action
from .exceptions_pending import pending_action
from .exceptions_report import render_markdown
from .exceptions_validate import validate_action


def run(args: Any) -> int:
    """Run one governed exception action."""
    report, rc = _run_action(args)
    output = json.dumps(report, indent=2, sort_keys=True)
    if getattr(args, "format", "md") != "json":
        output = render_markdown(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return rc


def _run_action(args: Any) -> tuple[dict[str, object], int]:
    action = str(getattr(args, "action", "") or "").strip()
    if action == "validate":
        return validate_action(args)
    if action == "close-raw-git":
        return close_raw_git_action(args)
    return pending_action(args)


__all__ = ["run"]
