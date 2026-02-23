"""Shared parser setup helpers for `devctl cli.py`.

This keeps `cli.py` focused on dispatch wiring while preserving a single
source of truth for command argument definitions.
"""

from __future__ import annotations

import argparse

from .cli_parser_quality import add_quality_parsers
from .cli_parser_release import add_release_parsers
from .cli_parser_reporting import add_reporting_parsers


def add_standard_parsers(
    sub: argparse._SubParsersAction,
    *,
    default_ci_limit: int,
    default_mem_iterations: int,
    default_mutants_timeout: int,
    default_mutation_threshold: float,
) -> None:
    """Register the core command parsers handled directly by `cli.py`."""
    add_quality_parsers(
        sub,
        default_mem_iterations=default_mem_iterations,
        default_mutants_timeout=default_mutants_timeout,
        default_mutation_threshold=default_mutation_threshold,
    )
    add_release_parsers(sub)
    add_reporting_parsers(sub, default_ci_limit=default_ci_limit)
