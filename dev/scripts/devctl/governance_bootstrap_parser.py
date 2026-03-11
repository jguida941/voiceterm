"""Parser wiring for `devctl governance-bootstrap`."""

from __future__ import annotations

import argparse

from .common_io import add_standard_output_arguments


def add_governance_bootstrap_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `governance-bootstrap` parser."""
    bootstrap_cmd = sub.add_parser(
        "governance-bootstrap",
        help=(
            "Normalize a copied pilot repo into a self-contained git worktree so "
            "portable governance checks can run without broken submodule gitdir state"
        ),
    )
    bootstrap_cmd.add_argument(
        "--target-repo",
        required=True,
        help="Path to the copied target repository that will host the governance pilot",
    )
    add_standard_output_arguments(
        bootstrap_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )
