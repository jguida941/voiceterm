"""Parser wiring for `devctl quality-policy`."""

from __future__ import annotations

import argparse

from .common_io import add_standard_output_arguments


def add_quality_policy_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `quality-policy` parser."""
    quality_policy_cmd = sub.add_parser(
        "quality-policy",
        help="Resolve and render the active quality-policy configuration",
    )
    quality_policy_cmd.add_argument(
        "--quality-policy",
        help=(
            "Optional repo policy JSON file to resolve "
            "(defaults to dev/config/devctl_repo_policy.json or "
            "DEVCTL_QUALITY_POLICY)."
        ),
    )
    add_standard_output_arguments(
        quality_policy_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )
