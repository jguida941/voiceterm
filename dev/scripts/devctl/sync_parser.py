"""Shared parser wiring for the devctl sync command."""

from __future__ import annotations

import argparse

from .common import add_standard_output_arguments


def add_sync_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register sync parser and arguments."""
    sync_cmd = subparsers.add_parser(
        "sync", help="Sync repo-policy development/release/current branches with guardrails"
    )
    sync_cmd.add_argument(
        "--remote", help="Remote to sync against (default: repo policy)"
    )
    sync_cmd.add_argument(
        "--branches",
        nargs="+",
        help="Explicit branches to sync (default: repo-policy development/release plus current branch)",
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
        help="Push local-ahead branches through the governed devctl push flow after fast-forward pull",
    )
    sync_cmd.add_argument(
        "--quality-policy",
        help="Override the repo governance policy path for this run",
    )
    add_standard_output_arguments(sync_cmd)


def add_push_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register push parser and arguments."""
    push_cmd = subparsers.add_parser(
        "push",
        help="Guarded repo-policy branch push with preflight and post-push audit",
    )
    push_cmd.add_argument(
        "--remote",
        help="Remote to push to (default: repo policy)",
    )
    push_cmd.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the push after validation succeeds",
    )
    push_cmd.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip the configured push preflight command",
    )
    push_cmd.add_argument(
        "--skip-post-push",
        action="store_true",
        help="Skip the configured post-push bundle after a successful push",
    )
    push_cmd.add_argument(
        "--quality-policy",
        help="Override the repo governance policy path for this run",
    )
    add_standard_output_arguments(push_cmd)
