"""Parser wiring for `devctl triage-loop` arguments."""

from __future__ import annotations


def add_triage_loop_parser(sub) -> None:
    """Register the `triage-loop` command parser on the given subparser group."""
    loop_cmd = sub.add_parser(
        "triage-loop",
        help="Run bounded CodeRabbit backlog triage/remediation loop with report bundles",
    )
    loop_cmd.add_argument("--repo", help="owner/repo (default: $GITHUB_REPOSITORY)")
    loop_cmd.add_argument("--branch", required=True)
    loop_cmd.add_argument(
        "--workflow",
        default="CodeRabbit Triage Bridge",
        help="Workflow that produces backlog-medium.json artifacts",
    )
    loop_cmd.add_argument("--max-attempts", type=int, default=3)
    loop_cmd.add_argument("--run-list-limit", type=int, default=30)
    loop_cmd.add_argument("--poll-seconds", type=int, default=20)
    loop_cmd.add_argument("--timeout-seconds", type=int, default=1800)
    loop_cmd.add_argument(
        "--mode",
        choices=["report-only", "plan-then-fix", "fix-only"],
        default="plan-then-fix",
        help="Loop mode: report-only or run fix attempts when backlog remains",
    )
    loop_cmd.add_argument(
        "--fix-command",
        help=(
            "Optional command executed when backlog is non-empty in plan-then-fix/fix-only "
            "modes. Command must commit+push a new SHA to the same branch."
        ),
    )
    loop_cmd.add_argument("--emit-bundle", action="store_true")
    loop_cmd.add_argument(
        "--bundle-dir",
        default=".cihub/coderabbit",
        help="Directory where bundle artifacts are written",
    )
    loop_cmd.add_argument(
        "--bundle-prefix",
        default="coderabbit-ralph-loop",
        help="Bundle filename prefix for md/json/proposal outputs",
    )
    loop_cmd.add_argument(
        "--mp-proposal",
        action="store_true",
        help="Emit MASTER_PLAN proposal markdown derived from loop results",
    )
    loop_cmd.add_argument(
        "--mp-proposal-path",
        help="Optional explicit path for MASTER_PLAN proposal markdown",
    )
    loop_cmd.add_argument(
        "--notify",
        choices=["summary-only", "summary-and-comment"],
        default="summary-only",
        help="Notification mode: summary only or summary + GitHub comment upsert",
    )
    loop_cmd.add_argument(
        "--comment-target",
        choices=["auto", "pr", "commit"],
        default="auto",
        help="Comment target for summary-and-comment mode (auto prefers PR, then commit)",
    )
    loop_cmd.add_argument(
        "--comment-pr-number",
        type=int,
        help="Optional explicit PR number for comment-target=pr/auto",
    )
    loop_cmd.add_argument(
        "--source-run-id",
        type=int,
        help="Authoritative source workflow run id when launched from workflow_run",
    )
    loop_cmd.add_argument(
        "--source-run-sha",
        help="Expected source workflow head SHA (used for run/artifact correlation validation)",
    )
    loop_cmd.add_argument(
        "--source-event",
        choices=["workflow_run", "workflow_dispatch"],
        default="workflow_dispatch",
        help="Source trigger kind for run correlation and reporting",
    )
    loop_cmd.add_argument("--dry-run", action="store_true")
    loop_cmd.add_argument("--format", choices=["md", "json"], default="md")
    loop_cmd.add_argument("--output")
    loop_cmd.add_argument("--json-output", help="Optional secondary JSON report path")
    loop_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    loop_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
