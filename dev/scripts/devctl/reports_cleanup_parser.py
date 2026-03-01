"""Parser wiring for `devctl reports-cleanup` arguments."""

from __future__ import annotations

import argparse

from .reports_retention import (
    DEFAULT_REPORTS_ROOT_RELATIVE,
    DEFAULT_RETENTION_KEEP_RECENT,
    DEFAULT_RETENTION_MAX_AGE_DAYS,
)


def add_reports_cleanup_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `reports-cleanup` command parser."""
    cleanup_cmd = subparsers.add_parser(
        "reports-cleanup",
        help="Prune stale dev/reports run artifacts with retention safeguards",
    )
    cleanup_cmd.add_argument(
        "--reports-root",
        default=str(DEFAULT_REPORTS_ROOT_RELATIVE),
        help="Repository-relative reports root (default: dev/reports)",
    )
    cleanup_cmd.add_argument(
        "--max-age-days",
        type=int,
        default=DEFAULT_RETENTION_MAX_AGE_DAYS,
        help="Delete candidates older than this age in days (default: 30)",
    )
    cleanup_cmd.add_argument(
        "--keep-recent",
        type=int,
        default=DEFAULT_RETENTION_KEEP_RECENT,
        help="Always keep this many newest run directories per managed subroot (default: 10)",
    )
    cleanup_cmd.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt before deletion",
    )
    cleanup_cmd.add_argument("--dry-run", action="store_true")
    cleanup_cmd.add_argument("--format", choices=["json", "md"], default="md")
    cleanup_cmd.add_argument("--output")
    cleanup_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    cleanup_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
