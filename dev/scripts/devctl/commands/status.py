"""devctl status command implementation."""

import json
import sys

from ..common import pipe_output, write_output
from ..metric_writers import append_metric
from ..status_report import build_project_report, render_project_markdown


def run(args) -> int:
    """Render a status summary from git, CI, mutation, and optional dev logs."""
    ci_requested = bool(args.ci or getattr(args, "require_ci", False))
    parallel_enabled = not getattr(args, "no_parallel", False)
    report = build_project_report(
        command="status",
        include_ci=ci_requested,
        ci_limit=args.ci_limit,
        include_dev_logs=getattr(args, "dev_logs", False),
        dev_root=getattr(args, "dev_root", None),
        dev_sessions_limit=getattr(args, "dev_sessions_limit", 5),
        parallel=parallel_enabled,
    )

    if args.format == "json":
        output = json.dumps(report, indent=2)
    elif args.format == "md":
        output = render_project_markdown(
            report,
            title="devctl status",
            include_ci_details=True,
            ci_details_limit=5,
        )
    else:
        output = json.dumps(report, indent=2)

    try:
        append_metric("status", report)
    except Exception as exc:  # pragma: no cover - fail-soft telemetry path
        print(
            f"[devctl status] warning: unable to persist metrics ({exc})",
            file=sys.stderr,
        )
    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)

    if getattr(args, "require_ci", False):
        ci_info = report.get("ci", {})
        if "error" in ci_info:
            return 2
    return 0
