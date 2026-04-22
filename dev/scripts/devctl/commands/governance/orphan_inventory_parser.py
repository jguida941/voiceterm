"""Parser registration for devctl orphan-inventory."""

from __future__ import annotations

from ...common import add_standard_output_arguments

COMMAND_NAME = "orphan-inventory"
DEFAULT_SCAN_SCOPE = "bounded_local"


def add_parser(subparsers) -> None:
    """Register the ``orphan-inventory`` CLI parser."""
    cmd = subparsers.add_parser(
        COMMAND_NAME,
        help="Build a report-only bounded worktree-orphan inventory scan.",
    )

    add_scan_scope_argument(cmd)
    add_repo_path_argument(cmd)
    add_standard_output_arguments(
        cmd,
        format_choices=("md", "json"),
        default_format="md",
    )


def add_scan_scope_argument(cmd) -> None:
    cmd.add_argument(
        "--scan-scope",
        default=DEFAULT_SCAN_SCOPE,
        help="Label for the bounded scan scope (default: bounded_local).",
    )


def add_repo_path_argument(cmd) -> None:
    cmd.add_argument(
        "--repo-path",
        help="Optional external repository root to scan instead of this checkout.",
    )


__all__ = ["COMMAND_NAME", "DEFAULT_SCAN_SCOPE", "add_parser"]
