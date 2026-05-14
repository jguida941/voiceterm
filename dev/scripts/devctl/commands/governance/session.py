"""devctl session: standardized entry point for AI agent sessions.

Replaces ad-hoc prompts with governed, portable session bootstraps.
Each role (reviewer, implementer, dashboard) gets a consistent
startup sequence through the typed review-channel system.
"""

from __future__ import annotations

from ...config import get_repo_root
from ...common import add_standard_output_arguments
from .session_orientation import emit_session_orientation


def add_parser(subparsers) -> None:
    """Register the session CLI parser."""
    cmd = subparsers.add_parser(
        "session",
        help="Start a governed AI agent session with role-specific bootstrap.",
    )
    cmd.add_argument(
        "--role",
        choices=("reviewer", "implementer", "dashboard", "observer"),
        default="",
        help="Agent role for this session.",
    )
    cmd.add_argument(
        "--loop",
        action="store_true",
        default=False,
        help="Reviewer-only: continuous polling loop that relaunches on exit.",
    )
    cmd.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconds between polling cycles in --loop mode (default: 30).",
    )
    cmd.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Skip TTY requirement. Use when running without a terminal.",
    )
    cmd.add_argument(
        "--provider",
        default="",
        help="Provider id used when writing a session-resume receipt.",
    )
    cmd.add_argument(
        "--session-id-or-transcript-path",
        default="",
        help="Optional provider session id, transcript path, or metadata path.",
    )
    cmd.add_argument(
        "--write-resume-receipt",
        action="store_true",
        default=False,
        help="Append an AgentResumeReceipt after loading typed state.",
    )
    cmd.add_argument(
        "--resume-result",
        choices=("loaded", "blocked", "failed"),
        default="loaded",
        help="Result recorded when --write-resume-receipt is used.",
    )
    cmd.add_argument(
        "--authority-result",
        choices=("allowed", "blocked"),
        default="",
        help="Optional authority result recorded in the resume receipt.",
    )
    cmd.add_argument(
        "--include-review-status",
        choices=("always", "auto", "never"),
        default="always",
        help="Whether the one-shot session packet refreshes review-channel status.",
    )
    cmd.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Per-step timeout for the one-shot orientation sequence.",
    )
    add_standard_output_arguments(cmd)
    subcommands = cmd.add_subparsers(dest="session_action")
    reconcile = subcommands.add_parser(
        "reconcile",
        help="Reconcile persisted session liveness artifacts.",
    )
    reconcile.add_argument(
        "--kill-stale",
        action="store_true",
        default=False,
        help="Detach stale persisted attachments and terminate stale attachment PIDs.",
    )
    reconcile.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report stale session artifacts without mutating them.",
    )
    reconcile.add_argument(
        "--session-output-root",
        default="",
        help=(
            "Review-channel status root containing sessions/. Defaults to the "
            "repo-pack review status directory."
        ),
    )
    reconcile.add_argument(
        "--no-refresh-status",
        action="store_true",
        default=False,
        help="Skip review-channel status projection refresh after cleanup.",
    )
    reconcile.add_argument(
        "--execution-mode",
        choices=("auto", "markdown-bridge", "overlay"),
        default="markdown-bridge",
        help="Execution mode passed to review-channel status refresh.",
    )
    add_standard_output_arguments(reconcile)


def run(args) -> int:
    """Dispatch to the role-specific session handler."""
    if getattr(args, "session_action", "") == "reconcile":
        from .session_reconcile import run_reconcile

        return run_reconcile(args, repo_root=get_repo_root())

    role = args.role
    if not role:
        raise SystemExit("devctl session requires --role or a subcommand")
    repo_root = get_repo_root()
    if role == "reviewer" and args.loop:
        from .session_reviewer_loop import run_reviewer_loop

        return run_reviewer_loop(
            repo_root=repo_root,
            interval=args.interval,
            headless=args.headless,
        )
    if role in {"reviewer", "implementer", "observer", "dashboard"}:
        orientation_role = "observer" if role == "dashboard" else role
        return emit_session_orientation(args, repo_root, role=orientation_role)
    return 1
