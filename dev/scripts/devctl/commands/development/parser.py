"""Argument parser wiring for ``devctl develop``."""

from __future__ import annotations

import argparse

from ...common import add_standard_output_arguments

DEVELOP_ACTIONS = ("status", "next", "pause", "resume", "audit-guards", "launch")


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
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md", "terminal"),
        default_format="md",
    )


def _action_flags() -> tuple[tuple[str, str], ...]:
    return (
        ("status", "Render controller status."),
        ("next", "Select the next typed development slice."),
        ("pause", "Render a typed pause request without mutating state."),
        ("resume", "Render a typed resume request without mutating state."),
        ("audit-guards", "Show guard/probe learning checks for this loop."),
        ("launch", "Run one read-only controller cycle report."),
    )


__all__ = ["DEVELOP_ACTIONS", "add_parser"]
