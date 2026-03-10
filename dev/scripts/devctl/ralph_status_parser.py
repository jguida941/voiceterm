"""Parser wiring for `devctl ralph-status` command."""

from __future__ import annotations

import argparse

from .common_io import add_standard_output_arguments


def add_ralph_status_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `ralph-status` parser."""
    p = sub.add_parser(
        "ralph-status",
        help="Ralph guardrail loop analytics and status",
    )
    add_standard_output_arguments(p)
    p.add_argument("--json-output", help="Write JSON report to a separate file")
    p.add_argument(
        "--with-charts",
        action="store_true",
        help="Generate SVG charts alongside the report",
    )
    p.add_argument(
        "--output-root",
        default=None,
        help="Output directory for charts and report artifacts",
    )
    p.add_argument(
        "--report-dir",
        default=None,
        help="Directory containing ralph-report.json files",
    )
