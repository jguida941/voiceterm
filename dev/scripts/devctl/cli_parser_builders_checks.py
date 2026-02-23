"""Parser builders for check and mutation-related devctl commands."""

from __future__ import annotations

import argparse


def add_check_parser(
    sub: argparse._SubParsersAction,
    *,
    default_mem_iterations: int,
    default_mutants_timeout: int,
    default_mutation_threshold: float,
) -> None:
    """Register the `check` command parser."""
    check_cmd = sub.add_parser("check", help="Run fmt/clippy/tests/build (and optional extras)")
    check_cmd.add_argument(
        "--profile",
        choices=["ci", "prepush", "release", "maintainer-lint", "quick", "ai-guard"],
    )
    check_cmd.add_argument("--ci", action="store_true", help="Match rust_ci.yml scope (alias for --profile ci)")
    check_cmd.add_argument(
        "--prepush",
        action="store_true",
        help="Run CI + perf/mem loop (alias for --profile prepush)",
    )
    check_cmd.add_argument("--skip-fmt", action="store_true")
    check_cmd.add_argument("--skip-clippy", action="store_true")
    check_cmd.add_argument("--skip-tests", action="store_true")
    check_cmd.add_argument("--skip-build", action="store_true")
    check_cmd.add_argument("--fix", action="store_true", help="Run cargo fmt (not --check)")
    check_cmd.add_argument("--with-perf", action="store_true", help="Run perf smoke + verify")
    check_cmd.add_argument("--with-mem-loop", action="store_true", help="Run memory guard loop")
    check_cmd.add_argument("--mem-iterations", type=int, default=default_mem_iterations)
    check_cmd.add_argument(
        "--with-wake-guard",
        action="store_true",
        help="Run wake-word regression + soak guard",
    )
    check_cmd.add_argument(
        "--wake-soak-rounds",
        type=int,
        default=4,
        help="Wake-word soak iterations when wake guard is enabled",
    )
    check_cmd.add_argument("--with-mutants", action="store_true", help="Run mutants after checks")
    check_cmd.add_argument("--with-mutation-score", action="store_true", help="Check mutation score")
    check_cmd.add_argument(
        "--with-ai-guard",
        action="store_true",
        help="Run code-shape, lint-debt, Rust best-practices, and Rust audit-pattern guards",
    )
    check_cmd.add_argument("--mutation-score-path", help="Path to outcomes.json")
    check_cmd.add_argument("--mutation-score-threshold", type=float, default=default_mutation_threshold)
    check_cmd.add_argument(
        "--mutation-score-warn-age-hours",
        type=float,
        default=24.0,
        help="Warn when mutation outcomes are older than this many hours (set <0 to disable)",
    )
    check_cmd.add_argument(
        "--mutation-score-max-age-hours",
        type=float,
        help="Fail release mutation-score step when outcomes are older than this many hours",
    )
    check_cmd.add_argument("--mutants-module", help="Mutants module filter")
    check_cmd.add_argument("--mutants-all", action="store_true")
    check_cmd.add_argument("--mutants-timeout", type=int, default=default_mutants_timeout)
    check_cmd.add_argument("--mutants-shard", help="Mutants shard spec like 1/8")
    check_cmd.add_argument("--mutants-offline", action="store_true")
    check_cmd.add_argument("--mutants-cargo-home")
    check_cmd.add_argument("--mutants-cargo-target-dir")
    check_cmd.add_argument("--mutants-plot", action="store_true")
    check_cmd.add_argument("--mutants-plot-scope", choices=["file", "dir"])
    check_cmd.add_argument("--mutants-plot-top-pct", type=float)
    check_cmd.add_argument("--mutants-plot-output")
    check_cmd.add_argument("--mutants-plot-show", action="store_true")
    check_cmd.add_argument("--keep-going", action="store_true")
    check_cmd.add_argument(
        "--no-parallel",
        action="store_true",
        help="Run check steps sequentially instead of parallelized phase batches",
    )
    check_cmd.add_argument(
        "--parallel-workers",
        type=int,
        default=4,
        help="Worker count for parallelizable check phases (default: 4)",
    )
    check_cmd.add_argument("--dry-run", action="store_true")
    check_cmd.add_argument("--format", choices=["text", "json", "md"], default="text")
    check_cmd.add_argument("--output", help="Write report to a file")
    check_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    check_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
    check_cmd.add_argument("--offline", action="store_true")
    check_cmd.add_argument("--cargo-home")
    check_cmd.add_argument("--cargo-target-dir")
    check_cmd.add_argument(
        "--no-process-sweep-cleanup",
        action="store_true",
        help="Disable automatic orphaned voiceterm test-binary cleanup before/after checks",
    )


def add_mutants_parser(
    sub: argparse._SubParsersAction,
    *,
    default_mutants_timeout: int,
) -> None:
    """Register the `mutants` command parser."""
    mutants_cmd = sub.add_parser("mutants", help="Run mutation testing helper")
    mutants_cmd.add_argument("--all", action="store_true")
    mutants_cmd.add_argument("--module")
    mutants_cmd.add_argument("--timeout", type=int, default=default_mutants_timeout)
    mutants_cmd.add_argument("--shard", help="Run one shard, e.g. 1/8")
    mutants_cmd.add_argument("--results-only", action="store_true")
    mutants_cmd.add_argument("--json", action="store_true")
    mutants_cmd.add_argument("--offline", action="store_true")
    mutants_cmd.add_argument("--cargo-home")
    mutants_cmd.add_argument("--cargo-target-dir")
    mutants_cmd.add_argument("--plot", action="store_true")
    mutants_cmd.add_argument("--plot-scope", choices=["file", "dir"])
    mutants_cmd.add_argument("--plot-top-pct", type=float)
    mutants_cmd.add_argument("--plot-output")
    mutants_cmd.add_argument("--plot-show", action="store_true")
    mutants_cmd.add_argument("--top", type=int)
    mutants_cmd.add_argument("--dry-run", action="store_true")


def add_mutation_score_parser(
    sub: argparse._SubParsersAction,
    *,
    default_mutation_threshold: float,
) -> None:
    """Register the `mutation-score` command parser."""
    score_cmd = sub.add_parser("mutation-score", help="Check mutation score threshold")
    score_cmd.add_argument("--path", help="Path to outcomes.json (optional)")
    score_cmd.add_argument("--threshold", type=float, default=default_mutation_threshold)
    score_cmd.add_argument(
        "--warn-age-hours",
        type=float,
        default=24.0,
        help="Warn when mutation outcomes are older than this many hours (set <0 to disable)",
    )
    score_cmd.add_argument(
        "--max-age-hours",
        type=float,
        help="Fail when outcomes are older than this many hours",
    )
    score_cmd.add_argument("--dry-run", action="store_true")
