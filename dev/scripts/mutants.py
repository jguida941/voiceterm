#!/usr/bin/env python3
"""VoiceTerm mutation testing CLI.

Supports three targeting modes:
  (default)     Auto-detect changed .rs files via git diff against --base-branch
  --file F      Target one or more explicit source files (comma-separated)
  --module M    Target a predefined module group

Baseline skip is on by default (sandbox baseline is unreliable).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Wire repo root so ``dev.scripts.devctl.*`` imports resolve.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dev.scripts.devctl.config import REPO_ROOT, SRC_DIR  # noqa: E402

from mutants_config import (  # noqa: E402
    DEFAULT_BASE_BRANCH,
    MODULES,
    list_modules,
    parse_shard_spec,
    select_modules_interactive,
)
from mutants_git import git_changed_rs_files  # noqa: E402
from mutants_plot import plot_hotspots  # noqa: E402
from mutants_results import output_results, parse_results  # noqa: E402
from mutants_runner import run_mutants  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VoiceTerm Mutation Testing Helper")

    parser.add_argument(
        "--changed", action="store_true", default=False,
        help="Auto-detect changed .rs files via git diff (default when no --module/--file/--all)",
    )
    parser.add_argument(
        "--base-branch", default=DEFAULT_BASE_BRANCH,
        help=f"Base branch for --changed diff (default: {DEFAULT_BASE_BRANCH})",
    )
    parser.add_argument("--file", help="Target specific .rs files (comma-separated, workspace-relative)")
    parser.add_argument("--all", action="store_true", help="Test all modules")
    parser.add_argument("--module", "-m", help="Specific module to test")
    parser.add_argument("--list", "-l", action="store_true", help="List available modules")

    parser.add_argument(
        "--baseline-skip", action="store_true", default=True,
        help="Skip baseline check (default: on)",
    )
    parser.add_argument("--no-baseline-skip", action="store_true", help="Run the baseline check")

    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--timeout", "-t", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--results-only", action="store_true", help="Just parse existing results")
    parser.add_argument("--offline", action="store_true", help="Set CARGO_NET_OFFLINE=true")
    parser.add_argument("--cargo-home", help="Override CARGO_HOME for cargo mutants")
    parser.add_argument("--cargo-target-dir", help="Override CARGO_TARGET_DIR for cargo mutants")
    parser.add_argument("--shard", help="Run one shard, e.g. 1/8")
    parser.add_argument("--top", type=int, default=5, help="Top N paths to summarize")
    parser.add_argument("--plot", action="store_true", help="Render a matplotlib hotspot plot")
    parser.add_argument("--plot-scope", choices=["file", "dir"], default="file")
    parser.add_argument("--plot-top-pct", type=float, default=0.25)
    parser.add_argument("--plot-output", help="Output path for the plot image")
    parser.add_argument("--plot-show", action="store_true", help="Display the plot window")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.list:
        list_modules()
        return

    if args.results_only:
        _show_results(args)
        return

    file_targets, modules = _resolve_targets(args)

    try:
        shard = parse_shard_spec(args.shard)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(2)

    baseline_skip = args.baseline_skip and not args.no_baseline_skip

    returncode = run_mutants(
        workspace_dir=SRC_DIR,
        modules=modules,
        file_targets=file_targets,
        timeout=args.timeout,
        baseline_skip=baseline_skip,
        shard=shard,
        cargo_home=args.cargo_home,
        cargo_target_dir=args.cargo_target_dir,
        offline=args.offline,
    )

    _show_results(args)

    if returncode is None:
        sys.exit(2)
    if returncode != 0:
        sys.exit(returncode)
    results = parse_results()
    if results and results["score"] < 80:
        sys.exit(1)


def _resolve_targets(args) -> tuple[list[str] | None, list[str] | None]:
    """Resolve targeting mode: --file > --module > --all > --changed (default)."""
    if args.file:
        targets = [f.strip() for f in args.file.split(",") if f.strip()]
        print(f"\nTargeting {len(targets)} explicit file(s)")
        return targets, None

    if args.all:
        modules = list(MODULES.keys())
        print(f"\nSelected all modules: {', '.join(modules)}")
        return None, modules

    if args.module:
        modules = [m.strip() for m in args.module.split(",")]
        print(f"\nSelected modules: {', '.join(modules)}")
        return None, modules

    print(f"\nAuto-detecting changed .rs files vs {args.base_branch}...")
    targets = git_changed_rs_files(REPO_ROOT, args.base_branch, SRC_DIR)
    if not targets:
        print("No changed .rs source files found. Nothing to mutate.")
        sys.exit(0)
    print(f"Found {len(targets)} changed source file(s):")
    for f in targets:
        print(f"  - {f}")
    return targets, None


def _show_results(args) -> None:
    results = parse_results()
    output_results(results, "json" if args.json else "markdown", top_n=args.top)
    if args.plot:
        plot_hotspots(
            results,
            args.plot_scope,
            args.plot_top_pct,
            args.plot_output,
            args.plot_show,
        )


if __name__ == "__main__":
    main()
