"""Shared CLI parser wiring for orchestrator accountability commands."""

from __future__ import annotations

from .common import add_standard_output_arguments


def add_orchestrate_parsers(subparsers) -> None:
    """Register orchestrator accountability command parsers."""
    orchestrate_status_cmd = subparsers.add_parser(
        "orchestrate-status",
        help="Summarize active-plan and multi-agent coordination guard status",
    )
    add_standard_output_arguments(orchestrate_status_cmd)

    orchestrate_watch_cmd = subparsers.add_parser(
        "orchestrate-watch",
        help="Evaluate orchestrator SLA timers for agent updates and instruction ACKs",
    )
    orchestrate_watch_cmd.add_argument(
        "--stale-minutes",
        type=int,
        default=30,
        help="Fail when non-planned agents have no board update for this many minutes",
    )
    add_standard_output_arguments(orchestrate_watch_cmd)
