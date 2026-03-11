"""devctl governance-review command implementation."""

from __future__ import annotations

import json

from ..common import emit_output, pipe_output, write_output
from ..governance_review_log import (
    append_governance_review_row,
    build_governance_review_report,
    build_governance_review_row,
    resolve_governance_review_log_path,
    resolve_governance_review_summary_root,
)
from ..governance_review_models import GovernanceReviewInput
from ..governance_review_render import (
    render_governance_review_markdown,
    write_governance_review_summary,
)


def run(args) -> int:
    """Record one governance finding review row or render the current summary."""
    try:
        log_path = resolve_governance_review_log_path(getattr(args, "log_path", None))
        summary_root = resolve_governance_review_summary_root(
            getattr(args, "summary_root", None)
        )
        if bool(getattr(args, "record", False)):
            row = build_governance_review_row(
                review_input=GovernanceReviewInput(
                    finding_id=getattr(args, "finding_id", None),
                    signal_type=getattr(args, "signal_type", None),
                    check_id=getattr(args, "check_id", None),
                    verdict=getattr(args, "verdict", None),
                    file_path=getattr(args, "path", None),
                    symbol=getattr(args, "symbol", None),
                    line=getattr(args, "line", None),
                    severity=getattr(args, "severity", None),
                    risk_type=getattr(args, "risk_type", None),
                    source_command=getattr(args, "source_command", None),
                    scan_mode=getattr(args, "scan_mode", None),
                    repo_name=getattr(args, "repo_name", None),
                    repo_path=getattr(args, "repo_path", None),
                    notes=getattr(args, "notes", None),
                ),
            )
            append_governance_review_row(row, log_path=log_path)
        report = build_governance_review_report(
            log_path=log_path,
            max_rows=int(getattr(args, "max_rows", 5000)),
        )
        report["paths"] = write_governance_review_summary(
            report, summary_root=summary_root
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    output = (
        json.dumps(report, indent=2)
        if args.format == "json"
        else render_governance_review_markdown(report)
    )
    pipe_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    return 0 if pipe_code == 0 else pipe_code
