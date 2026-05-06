"""Parser wiring for governed exception read-only reports."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


def add_exceptions_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``exceptions`` subcommand."""
    cmd = sub.add_parser(
        "exceptions",
        help="Governed exception lifecycle reports and validation",
    )
    cmd.add_argument(
        "action",
        choices=("pending", "validate"),
        help="Read-only action to run.",
    )
    cmd.add_argument(
        "path",
        nargs="?",
        default="",
        help="JSON/JSONL file to validate for `exceptions validate`.",
    )
    cmd.add_argument(
        "--store-path",
        default="",
        help="Override governed exception lifecycle JSONL store path.",
    )
    cmd.add_argument(
        "--current-head",
        default="",
        help="Optional HEAD used to detect stale receipt validation fixtures.",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


__all__ = ["add_exceptions_parser"]
