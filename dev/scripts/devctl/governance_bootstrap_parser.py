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
    bootstrap_cmd.add_argument(
        "--no-starter-policy",
        dest="write_starter_policy",
        action="store_false",
        help="Skip writing a starter devctl repo policy file into the target repo",
    )
    bootstrap_cmd.add_argument(
        "--force-starter-policy",
        action="store_true",
        help="Overwrite an existing starter repo policy file in the target repo",
    )
    bootstrap_cmd.set_defaults(write_starter_policy=True)
    add_standard_output_arguments(
        bootstrap_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )
