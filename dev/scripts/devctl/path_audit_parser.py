"""Shared parser wiring for `devctl path-audit`."""

from __future__ import annotations

import argparse


def add_path_audit_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register `path-audit` parser and arguments."""
    path_audit_cmd = subparsers.add_parser(
        "path-audit",
        help="Fail when stale legacy check-script paths still exist",
    )
    path_audit_cmd.add_argument("--format", choices=["json", "md"], default="md")
    path_audit_cmd.add_argument("--output")
    path_audit_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    path_audit_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
