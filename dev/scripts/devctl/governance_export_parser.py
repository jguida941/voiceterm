"""Parser wiring for `devctl governance-export`."""

from __future__ import annotations

import argparse

from .common_io import add_standard_output_arguments


def add_governance_export_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `governance-export` parser."""
    export_cmd = sub.add_parser(
        "governance-export",
        help="Copy the portable governance stack plus fresh review artifacts into an external snapshot",
    )
    export_cmd.add_argument(
        "--quality-policy",
        help=(
            "Optional repo policy JSON file used to resolve the exported "
            "quality-policy and probe artifacts."
        ),
    )
    export_cmd.add_argument(
        "--export-base-dir",
        help=(
            "Directory that will receive the snapshot (must live outside the repo; "
            "default: ../portable_snapshot_exports)."
        ),
    )
    export_cmd.add_argument(
        "--snapshot-name",
        help="Optional snapshot directory name (default: portable_code_governance_snapshot_<date>)",
    )
    export_cmd.add_argument(
        "--since-ref",
        help="Optional git base ref used when generating the exported probe report",
    )
    export_cmd.add_argument(
        "--adoption-scan",
        action="store_true",
        help=(
            "Generate exported probe artifacts using a full current-worktree "
            "onboarding scan instead of commit-range mode"
        ),
    )
    export_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    export_cmd.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip creation of the sibling .zip archive",
    )
    export_cmd.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing snapshot directory with the same name",
    )
    add_standard_output_arguments(
        export_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )
