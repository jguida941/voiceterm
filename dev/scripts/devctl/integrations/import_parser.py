"""Parser wiring for `devctl integrations-import` arguments."""

from __future__ import annotations

import argparse


def add_integrations_import_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register `integrations-import` parser and arguments."""
    cmd = subparsers.add_parser(
        "integrations-import",
        help="Allowlisted selective importer from pinned integration sources",
    )
    cmd.add_argument(
        "--list-profiles",
        action="store_true",
        help="List allowlisted sources/profiles from policy and exit",
    )
    cmd.add_argument("--source", help="Policy source key (for example code-link-ide)")
    cmd.add_argument("--profile", help="Policy profile id under the selected source")
    cmd.add_argument(
        "--apply",
        action="store_true",
        help="Write imported files to destination paths (default is preview-only)",
    )
    cmd.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing existing destination files in apply mode",
    )
    cmd.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation prompts in apply mode",
    )
    cmd.add_argument(
        "--max-files",
        type=int,
        help="Optional explicit max file cap override (cannot exceed policy cap)",
    )
    cmd.add_argument("--dry-run", action="store_true")
    cmd.add_argument("--format", choices=["md", "json"], default="md")
    cmd.add_argument("--output")
    cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
