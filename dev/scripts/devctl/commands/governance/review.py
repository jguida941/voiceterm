"""devctl governance-review command implementation."""

from __future__ import annotations

from ...governance_review_log import (
    append_governance_review_row,
    build_governance_review_report,
    build_governance_review_row,
    resolve_governance_review_log_path,
    resolve_governance_review_summary_root,
)
from ...governance_review_models import GovernanceReviewInput
from ...governance_review_render import (
    render_governance_review_markdown,
    write_governance_review_summary,
)
from .common import emit_governance_command_output, render_governance_value_error


def run(args) -> int:
    """Record one governance finding review row or render the current summary."""
    try:
        log_path = resolve_governance_review_log_path(getattr(args, "log_path", None))
        summary_root = resolve_governance_review_summary_root(
            getattr(args, "summary_root", None)
        )
        guidance_followed_raw = getattr(args, "guidance_followed", None)
        guidance_followed = (
            None
            if guidance_followed_raw is None
            else guidance_followed_raw == "true"
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
                    finding_class=getattr(args, "finding_class", None),
                    recurrence_risk=getattr(args, "recurrence_risk", None),
                    prevention_surface=getattr(args, "prevention_surface", None),
                    waiver_reason=getattr(args, "waiver_reason", None),
                    guidance_id=getattr(args, "guidance_id", None),
                    guidance_followed=guidance_followed,
                ),
            )
            append_governance_review_row(row, log_path=log_path)
        report = build_governance_review_report(
            log_path=log_path,
            max_rows=int(getattr(args, "max_rows", 5000)),
        )
        report["paths"] = write_governance_review_summary(
            report,
            summary_root=summary_root,
        )
    except ValueError as exc:
        return render_governance_value_error(exc)

    return emit_governance_command_output(
        args,
        command="governance-review",
        json_payload=report,
        markdown_output=render_governance_review_markdown(report),
    )
