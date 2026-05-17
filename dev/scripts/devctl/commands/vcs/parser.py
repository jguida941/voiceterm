"""Parser registration for devctl sync, push, and commit commands."""

from __future__ import annotations

import argparse

from ...common import add_standard_output_arguments


def add_sync_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register sync parser and arguments."""
    sync_cmd = subparsers.add_parser(
        "sync", help="Sync repo-policy development/release/current branches with guardrails"
    )
    sync_cmd.add_argument(
        "--remote", help="Remote to sync against (default: repo policy)"
    )
    sync_cmd.add_argument(
        "--branches",
        nargs="+",
        help="Explicit branches to sync (default: repo-policy development/release plus current branch)",
    )
    sync_cmd.add_argument(
        "--no-current",
        action="store_true",
        help="Do not include the current branch in the sync set",
    )
    sync_cmd.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow sync to run with local uncommitted changes",
    )
    sync_cmd.add_argument(
        "--push",
        action="store_true",
        help="Push local-ahead branches through the governed devctl push flow after fast-forward pull",
    )
    sync_cmd.add_argument(
        "--quality-policy",
        help="Override the repo governance policy path for this run",
    )
    add_standard_output_arguments(sync_cmd)


def add_push_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register push parser and arguments."""
    push_cmd = subparsers.add_parser(
        "push",
        help="Guarded repo-policy branch push with preflight and post-push audit",
    )
    push_cmd.add_argument(
        "--remote",
        help="Remote to push to (default: repo policy)",
    )
    push_cmd.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the push after validation succeeds",
    )
    push_cmd.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Policy-gated: skip the configured push preflight command",
    )
    push_cmd.add_argument(
        "--skip-post-push",
        action="store_true",
        help="Policy-gated: skip the configured post-push bundle after a successful push",
    )
    push_cmd.add_argument(
        "--quality-policy",
        help="Override the repo governance policy path for this run",
    )
    push_cmd.add_argument(
        "--actor",
        default="",
        help="Actor executing the push; used to resolve live AgentLoopDecision.",
    )
    push_cmd.add_argument(
        "--role",
        default="",
        help="Actor role used to resolve live AgentLoopDecision.",
    )
    push_cmd.add_argument(
        "--session-id",
        default="",
        help="Actor session id used to resolve live AgentLoopDecision.",
    )
    push_cmd.add_argument(
        "--control-decision-input",
        default="",
        help="AgentLoopDecision/control decision JSON path enforced before push.",
    )
    add_standard_output_arguments(push_cmd)


def add_commit_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register commit parser and arguments."""
    commit_cmd = subparsers.add_parser(
        "commit",
        help="Governed commit — runs guard bundle before git commit",
    )
    commit_cmd.add_argument(
        "-m",
        "--message",
        help="Commit message (passed to git commit -m)",
    )
    commit_cmd.add_argument(
        "--amend",
        action="store_true",
        help="Amend the previous commit (passed to git commit --amend)",
    )
    commit_cmd.add_argument(
        "--approve-pending",
        action="store_true",
        help=(
            "Operator-owned remote-control resume: approve the current governed "
            "pipeline and continue the existing commit without reconstructing "
            "packet fields by hand."
        ),
    )
    commit_cmd.add_argument(
        "--paths",
        nargs="+",
        default=(),
        help=(
            "Repo-relative paths to stage through the governed vcs.stage action "
            "before guard and approval checks."
        ),
    )
    commit_cmd.add_argument(
        "--role",
        choices=("dashboard", "implementer", "observer", "reviewer"),
        default=None,
        help=(
            "Declare caller lane for mutation authority. Review-channel "
            "conductors populate this automatically."
        ),
    )
    commit_cmd.add_argument(
        "--action-request",
        default=None,
        help=(
            "Scoped review-channel action_request packet that grants this "
            "governed commit invocation authority for its declared runtime target."
        ),
    )
    commit_cmd.add_argument(
        "passthrough",
        nargs=argparse.REMAINDER,
        help="Additional arguments passed through to git commit (use -- before option-style flags)",
    )
    add_standard_output_arguments(commit_cmd)
