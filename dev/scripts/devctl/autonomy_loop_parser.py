"""Parser wiring for `devctl autonomy-loop` arguments."""

from __future__ import annotations


def add_autonomy_loop_parser(sub) -> None:
    """Register the `autonomy-loop` command parser on the given subparser group."""
    loop_cmd = sub.add_parser(
        "autonomy-loop",
        help=(
            "Run a bounded autonomous controller loop that orchestrates triage-loop "
            "and emits checkpoint packet/queue artifacts"
        ),
    )
    loop_cmd.add_argument("--repo", help="owner/repo (default: $GITHUB_REPOSITORY)")
    loop_cmd.add_argument("--plan-id", required=True, help="Stable plan identifier for this controller run")
    loop_cmd.add_argument("--branch-base", default="develop", help="Target integration branch")
    loop_cmd.add_argument(
        "--working-branch-prefix",
        default="autoloop",
        help="Prefix for generated working branch names in checkpoint packets",
    )
    loop_cmd.add_argument(
        "--workflow",
        default="CodeRabbit Triage Bridge",
        help="Workflow consumed by nested triage-loop attempts",
    )
    loop_cmd.add_argument(
        "--mode",
        choices=["report-only", "plan-then-fix", "fix-only"],
        default="report-only",
        help="Nested triage-loop mode for each controller round",
    )
    loop_cmd.add_argument(
        "--loop-branch-mode",
        choices=["base", "working"],
        default="base",
        help=(
            "Which branch value to pass to triage-loop (base is safer with current "
            "CodeRabbit workflow triggers)"
        ),
    )
    loop_cmd.add_argument("--fix-command", help="Optional nested fix command for plan-then-fix/fix-only")
    loop_cmd.add_argument("--max-rounds", type=int, default=6)
    loop_cmd.add_argument("--max-hours", type=float, default=4.0)
    loop_cmd.add_argument("--max-tasks", type=int, default=24)
    loop_cmd.add_argument("--checkpoint-every", type=int, default=1)
    loop_cmd.add_argument("--loop-max-attempts", type=int, default=1)
    loop_cmd.add_argument("--run-list-limit", type=int, default=30)
    loop_cmd.add_argument("--poll-seconds", type=int, default=20)
    loop_cmd.add_argument("--timeout-seconds", type=int, default=1800)
    loop_cmd.add_argument(
        "--notify",
        choices=["summary-only", "summary-and-comment"],
        default="summary-only",
        help="Nested triage-loop notification mode",
    )
    loop_cmd.add_argument(
        "--comment-target",
        choices=["auto", "pr", "commit"],
        default="auto",
        help="Nested triage-loop comment target when notify=summary-and-comment",
    )
    loop_cmd.add_argument(
        "--comment-pr-number",
        type=int,
        help="Optional explicit PR number for nested summary-and-comment mode",
    )
    loop_cmd.add_argument(
        "--packet-out",
        default="dev/reports/autonomy/packets",
        help="Packet artifact root (controller writes run-scoped packet files here)",
    )
    loop_cmd.add_argument(
        "--queue-out",
        default="dev/reports/autonomy/queue",
        help="Queue artifact root (inbox/outbox/archive)",
    )
    loop_cmd.add_argument("--max-packet-age-hours", type=float, default=72.0)
    loop_cmd.add_argument("--max-draft-chars", type=int, default=1600)
    loop_cmd.add_argument(
        "--allow-auto-send",
        action="store_true",
        help="Allow loop-packet to mark low-risk packets as auto-send eligible",
    )
    loop_cmd.add_argument(
        "--terminal-trace-lines",
        type=int,
        default=12,
        help="Maximum terminal/action trace lines attached per checkpoint packet",
    )
    loop_cmd.add_argument("--dry-run", action="store_true")
    loop_cmd.add_argument("--format", choices=["md", "json"], default="json")
    loop_cmd.add_argument("--output")
    loop_cmd.add_argument("--json-output", help="Optional secondary JSON report path")
    loop_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    loop_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
