"""Parser wiring for `devctl probe-report`."""

from __future__ import annotations

import argparse

from .common_io import add_standard_output_arguments


def add_probe_report_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `probe-report` parser."""
    probe_report_cmd = sub.add_parser(
        "probe-report",
        help="Run all registered review probes and emit one aggregated report",
    )
    probe_report_cmd.add_argument(
        "--since-ref",
        help="Optional git base ref used to limit probe scanning",
    )
    probe_report_cmd.add_argument(
        "--adoption-scan",
        action="store_true",
        help=(
            "Run a full-repo onboarding scan using the current worktree instead of "
            "only changed files from git diff context"
        ),
    )
    probe_report_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    probe_report_cmd.add_argument(
        "--quality-policy",
        help=(
            "Optional repo policy JSON file used to resolve active probes "
            "(defaults to dev/config/devctl_repo_policy.json or "
            "DEVCTL_QUALITY_POLICY)."
        ),
    )
    probe_report_cmd.add_argument(
        "--output-root",
        default="dev/reports/probes",
        help="Root directory for aggregated probe artifacts",
    )
    probe_report_cmd.add_argument(
        "--emit-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write review_targets.json plus latest summary artifacts under --output-root",
    )
    add_standard_output_arguments(
        probe_report_cmd,
        format_choices=("json", "md", "terminal"),
        default_format="md",
    )
    probe_report_cmd.add_argument(
        "--json-output",
        help="Optional path for the JSON report when --format is not json",
    )
