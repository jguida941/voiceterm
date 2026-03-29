"""Parser wiring for `devctl data-science` command."""

from __future__ import annotations

import argparse


def add_data_science_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `data-science` parser."""
    data_science_cmd = sub.add_parser(
        "data-science",
        help="Build a rolling telemetry snapshot for swarm/command data science analysis",
    )
    data_science_cmd.add_argument(
        "--output-root",
        default="dev/reports/data_science",
        help="Output root for generated summary/history/chart artifacts",
    )
    data_science_cmd.add_argument(
        "--event-log",
        help="Optional event log override (default: audit policy path)",
    )
    data_science_cmd.add_argument(
        "--swarm-root",
        default="dev/reports/autonomy/swarms",
        help="Swarm summary root to scan",
    )
    data_science_cmd.add_argument(
        "--benchmark-root",
        default="dev/reports/autonomy/benchmarks",
        help="Benchmark summary root to scan",
    )
    data_science_cmd.add_argument(
        "--watchdog-root",
        default="dev/reports/autonomy/watchdog/episodes",
        help="Guarded coding episode root or JSONL file to scan",
    )
    data_science_cmd.add_argument(
        "--governance-review-log",
        default="dev/reports/governance/finding_reviews.jsonl",
        help="Governance review JSONL used to measure false-positive and cleanup rates",
    )
    data_science_cmd.add_argument(
        "--external-finding-log",
        default="dev/reports/governance/external_pilot_findings.jsonl",
        help="Imported external-finding JSONL used to measure corpus size and adjudication coverage",
    )
    data_science_cmd.add_argument(
        "--max-events",
        type=int,
        default=20000,
        help="Maximum event rows sampled from JSONL",
    )
    data_science_cmd.add_argument(
        "--max-swarm-files",
        type=int,
        default=2000,
        help="Maximum swarm summary files to scan",
    )
    data_science_cmd.add_argument(
        "--max-benchmark-files",
        type=int,
        default=500,
        help="Maximum benchmark summary files to scan",
    )
    data_science_cmd.add_argument(
        "--max-watchdog-rows",
        type=int,
        default=5000,
        help="Maximum guarded coding episode rows sampled from JSONL",
    )
    data_science_cmd.add_argument(
        "--max-governance-review-rows",
        type=int,
        default=5000,
        help="Maximum governance review rows sampled from JSONL",
    )
    data_science_cmd.add_argument(
        "--max-external-finding-rows",
        type=int,
        default=10000,
        help="Maximum imported external finding rows sampled from JSONL",
    )
    data_science_cmd.add_argument("--format", choices=["json", "md"], default="md")
    data_science_cmd.add_argument("--output")
    data_science_cmd.add_argument("--json-output")
    data_science_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    data_science_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
