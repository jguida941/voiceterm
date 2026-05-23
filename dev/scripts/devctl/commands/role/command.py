"""Top-level dispatcher for the `devctl role` subcommand.

Per the Phase 0.5 two-tier model accepted 2026-05-23: this CLI does
lightweight typed connectivity validation (schema + capability_class
lookup + referenced-id existence + round-trip read-after-write) and
emits a typed ``RoleConnectivityProof`` receipt. NO pytest invocation
in the CLI itself, so the surface is portable to repos with zero test
infrastructure. The full TDD discipline runs in the repo's test suite.

Actions: ``create``, ``grant-capability``, ``list``, ``show``.
"""

from __future__ import annotations

import json
from typing import Any

from ...common import add_standard_output_arguments, emit_output, write_output
from . import create as create_handler
from . import grant_capability as grant_handler
from . import list as list_handler
from . import show as show_handler


def add_parser(sub) -> None:
    """Register the ``role`` subcommand and its action sub-parsers."""
    parser = sub.add_parser(
        "role",
        help=(
            "Operator-defined typed role customization. Create, grant "
            "capabilities to, list, and show custom typed roles."
        ),
    )
    action_sub = parser.add_subparsers(dest="role_action", required=True)
    create_handler.add_create_parser(action_sub)
    grant_handler.add_grant_capability_parser(action_sub)
    list_handler.add_list_parser(action_sub)
    show_handler.add_show_parser(action_sub)


def run(args: Any) -> int:
    """Dispatch one ``devctl role <action>`` invocation."""
    action = getattr(args, "role_action", "")
    if action == "create":
        return _emit(args, *create_handler.run_create(args))
    if action == "grant-capability":
        return _emit(args, *grant_handler.run_grant_capability(args))
    if action == "list":
        return _emit(args, *list_handler.run_list(args))
    if action == "show":
        return _emit(args, *show_handler.run_show(args))
    return _emit(
        args,
        {"ok": False, "errors": [f"unknown_role_action:{action!r}"]},
        1,
    )


def _emit(args: Any, report: dict, exit_code: int) -> int:
    """Render the report via the standard output channels."""
    if getattr(args, "format", "md") == "json":
        output = json.dumps(report, indent=2, sort_keys=True)
    else:
        output = _render_markdown(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return exit_code


def _render_markdown(report: dict) -> str:
    lines = [f"# devctl role {report.get('action') or ''}", "", f"- ok: {report.get('ok')}"]
    for key in (
        "role_id",
        "action",
        "persistence_target_path",
    ):
        value = report.get(key)
        if value not in (None, ""):
            lines.append(f"- {key}: {value}")
    receipt = report.get("receipt")
    if isinstance(receipt, dict):
        lines.extend(["", "## RoleConnectivityProof"])
        for key in (
            "role_id",
            "persistence_target_path",
            "connectivity_ok",
            "schema_ok",
            "capability_class_ok",
            "workstream_ok",
            "round_trip_ok",
            "contract_id",
        ):
            value = receipt.get(key)
            if value is not None:
                lines.append(f"- {key}: {value}")
    errors = report.get("errors") or []
    if errors:
        lines.extend(["", "## Errors"])
        for err in errors:
            lines.append(f"- {err}")
    return "\n".join(lines)


__all__ = ["add_parser", "run"]
