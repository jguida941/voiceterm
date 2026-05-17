"""Parser wiring for governed exception lifecycle reports."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


def add_exceptions_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``exceptions`` subcommand."""
    cmd = sub.add_parser(
        "exceptions",
        help="Governed exception lifecycle reports, validation, and closure",
    )
    cmd.add_argument(
        "action",
        choices=("pending", "validate", "close-raw-git"),
        help="Governed exception action to run.",
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
        "--receipt-store-path",
        default="",
        help="RawGitBypassReceipt JSONL store path for `exceptions close-raw-git`.",
    )
    cmd.add_argument(
        "--current-head",
        default="",
        help="Optional HEAD used to detect stale receipt validation fixtures.",
    )
    cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview writable actions without rewriting governed state.",
    )
    cmd.add_argument(
        "--backfill",
        action="store_true",
        help="Mark `exceptions close-raw-git` as an intentional historical backfill.",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


__all__ = ["add_exceptions_parser"]
