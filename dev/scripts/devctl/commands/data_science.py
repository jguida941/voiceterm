"""devctl data-science command implementation."""

from __future__ import annotations

import json
from pathlib import Path

from ..common import emit_output, pipe_output, write_output
from ..data_science.metrics import run_data_science_snapshot


def run(args) -> int:
    """Build one data-science snapshot from devctl telemetry + swarm history."""
    report = run_data_science_snapshot(
        trigger_command="devctl:data-science",
        output_root=str(args.output_root),
        event_log_path=str(args.event_log) if args.event_log else None,
        swarm_root=str(args.swarm_root) if args.swarm_root else None,
        benchmark_root=str(args.benchmark_root) if args.benchmark_root else None,
        watchdog_root=str(args.watchdog_root) if args.watchdog_root else None,
        governance_review_log=(
            str(args.governance_review_log) if args.governance_review_log else None
        ),
        max_events=int(args.max_events),
        max_swarm_files=int(args.max_swarm_files),
        max_benchmark_files=int(args.max_benchmark_files),
        max_watchdog_rows=int(args.max_watchdog_rows),
        max_governance_review_rows=int(args.max_governance_review_rows),
    )

    output = (
        json.dumps(report, indent=2)
        if args.format == "json"
        else (
            (report.get("paths") or {}).get("summary_md")
            and Path(str(report["paths"]["summary_md"])).read_text(encoding="utf-8")
        )
    )
    if not isinstance(output, str):
        output = json.dumps(report, indent=2)

    json_payload = json.dumps(report, indent=2)
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
    return 0
