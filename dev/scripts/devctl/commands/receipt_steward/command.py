"""CLI dispatcher for `devctl receipt-steward` (A38.2 S2).

Mirrors the bypass command package: `add_parser` registers four typed
sub-actions (audit, audit-recent, audit-gap-report, claim) and `run`
dispatches on `args.receipt_steward_action`.
"""

from __future__ import annotations

import json
from typing import Any

from ...common import emit_output, write_output
from .audit import add_audit_parser, audit_action, render_audit_markdown
from .audit_gap_report import (
    add_audit_gap_report_parser,
    audit_gap_report_action,
    render_audit_gap_report_markdown,
)
from .audit_recent import (
    add_audit_recent_parser,
    audit_recent_action,
    render_audit_recent_markdown,
)
from .claim import add_claim_parser, claim_action, render_claim_markdown


def add_parser(sub) -> None:
    """Register the `receipt-steward` subcommand."""
    parser = sub.add_parser(
        "receipt-steward",
        help=(
            "Audit FeatureProofReceipt coverage per slice via the typed "
            "receipt-steward role (READ-only, GOVERNANCE)."
        ),
    )
    action_sub = parser.add_subparsers(dest="receipt_steward_action", required=True)
    add_audit_parser(action_sub)
    add_audit_recent_parser(action_sub)
    add_audit_gap_report_parser(action_sub)
    add_claim_parser(action_sub)


def run(args: Any) -> int:
    """Dispatch one receipt-steward action."""
    action = str(getattr(args, "receipt_steward_action", "") or "").strip()
    fmt = str(getattr(args, "format", "json") or "json").strip()
    if action == "audit":
        report, rc = audit_action(args)
        markdown_renderer = render_audit_markdown
    elif action == "audit-recent":
        report, rc = audit_recent_action(args)
        markdown_renderer = render_audit_recent_markdown
    elif action == "audit-gap-report":
        report, rc = audit_gap_report_action(args)
        markdown_renderer = render_audit_gap_report_markdown
    elif action == "claim":
        report, rc = claim_action(args)
        markdown_renderer = render_claim_markdown
    else:
        report, rc = (
            {
                "command": "receipt-steward",
                "action": action,
                "ok": False,
                "error": "unknown_receipt_steward_action",
            },
            1,
        )
        markdown_renderer = _render_unknown_action_markdown

    if fmt == "json":
        output = json.dumps(report, indent=2, sort_keys=True)
    else:
        output = markdown_renderer(report)
    emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )
    return rc


def _render_unknown_action_markdown(report: dict[str, object]) -> str:
    return (
        "# devctl receipt-steward\n\n"
        f"- ok: {report.get('ok')}\n"
        f"- action: {report.get('action')}\n"
        f"- error: {report.get('error')}\n"
    )


__all__ = ["add_parser", "run"]
