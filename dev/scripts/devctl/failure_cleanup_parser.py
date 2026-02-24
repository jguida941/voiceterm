"""Parser wiring for `devctl failure-cleanup` arguments."""

from __future__ import annotations

import argparse


def add_failure_cleanup_parser(
    subparsers: argparse._SubParsersAction,
    *,
    default_ci_limit: int,
) -> None:
    """Register the `failure-cleanup` command parser."""
    cleanup_cmd = subparsers.add_parser(
        "failure-cleanup",
        help="Delete failure triage artifacts with optional CI-green guardrails",
    )
    cleanup_cmd.add_argument(
        "--directory",
        default="dev/reports/failures",
        help="Repository-relative directory to clean (default: dev/reports/failures)",
    )
    cleanup_cmd.add_argument(
        "--allow-outside-failure-root",
        action="store_true",
        help=(
            "Allow cleanup paths outside dev/reports/failures "
            "(still restricted to dev/reports under repository root)"
        ),
    )
    cleanup_cmd.add_argument(
        "--require-green-ci",
        action="store_true",
        help="Require recent GitHub Actions runs to be green before deleting artifacts",
    )
    cleanup_cmd.add_argument(
        "--ci-limit",
        type=int,
        default=default_ci_limit,
        help="Recent CI run count to evaluate when --require-green-ci is enabled",
    )
    cleanup_cmd.add_argument(
        "--ci-branch",
        help="Filter CI gate runs to a specific head branch (used with --require-green-ci)",
    )
    cleanup_cmd.add_argument(
        "--ci-workflow",
        help="Filter CI gate runs by workflow/display title (used with --require-green-ci)",
    )
    cleanup_cmd.add_argument(
        "--ci-event",
        help="Filter CI gate runs by event type (for example push, pull_request, schedule)",
    )
    cleanup_cmd.add_argument(
        "--ci-sha",
        help="Filter CI gate runs by commit SHA prefix (used with --require-green-ci)",
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
