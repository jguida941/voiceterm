"""Parser wiring for ``devctl rollout-tail``.

Keeps the subparser definition out of ``cli.py`` so the command module
owns its own CLI surface, matching the pattern used by
``probe_report_parser`` and siblings.
"""

from __future__ import annotations

import argparse

from ..commands.rollout_tail import SUPPORTED_PROVIDERS
from ..common_io import add_standard_output_arguments


def add_rollout_tail_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``rollout-tail`` subcommand on ``sub``."""
    cmd = sub.add_parser(
        "rollout-tail",
        help=(
            "Tail Codex/Claude session JSONL traces so operators can see "
            "agent internals (escalations, errors, tool calls)"
        ),
    )
    cmd.add_argument(
        "--provider",
        required=True,
        choices=list(SUPPORTED_PROVIDERS),
        help="Which CLI session trace to read (codex or claude)",
    )
    cmd.add_argument(
        "--session-id",
        default=None,
        help=(
            "Session id substring to match; omit to auto-detect the "
            "newest session JSONL by mtime."
        ),
    )
    cmd.add_argument(
        "--follow",
        action="store_true",
        default=False,
        help="Placeholder for live tail mode (not yet implemented)",
    )
    cmd.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of most-recent events to render (default: 50)",
    )
    cmd.add_argument(
        "--sessions-root",
        default=None,
        help=(
            "Optional override for the provider sessions root directory "
            "(primarily used by tests and headless environments)."
        ),
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("terminal", "json", "md"),
        default_format="md",
    )
