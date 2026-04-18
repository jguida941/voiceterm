"""Parser wiring for ``devctl pipeline``.

Mirrors the pattern used by ``rollout_tail_parser``: this module owns
the CLI surface for the ``pipeline`` subcommand so ``cli.py`` only has
to call one ``add_pipeline_parser(sub)`` during parser construction.
"""

from __future__ import annotations

import argparse

from ..common_io import add_standard_output_arguments


SUPPORTED_ACTIONS: tuple[str, ...] = (
    "status",
    "recover",
    "abandon",
    "refresh-authorization",
)


def add_pipeline_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``pipeline`` subcommand on ``sub``."""
    cmd = sub.add_parser(
        "pipeline",
        help=(
            "Typed recovery lane for a wedged commit pipeline: inspect, "
            "rebind, refresh, or abandon the current pipeline without "
            "bypassing the governed commit surface."
        ),
    )
    cmd.add_argument(
        "--action",
        required=True,
        choices=list(SUPPORTED_ACTIONS),
        help=(
            "Recovery action. `status` is read-only; the other three "
            "mutate the pipeline artifact and write a typed receipt."
        ),
    )
    cmd.add_argument(
        "--reason",
        default="",
        help=(
            "Operator-supplied reason string. Required (min 10 chars) for "
            "--action abandon; optional but recorded for recover and "
            "refresh-authorization."
        ),
    )
    cmd.add_argument(
        "--operator-actor",
        default="operator",
        dest="operator_actor",
        help="Operator identity stamped into the typed receipt.",
    )
    cmd.add_argument(
        "--pipeline-root",
        default=None,
        dest="pipeline_root_override",
        help=(
            "Override the directory that contains commit_pipeline.json "
            "(primarily used by tests and headless fixtures)."
        ),
    )
    cmd.add_argument(
        "--receipts-root",
        default=None,
        dest="receipts_root_override",
        help=(
            "Override the directory where PipelineRecoveryReceipt files "
            "are written. Defaults to the canonical review_channel latest "
            "directory."
        ),
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("md", "json"),
        default_format="md",
    )
