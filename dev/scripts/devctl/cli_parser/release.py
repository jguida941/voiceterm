"""Parser registration helpers for release/distribution commands."""

from __future__ import annotations

import argparse

from .builders_ops import add_release_parsers as add_release_distribution_parsers


def add_release_parsers(sub: argparse._SubParsersAction) -> None:
    """Register release-gates plus release/distribution parsers."""
    release_gates_cmd = sub.add_parser(
        "release-gates",
        help="Run CodeRabbit triage/preflight/Ralph release gate checks for one branch/SHA",
    )
    release_gates_cmd.add_argument(
        "--branch",
        required=True,
        help="Branch name used for workflow run lookup",
    )
    release_gates_cmd.add_argument(
        "--sha",
        required=True,
        help="Commit SHA to validate",
    )
    release_gates_cmd.add_argument(
        "--repo",
        help="Optional owner/repo override for workflow run lookup",
    )
    release_gates_cmd.add_argument(
        "--wait-seconds",
        type=int,
        default=1800,
        help="Maximum seconds to wait for required workflow runs",
    )
    release_gates_cmd.add_argument(
        "--poll-seconds",
        type=int,
        default=20,
        help="Polling interval for workflow run checks",
    )
    release_gates_cmd.add_argument(
        "--preflight-workflow",
        default="release_preflight.yml",
        help="Workflow name used for preflight gate check",
    )
    release_gates_cmd.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip preflight workflow gate (useful inside preflight itself)",
    )
    release_gates_cmd.add_argument(
        "--allow-branch-fallback",
        action="store_true",
        help="Allow commit-only fallback when branch-filtered run lookup is empty",
    )
    release_gates_cmd.add_argument("--dry-run", action="store_true")
    release_gates_cmd.add_argument("--format", choices=["md", "json"], default="md")
    release_gates_cmd.add_argument("--output")
    release_gates_cmd.add_argument(
        "--pipe-command", help="Pipe report output to a command"
    )
    release_gates_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )
    add_release_distribution_parsers(sub)
