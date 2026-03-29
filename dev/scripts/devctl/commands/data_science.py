"""devctl data-science command implementation."""

from __future__ import annotations

from pathlib import Path

from ..data_science.metrics import run_data_science_snapshot
from ..runtime.machine_output import ArtifactOutputOptions, emit_machine_artifact_output


def run(args) -> int:
    """Build one data-science snapshot from devctl telemetry + swarm history."""
    report = run_data_science_snapshot(
        trigger_command="devctl:data-science",
        output_root=str(args.output_root),
        event_log_path=str(args.event_log) if args.event_log else None,
        swarm_root=str(args.swarm_root) if args.swarm_root else None,
        benchmark_root=str(args.benchmark_root) if args.benchmark_root else None,
        watchdog_root=str(args.watchdog_root) if args.watchdog_root else None,
        governance_review_log=(str(args.governance_review_log) if args.governance_review_log else None),
        external_finding_log=(str(args.external_finding_log) if args.external_finding_log else None),
        max_events=int(args.max_events),
        max_swarm_files=int(args.max_swarm_files),
        max_benchmark_files=int(args.max_benchmark_files),
        max_watchdog_rows=int(args.max_watchdog_rows),
        max_governance_review_rows=int(args.max_governance_review_rows),
        max_external_finding_rows=int(args.max_external_finding_rows),
    )

    human_output = (
        (report.get("paths") or {}).get("summary_md")
        and Path(str(report["paths"]["summary_md"])).read_text(encoding="utf-8")
    )
    if not isinstance(human_output, str):
        human_output = "# Data Science Snapshot\n"

    return emit_machine_artifact_output(
        args,
        command="data-science",
        json_payload=report,
        human_output=human_output,
        options=ArtifactOutputOptions(
            summary={
                "total_events": ((report.get("event_stats") or {}).get("total_events")),
                "watchdog_episodes": ((report.get("watchdog_stats") or {}).get("total_episodes")),
            },
            json_output_path=args.json_output,
        ),
    )
