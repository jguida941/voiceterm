"""Parser wiring for `devctl autonomy-benchmark` arguments."""

from __future__ import annotations

import argparse


def add_autonomy_benchmark_parser(sub) -> None:
    """Register the `autonomy-benchmark` command parser."""
    benchmark_cmd = sub.add_parser(
        "autonomy-benchmark",
        help=(
            "Run swarm-size/tactic benchmark matrix against active-plan scope and "
            "emit tradeoff metrics"
        ),
    )
    benchmark_cmd.add_argument(
        "--repo", help="owner/repo (optional; falls back to env/repo detection)"
    )
    benchmark_cmd.add_argument("--run-label", help="Optional explicit benchmark label")
    benchmark_cmd.add_argument(
        "--plan-doc", default="dev/active/autonomous_control_plane.md"
    )
    benchmark_cmd.add_argument("--index-doc", default="dev/active/INDEX.md")
    benchmark_cmd.add_argument("--master-plan-doc", default="dev/active/MASTER_PLAN.md")
    benchmark_cmd.add_argument("--mp-scope", default="MP-338")
    benchmark_cmd.add_argument("--next-steps-limit", type=int, default=8)
    benchmark_cmd.add_argument(
        "--question",
        help="Optional explicit benchmark prompt (default: derived from plan checklist)",
    )
    benchmark_cmd.add_argument(
        "--question-file", help="Optional file containing explicit benchmark prompt"
    )
    benchmark_cmd.add_argument(
        "--output-root",
        default="dev/reports/autonomy/benchmarks",
        help="Root directory for benchmark bundles",
    )
    benchmark_cmd.add_argument(
        "--swarm-counts",
        default="10,15,20,30,40",
        help="Comma-separated swarm batch sizes to benchmark",
    )
    benchmark_cmd.add_argument(
        "--tactics",
        default="uniform,specialized,research-first,test-first",
        help="Comma-separated tactic profiles",
    )
    benchmark_cmd.add_argument(
        "--agents",
        type=int,
        default=4,
        help="Fixed agent count per swarm run",
    )
    benchmark_cmd.add_argument(
        "--parallel-workers",
        type=int,
        default=4,
        help="Parallel workers per swarm run",
    )
    benchmark_cmd.add_argument(
        "--max-concurrent-swarms",
        type=int,
        default=10,
        help="Maximum concurrent swarm runs per scenario",
    )
    benchmark_cmd.add_argument("--branch-base", default="develop")
    benchmark_cmd.add_argument(
        "--mode",
        choices=["report-only", "plan-then-fix", "fix-only"],
        default="report-only",
    )
    benchmark_cmd.add_argument(
        "--fix-command",
        help=(
            "Fix command forwarded to each autonomy-swarm run when --mode is "
            "plan-then-fix/fix-only"
        ),
    )
    benchmark_cmd.add_argument("--max-rounds", type=int, default=1)
    benchmark_cmd.add_argument("--max-hours", type=float, default=0.5)
    benchmark_cmd.add_argument("--max-tasks", type=int, default=1)
    benchmark_cmd.add_argument("--loop-max-attempts", type=int, default=1)
    benchmark_cmd.add_argument("--agent-timeout-seconds", type=int, default=1800)
    benchmark_cmd.add_argument("--diff-ref", default="origin/develop")
    benchmark_cmd.add_argument(
        "--target-paths",
        nargs="*",
        default=[],
        help="Optional path filters for metadata diff scoring",
    )
    benchmark_cmd.add_argument("--token-budget", type=int, default=0)
    benchmark_cmd.add_argument("--per-agent-token-cost", type=int, default=12000)
    benchmark_cmd.add_argument(
        "--post-audit",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable post-audit digest after each swarm run",
    )
    benchmark_cmd.add_argument(
        "--reviewer-lane",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable reviewer lane for each swarm run",
    )
    benchmark_cmd.add_argument("--dry-run", action="store_true")
    benchmark_cmd.add_argument(
        "--charts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate benchmark tradeoff charts",
    )
    benchmark_cmd.add_argument("--format", choices=["json", "md"], default="md")
    benchmark_cmd.add_argument("--output")
    benchmark_cmd.add_argument("--json-output")
    benchmark_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    benchmark_cmd.add_argument(
        "--pipe-args", nargs="*", help="Extra args for pipe command"
    )
