"""Shared CLI parser wiring for orchestrator accountability commands."""

from __future__ import annotations


def add_orchestrate_parsers(subparsers) -> None:
    """Register orchestrator accountability command parsers."""
    orchestrate_status_cmd = subparsers.add_parser(
        "orchestrate-status",
        help="Summarize active-plan and multi-agent coordination guard status",
    )
    orchestrate_status_cmd.add_argument("--format", choices=["json", "md"], default="md")
    orchestrate_status_cmd.add_argument("--output")
    orchestrate_status_cmd.add_argument(
        "--pipe-command", help="Pipe report output to a command"
    )
    orchestrate_status_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )

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
    orchestrate_watch_cmd.add_argument("--format", choices=["json", "md"], default="md")
    orchestrate_watch_cmd.add_argument("--output")
    orchestrate_watch_cmd.add_argument(
        "--pipe-command", help="Pipe report output to a command"
    )
    orchestrate_watch_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )
