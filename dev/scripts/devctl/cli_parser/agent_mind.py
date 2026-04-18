"""Parser wiring for ``devctl agent-mind``.

Keeps the subparser definition out of ``cli.py`` so the command module
owns its own CLI surface, matching the pattern used by
``rollout_tail_parser`` and siblings.
"""

from __future__ import annotations

import argparse

from ..commands.agent_mind import SUPPORTED_AGENTS
from ..common_io import add_standard_output_arguments


def add_agent_mind_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``agent-mind`` subcommand on ``sub``.

    Flags mirror the BL-031 MVP contract: ``--agent`` picks whose mind
    stream to read, ``--since-cursor`` supports incremental polling,
    ``--limit`` caps the returned event window, and ``--project`` toggles
    the typed ``dev/reports/agent_minds/<provider>_latest.json`` artifact
    that other tools and guards consume.
    """
    cmd = sub.add_parser(
        "agent-mind",
        help=(
            "Read a peer agent's recent decision events from its rollout "
            "JSONL stream (cross-mind polling MVP for coordinated agents)"
        ),
    )
    cmd.add_argument(
        "--agent",
        required=True,
        choices=list(SUPPORTED_AGENTS),
        help="Which agent provider's mind stream to read (codex or claude)",
    )
    cmd.add_argument(
        "--since-cursor",
        default=None,
        help=(
            "Optional ISO-8601 timestamp. Only events strictly newer than "
            "this cursor are returned. Omit to return the last --limit "
            "events regardless of age."
        ),
    )
    cmd.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum decision events to return (default: 20)",
    )
    cmd.add_argument(
        "--project",
        action="store_true",
        default=False,
        help=(
            "Also write the typed slice to "
            "dev/reports/agent_minds/<provider>_latest.json so other "
            "tools and guards can consume it as a typed artifact."
        ),
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
