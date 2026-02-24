"""Parser wiring for `devctl autonomy-run` arguments."""

from __future__ import annotations

import argparse


def add_autonomy_run_parser(sub) -> None:
    """Register the `autonomy-run` command parser."""
    run_cmd = sub.add_parser(
        "autonomy-run",
        help=(
            "Run one guarded autonomy pipeline: load active-plan scope, execute "
            "swarm+reviewer lane, run governance checks, and append plan evidence"
        ),
    )
    run_cmd.add_argument(
        "--repo", help="owner/repo (optional; falls back to env/repo detection)"
    )
    run_cmd.add_argument("--run-label", help="Optional explicit run label")
    run_cmd.add_argument("--plan-doc", default="dev/active/autonomous_control_plane.md")
    run_cmd.add_argument("--index-doc", default="dev/active/INDEX.md")
    run_cmd.add_argument("--master-plan-doc", default="dev/active/MASTER_PLAN.md")
    run_cmd.add_argument("--mp-scope", default="MP-338")
    run_cmd.add_argument("--next-steps-limit", type=int, default=8)
    run_cmd.add_argument(
        "--question",
        help="Optional explicit swarm prompt (default: derived from unchecked plan steps)",
    )
    run_cmd.add_argument(
        "--run-root",
        default="dev/reports/autonomy/runs",
        help="Root directory for autonomy-run bundles",
    )
    run_cmd.add_argument(
        "--swarm-output-root",
        default="dev/reports/autonomy/swarms",
        help="Root directory for nested autonomy-swarm bundles",
    )
    run_cmd.add_argument("--branch-base", default="develop")
    run_cmd.add_argument(
        "--mode",
        choices=["report-only", "plan-then-fix", "fix-only"],
        default="report-only",
    )
    run_cmd.add_argument(
        "--fix-command",
        help=(
            "Nested fix command forwarded to autonomy-swarm/autonomy-loop when "
            "--mode is plan-then-fix/fix-only"
        ),
    )
    run_cmd.add_argument("--agents", type=int, help="Explicit agent count override")
    run_cmd.add_argument(
        "--adaptive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use metadata-driven agent sizing when --agents is not set",
    )
    run_cmd.add_argument("--min-agents", type=int, default=4)
    run_cmd.add_argument("--max-agents", type=int, default=20)
    run_cmd.add_argument("--token-budget", type=int, default=0)
    run_cmd.add_argument("--per-agent-token-cost", type=int, default=12000)
    run_cmd.add_argument("--parallel-workers", type=int, default=4)
    run_cmd.add_argument("--agent-timeout-seconds", type=int, default=1800)
    run_cmd.add_argument("--max-rounds", type=int, default=1)
    run_cmd.add_argument("--max-hours", type=float, default=1.0)
    run_cmd.add_argument("--max-tasks", type=int, default=1)
    run_cmd.add_argument("--checkpoint-every", type=int, default=1)
    run_cmd.add_argument("--loop-max-attempts", type=int, default=1)
    run_cmd.add_argument("--dry-run", action="store_true")
    run_cmd.add_argument("--diff-ref", default="origin/develop")
    run_cmd.add_argument(
        "--target-paths",
        nargs="*",
        default=[],
        help="Optional path filters for metadata diff scoring",
    )
    run_cmd.add_argument(
        "--charts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate swarm and digest charts",
    )
    run_cmd.add_argument(
        "--audit-source-root",
        default="dev/reports/autonomy",
        help="Source root for nested post-audit autonomy-report runs",
    )
    run_cmd.add_argument(
        "--audit-library-root",
        default="dev/reports/autonomy/library",
        help="Library root for nested post-audit autonomy-report bundles",
    )
    run_cmd.add_argument(
        "--audit-event-log",
        default="dev/reports/audits/devctl_events.jsonl",
        help="Event log for nested post-audit autonomy-report runs",
    )
    run_cmd.add_argument(
        "--stale-minutes",
        type=int,
        default=120,
        help="Stale threshold for nested orchestrate-watch audit",
    )
    run_cmd.add_argument(
        "--skip-governance",
        action="store_true",
        help="Skip governance guard commands (not recommended)",
    )
    run_cmd.add_argument(
        "--skip-plan-update",
        action="store_true",
        help="Do not append progress/audit evidence to the plan doc",
    )
    run_cmd.add_argument(
        "--continuous",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Keep running swarm cycles over plan checklist items until limits are hit "
            "or a cycle fails governance/safety checks"
        ),
    )
    run_cmd.add_argument(
        "--continuous-max-cycles",
        type=int,
        default=10,
        help="Maximum swarm cycles when --continuous is enabled",
    )
    run_cmd.add_argument("--format", choices=["json", "md"], default="md")
    run_cmd.add_argument("--output")
    run_cmd.add_argument("--json-output")
    run_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    run_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
