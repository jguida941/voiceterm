"""Parser registration for reusable-platform contract surfaces."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments
from ..repo_packs import active_path_config


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


def add_system_picture_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `system-picture` parser."""
    cmd = sub.add_parser(
        "system-picture",
        help=(
            "Build the generated startup/runtime/evidence reducer and optional "
            "tracked proof-ledger projection"
        ),
    )
    cmd.add_argument(
        "--output-root",
        default=active_path_config().system_picture_output_root_rel,
        help="Output root for managed latest/history system-picture artifacts",
    )
    cmd.add_argument(
        "--ledger-path",
        default=active_path_config().system_picture_ledger_rel,
        help="Tracked markdown proof-ledger projection path",
    )
    cmd.add_argument(
        "--write-ledger",
        action="store_true",
        help="Rewrite the tracked proof ledger from the generated snapshot",
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md"))
    cmd.add_argument("--json-output")


def add_system_map_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `system-map` parser."""
    cmd = sub.add_parser(
        "system-map",
        help="Render the generated SYSTEM_MAP connectivity snapshot",
    )
    cmd.add_argument(
        "--quality-policy",
        help="Optional repo policy JSON file to resolve.",
    )
    add_standard_output_arguments(cmd, format_choices=("json", "md"))
