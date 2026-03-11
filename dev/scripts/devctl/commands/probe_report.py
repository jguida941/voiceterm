"""devctl probe-report command implementation."""

from __future__ import annotations

import json

from ..common import emit_output, pipe_output, write_output
from ..quality_policy import resolve_review_probe_script_ids
from ..quality_scan_mode import resolve_scan_mode
from ..review_probe_report import (
    DEFAULT_PROBE_REPORT_OUTPUT_ROOT,
    build_probe_report,
    render_probe_report_markdown,
    render_probe_report_terminal,
)


def run(args) -> int:
    """Run all registered probes and emit one aggregated review-probe report."""
    try:
        scan_mode = resolve_scan_mode(
            since_ref=getattr(args, "since_ref", None),
            head_ref=getattr(args, "head_ref", "HEAD"),
            adoption_scan=bool(getattr(args, "adoption_scan", False)),
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    policy_path = getattr(args, "quality_policy", None)
    probe_ids = resolve_review_probe_script_ids(policy_path=policy_path)
    report = build_probe_report(
        since_ref=scan_mode.since_ref,
        head_ref=scan_mode.head_ref,
        emit_artifacts=getattr(args, "emit_artifacts", True),
        output_root=getattr(args, "output_root", DEFAULT_PROBE_REPORT_OUTPUT_ROOT),
        policy_path=policy_path,
        probe_ids=probe_ids,
    )
    json_payload = json.dumps(report, indent=2)
    if args.format == "json":
        output = json_payload
    elif args.format == "terminal":
        output = render_probe_report_terminal(report)
    else:
        output = render_probe_report_markdown(report)

    pipe_code = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        additional_outputs=[(json_payload, args.json_output)] if args.json_output else None,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_code != 0:
        return pipe_code
    return 0 if report["ok"] else 1
