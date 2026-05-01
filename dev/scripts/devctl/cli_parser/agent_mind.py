"""Parser wiring for ``devctl agent-mind``.

Keeps the subparser definition out of ``cli.py`` so the command module
owns its own CLI surface, matching the pattern used by
``rollout_tail_parser`` and siblings.
"""

from __future__ import annotations

import argparse

from ..common_io import add_standard_output_arguments
from ..runtime.provider_registry import known_provider_help


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
        metavar="PROVIDER",
        help=(
            "Agent provider id whose mind stream should be read. Known "
            f"providers include {known_provider_help()}, and future "
            "provider ids are accepted when --sessions-root points at their "
            "JSONL traces."
        ),
    )
    cmd.add_argument(
        "--since-cursor",
        nargs="?",
        const="last_projection",
        default=None,
        help=(
            "Optional ISO-8601 timestamp. Only events strictly newer than "
            "this cursor are returned. Use the flag without a value to "
            "resume from the last persisted agent-mind projection cursor. "
            "Omit the flag to return the last --limit events regardless of age."
        ),
    )
    cmd.add_argument(
        "--session-id",
        default=None,
        help=(
            "Session id substring to match; omit to auto-detect the newest "
            "session JSONL by mtime."
        ),
    )
    cmd.add_argument(
        "--exclude-session-id",
        action="append",
        default=None,
        help=(
            "Session id substring to exclude from selection. Repeat the "
            "flag to exclude multiple caller/current sessions. When "
            "DEVCTL_CALLER_AGENT and DEVCTL_CALLER_SESSION_ID identify a "
            "same-provider caller, that session is excluded automatically."
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
