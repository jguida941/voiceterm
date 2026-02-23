"""devctl report command implementation."""

import json

from ..common import pipe_output, write_output
from ..status_report import build_project_report, render_project_markdown


def run(args) -> int:
    """Generate a JSON or markdown report with optional CI/dev-log data."""
    report = build_project_report(
        command="report",
        include_ci=args.ci,
        ci_limit=args.ci_limit,
        include_dev_logs=getattr(args, "dev_logs", False),
        dev_root=getattr(args, "dev_root", None),
        dev_sessions_limit=getattr(args, "dev_sessions_limit", 5),
    )

    if args.format == "json":
        output = json.dumps(report, indent=2)
    else:
        output = render_project_markdown(
            report,
            title="devctl report",
            include_ci_details=False,
            ci_details_limit=0,
        )

    write_output(output, args.output)
    if args.pipe_command:
        return pipe_output(output, args.pipe_command, args.pipe_args)
    return 0
