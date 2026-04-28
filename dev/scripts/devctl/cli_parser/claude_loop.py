"""Argparse wiring for the read-only Claude loop surface."""

from __future__ import annotations

import argparse


def add_claude_loop_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``claude-loop`` subcommand."""
    cmd = sub.add_parser(
        "claude-loop",
        help="Read-only Claude loop state backed by DashboardSnapshot v3",
    )
    cmd.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="Output format.",
    )
    cmd.add_argument(
        "--follow",
        action="store_true",
        default=False,
        help="Poll and re-render Claude-loop snapshots until interrupted.",
    )
    cmd.add_argument(
        "--interval",
        default="5",
        help="Polling interval for --follow, for example 1, 500ms, or 5s.",
    )
    cmd.add_argument(
        "--max-follow-snapshots",
        type=int,
        default=None,
        help="Stop --follow after this many snapshots; useful for probes.",
    )
    cmd.add_argument(
        "--repo-root",
        default=None,
        help="Optional repo root override.",
    )


__all__ = ["add_claude_loop_parser"]
