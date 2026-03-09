"""Parser wiring for `devctl publication-sync`."""

from __future__ import annotations

import argparse

from .common import add_standard_output_arguments
from .publication_sync import DEFAULT_PUBLICATION_SYNC_REGISTRY_REL


def add_publication_sync_parser(sub: argparse._SubParsersAction) -> None:
    """Register the publication-sync parser."""
    cmd = sub.add_parser(
        "publication-sync",
        help="Track external publication drift against watched repo source paths",
    )
    cmd.add_argument(
        "--publication",
        help="Optional publication id filter from the tracked registry",
    )
    cmd.add_argument(
        "--registry-path",
        default=DEFAULT_PUBLICATION_SYNC_REGISTRY_REL,
        help="Publication registry JSON path",
    )
    cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Git ref compared against recorded publication source refs",
    )
    cmd.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit non-zero when stale publications are detected",
    )
    cmd.add_argument(
        "--record-source-ref",
        help="Resolve this git ref and store it as the selected publication source_ref",
    )
    cmd.add_argument(
        "--record-external-ref",
        help="Optional external site/repo ref stored with --record-source-ref",
    )
    cmd.add_argument(
        "--record-synced-at",
        help="Optional explicit UTC timestamp stored with --record-source-ref",
    )
    add_standard_output_arguments(cmd)
