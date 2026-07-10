"""Parser wiring for `devctl integrations-sync` arguments."""

from __future__ import annotations

import argparse


def add_integrations_sync_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register `integrations-sync` parser and arguments."""
    cmd = subparsers.add_parser(
        "integrations-sync",
        help="Sync pinned external integration submodules with policy guards",
    )
    cmd.add_argument(
        "--source",
        action="append",
        help="Optional source key from policy (repeatable, default: all policy sources)",
    )
    cmd.add_argument(
        "--status-only",
        action="store_true",
        help="Print current source pin/status metadata without running sync/update",
    )
    cmd.add_argument(
        "--remote",
        action="store_true",
        help="Update selected sources to latest remote-tracked submodule commits",
    )
    cmd.add_argument("--dry-run", action="store_true")
    cmd.add_argument("--format", choices=["md", "json"], default="md")
    cmd.add_argument("--output")
    cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
