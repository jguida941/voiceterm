"""Parser for bounded Python test execution."""

from __future__ import annotations

import argparse

from ..runtime.python_test_contract import (
    DEFAULT_PER_TEST_TIMEOUT_SECONDS,
    PYTHON_TEST_SUITES,
)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    cmd = subparsers.add_parser(
        "test-python",
        help="Run bounded, scoped Python tests through repo policy.",
    )
    cmd.add_argument(
        "--suite",
        choices=tuple(PYTHON_TEST_SUITES),
        default="devctl",
        help="Named Python test suite to run.",
    )
    cmd.add_argument(
        "--path",
        action="append",
        default=[],
        help="Override suite targets with one or more explicit pytest paths.",
    )
    cmd.add_argument(
        "--timeout-seconds",
        type=int,
        default=None,
        help="Session timeout for pytest; defaults to the named suite limit.",
    )
    cmd.add_argument(
        "--per-test-timeout-seconds",
        type=int,
        default=DEFAULT_PER_TEST_TIMEOUT_SECONDS,
        help="Per-test timeout enforced by the repo pytest plugin.",
    )
    cmd.add_argument(
        "--no-fail-fast",
        action="store_true",
        default=False,
        help="Collect all failures instead of stopping at the first failure.",
    )
    cmd.add_argument(
        "--parallel-workers",
        type=int,
        default=1,
        help="Maximum pytest shard workers for explicit multi-path runs.",
    )
    cmd.add_argument(
        "--no-parallel",
        action="store_true",
        default=False,
        help="Disable pytest path sharding even when multiple --path values are supplied.",
    )
    cmd.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the bounded pytest command without running it.",
    )
    cmd.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="Output format.",
    )
