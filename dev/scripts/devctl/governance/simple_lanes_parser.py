"""Parser registration for focused launcher and tandem validation lanes."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


def add_launcher_check_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `launcher-check` parser."""
    launcher_check_cmd = sub.add_parser(
        "launcher-check",
        help="Run focused AI guards for launcher/package Python entrypoints",
    )
    launcher_check_cmd.add_argument(
        "--since-ref",
        help="Optional git base ref used to limit the guard scan",
    )
    launcher_check_cmd.add_argument(
        "--adoption-scan",
        action="store_true",
        help="Run against the current worktree instead of diff-scoped growth checks",
    )
    launcher_check_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    launcher_check_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the delegated `check` plan without executing it",
    )
    launcher_check_cmd.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue through guard failures in the delegated `check` run",
    )
    launcher_check_cmd.add_argument(
        "--no-parallel",
        action="store_true",
        help="Run delegated AI guards sequentially instead of batched phases",
    )
    add_standard_output_arguments(
        launcher_check_cmd,
        format_choices=("text", "json", "md"),
        default_format="text",
    )


def add_launcher_probes_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `launcher-probes` parser."""
    launcher_probes_cmd = sub.add_parser(
        "launcher-probes",
        help="Run focused review probes for launcher/package Python entrypoints",
    )
    launcher_probes_cmd.add_argument(
        "--since-ref",
        help="Optional git base ref used to limit probe scanning",
    )
    launcher_probes_cmd.add_argument(
        "--adoption-scan",
        action="store_true",
        help="Run a full current-worktree onboarding scan",
    )
    launcher_probes_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    launcher_probes_cmd.add_argument(
        "--output-root",
        default="dev/reports/probes",
        help="Root directory for aggregated probe artifacts",
    )
    launcher_probes_cmd.add_argument(
        "--emit-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write probe artifacts under --output-root",
    )
    add_standard_output_arguments(
        launcher_probes_cmd,
        format_choices=("json", "md", "terminal"),
        default_format="md",
    )
    launcher_probes_cmd.add_argument(
        "--json-output",
        help="Optional path for the JSON report when --format is not json",
    )


def add_launcher_policy_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `launcher-policy` parser."""
    launcher_policy_cmd = sub.add_parser(
        "launcher-policy",
        help="Show the focused launcher/package quality policy",
    )
    add_standard_output_arguments(
        launcher_policy_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )


def add_tandem_validate_parser(sub: argparse._SubParsersAction) -> None:
    """Register the `tandem-validate` parser."""
    tandem_validate_cmd = sub.add_parser(
        "tandem-validate",
        help=(
            "Run the canonical live tandem validation lane "
            "(policy resolution, router-derived bundle/risk add-ons, final bridge/tandem guards)"
        ),
    )
    tandem_validate_cmd.add_argument(
        "--since-ref",
        help="Optional git base ref used to route against a commit range instead of the current dirty tree",
    )
    tandem_validate_cmd.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head ref used with --since-ref (default: HEAD)",
    )
    tandem_validate_cmd.add_argument(
        "--quality-policy",
        help=(
            "Optional repo policy JSON file used for router resolution and "
            "policy-aware delegated devctl commands"
        ),
    )
    tandem_validate_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Render and audit the routed command plan without executing it",
    )
    tandem_validate_cmd.add_argument(
        "--keep-going",
        action="store_true",
        help="Continue through delegated command failures instead of stopping at the first one",
    )
    add_standard_output_arguments(
        tandem_validate_cmd,
        format_choices=("json", "md"),
        default_format="md",
    )
