"""Progress feedback helpers for `devctl check`.

Prints ``[N/M] step-name...`` to stderr so users can see which step is
currently executing without interfering with ``--format``/``--output``.
"""

from __future__ import annotations

import sys
from typing import List


def count_quality_steps(args, settings: dict) -> int:
    """Pre-count the number of quality-gate steps that will be executed.

    This mirrors the conditional logic in ``check.run()`` so progress feedback
    can display ``[N/M]`` with an accurate total *before* execution begins.
    """
    count = 0
    if not args.skip_fmt:
        count += 1
    if not args.skip_clippy:
        count += 1
    if settings["with_ai_guard"]:
        count += 5  # code-shape, rust-lint-debt, rust-best-practices, rust-audit-patterns, rust-security-footguns
    if not settings["skip_tests"]:
        count += 1
    if not settings["skip_build"]:
        count += 1
    if settings["with_wake_guard"]:
        count += 1
    if settings["with_perf"]:
        count += 1  # perf-smoke
        if not args.dry_run:
            count += 1  # perf-verify
    if settings["with_mem_loop"]:
        count += args.mem_iterations
    if settings["with_mutants"]:
        count += 1
    if settings["with_mutation_score"]:
        count += 1
    return count


def emit_progress(
    step_specs: List[dict],
    current: int,
    total: int,
    is_parallel: bool,
) -> None:
    """Write ``[N/M] step-name...`` progress feedback to stderr."""
    count = len(step_specs)
    if count == 0:
        return
    if count == 1 or not is_parallel:
        for i, spec in enumerate(step_specs):
            idx = current + i + 1
            print(f"[{idx}/{total}] {spec['name']}...", file=sys.stderr, flush=True)
    else:
        start_idx = current + 1
        end_idx = current + count
        names = ", ".join(spec["name"] for spec in step_specs)
        print(
            f"[{start_idx}-{end_idx}/{total}] running {count} steps in parallel ({names})...",
            file=sys.stderr,
            flush=True,
        )
