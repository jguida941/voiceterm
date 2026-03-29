"""Parser registration for reusable-platform contract surfaces."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


def add_platform_contracts_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `platform-contracts` parser."""
    cmd = sub.add_parser(
        "platform-contracts",
        help=(
            "Render the reusable AI-governance platform contract blueprint "
            "for adopters, frontends, and repo-pack authors"
        ),
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md"))
