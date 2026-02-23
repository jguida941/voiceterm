"""Shared parser wiring for the devctl sync command."""

from __future__ import annotations

import argparse


def add_sync_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register sync parser and arguments."""
    sync_cmd = subparsers.add_parser("sync", help="Sync develop/master/current branches with guardrails")
    sync_cmd.add_argument("--remote", default="origin", help="Remote to sync against (default: origin)")
    sync_cmd.add_argument(
        "--branches",
        nargs="+",
        help="Explicit branches to sync (default: develop master plus current branch)",
    )
    sync_cmd.add_argument(
        "--no-current",
        action="store_true",
        help="Do not include the current branch in the sync set",
    )
    sync_cmd.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow sync to run with local uncommitted changes",
    )
    sync_cmd.add_argument(
        "--push",
        action="store_true",
        help="Push local-ahead branches after fast-forward pull",
    )
    sync_cmd.add_argument("--format", choices=["json", "md"], default="md")
    sync_cmd.add_argument("--output")
    sync_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    sync_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
