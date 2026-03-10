"""Parser registration helpers for quality and docs commands."""

from __future__ import annotations

import argparse

from .builders_checks import (
    add_check_parser,
    add_mutants_parser,
    add_mutation_score_parser,
)
from ..common import add_standard_output_arguments


def add_quality_parsers(
    sub: argparse._SubParsersAction,
    *,
    default_mem_iterations: int,
    default_mutants_timeout: int,
    default_mutation_threshold: float,
) -> None:
    """Register check/check-router/mutants/mutation-score parsers."""
    add_check_parser(
        sub,
        default_mem_iterations=default_mem_iterations,
        default_mutants_timeout=default_mutants_timeout,
        default_mutation_threshold=default_mutation_threshold,
    )

    _add_check_router_parser(sub)

    add_mutants_parser(sub, default_mutants_timeout=default_mutants_timeout)
    add_mutation_score_parser(
        sub,
        default_mutation_threshold=default_mutation_threshold,
    )


def _add_check_router_parser(sub: argparse._SubParsersAction) -> None:
    router_cmd = sub.add_parser(
        "check-router",
        help="Select (and optionally run) required AGENTS bundle + risk add-ons from changed paths",
    )
    router_cmd.add_argument(
        "--since-ref",
        help="Use commit-range mode by comparing changes from this ref (e.g. origin/develop, HEAD~1)",
    )
    router_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Range-mode head ref used with --since-ref (default: HEAD)",
    )
    router_cmd.add_argument(
        "--execute",
        action="store_true",
        help="Execute the selected AGENTS bundle commands plus detected risk add-ons",
    )
    router_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print routed commands without executing (requires --execute to show step plan)",
    )
    router_cmd.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue execution after a failed routed command",
    )
    add_standard_output_arguments(router_cmd, format_choices=("text", "json", "md"))
