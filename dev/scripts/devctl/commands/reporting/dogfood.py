"""devctl dogfood command implementation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import dogfood_governance as dogfood_governance_support
from ...common import (
    add_standard_output_arguments,
    emit_output,
    pipe_output,
    write_output,
)
from ...runtime.dogfood_log import (
    DEFAULT_MAX_DOGFOOD_ROWS,
    append_dogfood_record,
    build_dogfood_record,
    build_dogfood_report,
    resolve_dogfood_log_path,
    resolve_dogfood_summary_root,
)
from ...runtime.dogfood_models import (
    DogfoodCoverageBucket,
    DogfoodGovernanceSummary,
    DogfoodRecord,
    DogfoodRecordInput,
    DogfoodReport,
)
from ...runtime.dogfood_render import (
    render_dogfood_markdown,
    write_dogfood_summary,
)


def add_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``dogfood`` subcommand."""
    cmd = sub.add_parser(
        "dogfood",
        help="Persist and report dev-mode dogfood coverage over commands, guards, probes, and roles",
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md"), default_format="md")
    cmd.add_argument(
        "--record",
        action="store_true",
        help="Append one dogfood execution row before rendering the updated coverage report",
    )
    cmd.add_argument(
        "--report",
        action="store_true",
        help="Render the current dogfood coverage report (default behavior when --record is absent)",
    )
    cmd.add_argument(
        "--dev-mode",
        action="store_true",
        help="Required for --record so dogfood persistence stays an explicit development-only action",
    )
    cmd.add_argument("--log-path", help="Optional dogfood JSONL log override")
    cmd.add_argument("--summary-root", help="Optional dogfood summary root override")
    cmd.add_argument(
        "--max-rows",
        type=int,
        default=DEFAULT_MAX_DOGFOOD_ROWS,
        help="Maximum dogfood JSONL rows sampled when rendering the report",
    )
    cmd.add_argument(
        "--recent-limit",
        type=int,
        default=10,
        help="Maximum recent run rows and dogfood findings shown in the report",
    )
    cmd.add_argument(
        "--target-kind",
        choices=("command", "guard", "probe", "role"),
        help="Catalog family exercised by this dogfood row",
    )
    cmd.add_argument("--target-id", help="Catalog id exercised by this dogfood row")
    cmd.add_argument(
        "--status",
        choices=("passed", "failed", "blocked", "skipped"),
        help="Outcome for the recorded dogfood row",
    )
    cmd.add_argument("--campaign-id", help="Optional campaign identifier for the row")
    cmd.add_argument("--scenario-id", help="Optional scenario identifier for the row")
    cmd.add_argument("--repo-scope", help="Optional repo scope label for the row")
    cmd.add_argument("--repo-label", help="Optional repo label for the row")
    cmd.add_argument("--repo-path", help="Optional repo path override for the row")
    cmd.add_argument("--topology", help="Optional campaign topology label for the row")
    cmd.add_argument("--lane-role", help="Optional lane role for the row")
    cmd.add_argument(
        "--live-run-ref",
        nargs="+",
        help="Optional live run reference or references linked to the row",
    )
    cmd.add_argument(
        "--governance-finding-id",
        nargs="+",
        help="Optional governance finding reference or references linked to the row",
    )
    cmd.add_argument("--actor", help="Actor or lane recording the dogfood result")
    cmd.add_argument("--provider", help="Optional provider label for the recorded dogfood row")
    cmd.add_argument("--run-label", help="Optional run/session label for grouping records")
    cmd.add_argument("--source-command", help="Optional command that produced the record")
    cmd.add_argument("--artifact-path", help="Optional artifact path associated with the record")
    cmd.add_argument("--notes", help="Optional free-form note stored with the record")
    cmd.add_argument(
        "--record-governance",
        action="store_true",
        help=(
            "Append a matching signal_type=dogfood governance-review row while "
            "recording dogfood coverage"
        ),
    )
    cmd.add_argument(
        "--finding-path",
        help=(
            "Optional file path for an auto-recorded dogfood governance-review "
            "row. Defaults to the live target path when --record-governance is used."
        ),
    )
    cmd.add_argument(
        "--finding-line",
        type=int,
        help="Optional line number for the auto-recorded dogfood governance-review row",
    )
    cmd.add_argument(
        "--finding-id",
        help="Optional stable finding id override for the auto-recorded dogfood review row",
    )
    cmd.add_argument(
        "--governance-check-id",
        help="Optional check id override for the auto-recorded dogfood governance-review row",
    )
    cmd.add_argument(
        "--governance-verdict",
        choices=("confirmed_issue", "fixed", "deferred"),
        help="Optional verdict override for the auto-recorded dogfood governance-review row",
    )
    cmd.add_argument(
        "--finding-class",
        help="Finding class used when auto-recording a dogfood governance-review row",
    )
    cmd.add_argument(
        "--recurrence-risk",
        help="Recurrence-risk used when auto-recording a dogfood governance-review row",
    )
    cmd.add_argument(
        "--prevention-surface",
        help="Prevention surface used when auto-recording a dogfood governance-review row",
    )
    cmd.add_argument(
        "--finding-type",
        help="Optional finding_type recorded on the auto-recorded dogfood review row",
    )
    cmd.add_argument(
        "--severity",
        help="Optional severity for the auto-recorded dogfood governance-review row",
    )
    cmd.add_argument(
        "--risk-type",
        help="Optional risk type for the auto-recorded dogfood governance-review row",
    )
    cmd.add_argument(
        "--waiver-reason",
        help="Optional waiver reason for the auto-recorded dogfood governance-review row",
    )


def run(args) -> int:
    """Record one dogfood execution row or render the current coverage report."""
    try:
        log_path = resolve_dogfood_log_path(getattr(args, "log_path", None))
        summary_root = resolve_dogfood_summary_root(getattr(args, "summary_root", None))
        recorded_row: DogfoodRecord | None = None
        governance_row: dict[str, object] | None = None
        governance_paths: dict[str, str] | None = None
        promotion_candidate: dict[str, object] | None = None
        if bool(getattr(args, "record", False)):
            error = _record_validation_error(args)
            if error is not None:
                return _emit_error(args, error)
            recorded_row = build_dogfood_record(
                record_input=DogfoodRecordInput(
                    target_kind=getattr(args, "target_kind", None),
                    target_id=getattr(args, "target_id", None),
                    status=getattr(args, "status", None),
                    campaign_id=getattr(args, "campaign_id", None),
                    scenario_id=getattr(args, "scenario_id", None),
                    repo_scope=getattr(args, "repo_scope", None),
                    repo_label=getattr(args, "repo_label", None),
                    repo_path=getattr(args, "repo_path", None),
                    topology=getattr(args, "topology", None),
                    lane_role=getattr(args, "lane_role", None),
                    live_run_refs=tuple(getattr(args, "live_run_ref", None) or ()),
                    governance_finding_ids=tuple(
                        getattr(args, "governance_finding_id", None) or ()
                    ),
                    actor=getattr(args, "actor", None),
                    provider=getattr(args, "provider", None),
                    run_label=getattr(args, "run_label", None),
                    source_command=getattr(args, "source_command", None),
                    artifact_path=getattr(args, "artifact_path", None),
                    notes=getattr(args, "notes", None),
                )
            )
            append_dogfood_record(recorded_row, log_path=log_path)
            governance_row, governance_paths, promotion_candidate = (
                dogfood_governance_support.maybe_record_governance_closeout(
                    args,
                    recorded_row,
                )
            )
        report = build_dogfood_report(
            log_path=log_path,
            summary_root=summary_root,
            max_rows=int(getattr(args, "max_rows", DEFAULT_MAX_DOGFOOD_ROWS)),
            recent_limit=max(1, int(getattr(args, "recent_limit", 10))),
        )
        payload = _report_payload(
            report,
            recorded_row=recorded_row,
            governance_row=governance_row,
            governance_paths=governance_paths,
            promotion_candidate=promotion_candidate,
            summary_root=summary_root,
        )
    except ValueError as exc:
        return _emit_error(args, str(exc))

    rendered = render_dogfood_markdown(report)
    return emit_output(
        json.dumps(payload, indent=2) if args.format == "json" else rendered,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
        piper=pipe_output,
    )


def _record_validation_error(args) -> str | None:
    if not bool(getattr(args, "dev_mode", False)):
        return "`devctl dogfood --record` requires `--dev-mode`."
    for field_name in ("target_kind", "target_id", "status"):
        if not str(getattr(args, field_name, "") or "").strip():
            return f"`devctl dogfood --record` requires `--{field_name.replace('_', '-')}`."
    governance_error = dogfood_governance_support.governance_validation_error(args)
    if governance_error is not None:
        return governance_error
    return None


def _emit_error(args, message: str) -> int:
    payload = {
        "command": "dogfood",
        "ok": False,
        "error": message,
    }
    rendered = f"dogfood error: {message}"
    emit_output(
        json.dumps(payload, indent=2) if getattr(args, "format", "md") == "json" else rendered,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
        piper=pipe_output,
    )
    return 2


def _report_payload(
    report: DogfoodReport,
    *,
    recorded_row: DogfoodRecord | None,
    governance_row: dict[str, object] | None,
    governance_paths: dict[str, str] | None,
    promotion_candidate: dict[str, object] | None,
    summary_root: Path,
) -> dict[str, object]:
    payload = report.to_dict()
    payload["command"] = "dogfood"
    payload["coverage_rows"] = [
        _coverage_bucket_payload(bucket) for bucket in report.coverage
    ]
    payload["governance"] = _governance_summary_payload(report.governance_summary)
    if recorded_row is not None:
        payload["recorded"] = recorded_row.to_dict()
    if governance_row is not None:
        payload["governance_review"] = {
            "recorded": governance_row,
            "paths": governance_paths or {},
            "promotion_candidate_created": promotion_candidate is not None,
            "candidate_id": (
                ""
                if promotion_candidate is None
                else str(promotion_candidate.get("candidate_id") or "")
            ),
        }
    payload["paths"] = write_dogfood_summary(report, summary_root=summary_root)
    return payload


def _coverage_bucket_payload(bucket: DogfoodCoverageBucket) -> dict[str, object]:
    return {
        "target_kind": bucket.target_kind,
        "catalog_total": bucket.catalog_total,
        "covered_total": bucket.covered_total,
        "coverage_pct": bucket.coverage_pct,
        "passed_total": bucket.passed_total,
        "failed_total": bucket.failed_total,
        "blocked_total": bucket.blocked_total,
        "skipped_total": bucket.skipped_total,
        "uncovered_count": len(bucket.uncovered_ids),
        "unknown_count": len(bucket.unknown_ids),
    }


def _governance_summary_payload(
    summary: DogfoodGovernanceSummary,
) -> dict[str, object]:
    return {
        "total_findings": summary.total_findings,
        "open_findings": summary.open_findings,
        "fixed_findings": summary.fixed_findings,
        "recent_findings": list(summary.recent_findings),
    }
