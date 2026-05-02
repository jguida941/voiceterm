"""Argument parser wiring for ``devctl develop``."""

from __future__ import annotations

import argparse

from ...common import add_standard_output_arguments

DEVELOP_ACTIONS = (
    "status",
    "next",
    "show",
    "start",
    "watch",
    "verify",
    "submit",
    "close",
    "rollback",
    "pause",
    "resume",
    "audit-guards",
    "audit-packets",
    "launch",
)


def add_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``develop`` subcommand."""
    cmd = sub.add_parser(
        "develop",
        help="Read-only typed development controller over MP-377 governance state",
    )
    cmd.add_argument(
        "action",
        nargs="?",
        choices=DEVELOP_ACTIONS,
        help="Controller action. Defaults to status.",
    )
    for action_name, help_text in _action_flags():
        cmd.add_argument(
            f"--{action_name}",
            dest="action_flag",
            action="store_const",
            const=action_name,
            help=help_text,
        )

    cmd.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview the controller cycle without spawning workers or mutating state.",
    )
    cmd.add_argument(
        "--fleet",
        default="default",
        help="Topology preset to render. Only `default` is implemented.",
    )
    cmd.add_argument(
        "--max-cycles",
        type=int,
        default=1,
        help="Maximum controller cycles for launch previews.",
    )
    cmd.add_argument(
        "--max-workers",
        type=int,
        default=0,
        help="Requested worker budget for future fanout planning.",
    )
    cmd.add_argument(
        "--max-packets",
        type=int,
        default=30,
        help="Maximum packet-debt rows to include in audit-packets reports.",
    )
    cmd.add_argument(
        "--drain-packets",
        "--drain",
        dest="drain_packets",
        action="store_true",
        default=False,
        help=(
            "For audit-packets only, apply deterministic plan-row ingestion for "
            "eligible packet debt and emit durable-ingestion receipts."
        ),
    )
    cmd.add_argument(
        "--actor",
        default="auto",
        help=(
            "Actor whose packet-attention lane /develop should inspect. "
            "Use `auto` to resolve from typed caller or packet-attention state."
        ),
    )
    cmd.add_argument(
        "--slice-id",
        default="",
        help="Optional development slice id for lifecycle preview actions.",
    )
    cmd.add_argument(
        "--packet-id",
        default="",
        help="Optional packet id for /develop show and lifecycle previews.",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md", "terminal"),
        default_format="md",
    )


def _action_flags() -> tuple[tuple[str, str], ...]:
    return (
        ("status", "Render controller status."),
        ("next", "Select the next typed development slice."),
        ("show", "Render the typed read command for a slice or packet."),
        ("start", "Preview slice claim / lease prerequisites."),
        ("watch", "Preview live packet/sync watch commands for the actor."),
        ("verify", "Render required verification commands for the slice."),
        ("submit", "Preview governed handoff / submit prerequisites."),
        ("close", "Preview retrospective learning closure for the slice."),
        ("rollback", "Preview typed rollback / recovery prerequisites."),
        ("pause", "Render a typed pause request without mutating state."),
        ("resume", "Render a typed resume request without mutating state."),
        ("audit-guards", "Show guard/probe learning checks for this loop."),
        ("audit-packets", "Show packet carry-forward durable-ingestion debt."),
        ("launch", "Run one read-only controller cycle report."),
    )


__all__ = ["DEVELOP_ACTIONS", "add_parser"]
