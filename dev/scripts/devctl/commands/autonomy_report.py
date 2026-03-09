"""devctl autonomy-report command implementation."""

from __future__ import annotations

import json

from ..autonomy_report_helpers import collect_report
from ..autonomy_report_render import render_markdown
from ..common import emit_output, pipe_output, write_output


def run(args) -> int:
    """Build a dated human-readable autonomy reporting bundle."""
    report, bundle_dir, _charts_dir = collect_report(args)

    summary_json = bundle_dir / "summary.json"
    summary_md = bundle_dir / "summary.md"
    summary_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary_md.write_text(render_markdown(report), encoding="utf-8")

    json_payload = json.dumps(report, indent=2)
    output = json_payload if args.format == "json" else render_markdown(report)
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
