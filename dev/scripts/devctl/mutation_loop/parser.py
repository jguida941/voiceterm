"""Parser wiring for `devctl mutation-loop` arguments."""

from __future__ import annotations


def add_mutation_loop_parser(sub) -> None:
    """Register the `mutation-loop` command parser on the given subparser group."""
    loop_cmd = sub.add_parser(
        "mutation-loop",
        help="Run bounded mutation remediation loop with report bundles",
    )
    loop_cmd.add_argument("--repo", help="owner/repo (default: $GITHUB_REPOSITORY)")
    loop_cmd.add_argument("--branch", required=True)
    loop_cmd.add_argument(
        "--workflow",
        default="Mutation Testing",
        help="Workflow that produces mutation outcomes artifacts",
    )
    loop_cmd.add_argument("--max-attempts", type=int, default=3)
    loop_cmd.add_argument("--run-list-limit", type=int, default=30)
    loop_cmd.add_argument("--poll-seconds", type=int, default=20)
    loop_cmd.add_argument("--timeout-seconds", type=int, default=1800)
    loop_cmd.add_argument(
        "--mode",
        choices=["report-only", "plan-then-fix", "fix-only"],
        default="report-only",
        help="Loop mode: report-only or bounded fix attempts when score is below threshold",
    )
    loop_cmd.add_argument(
        "--threshold",
        type=float,
        default=0.80,
        help="Mutation score threshold to consider the loop resolved",
    )
    loop_cmd.add_argument(
        "--fix-command",
        help=(
            "Optional command executed when score is below threshold in plan-then-fix/fix-only "
            "modes. Command must commit+push a new SHA to the same branch."
        ),
    )
    loop_cmd.add_argument("--emit-bundle", action="store_true")
    loop_cmd.add_argument(
        "--bundle-dir",
        default=".cihub/mutation",
        help="Directory where bundle artifacts are written",
    )
    loop_cmd.add_argument(
        "--bundle-prefix",
        default="mutation-ralph-loop",
        help="Bundle filename prefix for md/json/playbook outputs",
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
        help="Comment target for summary-and-comment mode (auto prefers PR input, then commit)",
    )
    loop_cmd.add_argument(
        "--comment-pr-number",
        type=int,
        help="Optional explicit PR number for comment-target=pr/auto",
    )
    loop_cmd.add_argument("--dry-run", action="store_true")
    loop_cmd.add_argument("--format", choices=["md", "json"], default="md")
    loop_cmd.add_argument("--output")
    loop_cmd.add_argument("--json-output", help="Optional secondary JSON report path")
    loop_cmd.add_argument("--pipe-command", help="Pipe report output to a command")
    loop_cmd.add_argument("--pipe-args", nargs="*", help="Extra args for pipe command")
