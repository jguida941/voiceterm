"""Argparse wiring for the read-only Claude loop surface."""

from __future__ import annotations

import argparse


def add_claude_loop_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``claude-loop`` subcommand."""
    _add_loop_parser(
        sub,
        name="claude-loop",
        help_text="Read-only Claude loop state backed by DashboardSnapshot v3",
    )


def add_agent_loop_parser(sub: argparse._SubParsersAction) -> None:
    """Register the provider-neutral ``agent-loop`` subcommand."""
    _add_loop_parser(
        sub,
        name="agent-loop",
        help_text="Provider-neutral typed agent loop decision and policy",
    )


def _add_loop_parser(
    sub: argparse._SubParsersAction,
    *,
    name: str,
    help_text: str,
) -> None:
    cmd = sub.add_parser(
        name,
        help=help_text,
    )
    cmd.add_argument(
        "--format",
        choices=("md", "json", "simple"),
        default="md",
        help="Output format.",
    )
    cmd.add_argument(
        "--follow",
        action="store_true",
        default=False,
        help="Poll and re-render Claude-loop snapshots until interrupted.",
    )
    cmd.add_argument(
        "--interval",
        default="typed",
        help=(
            "Polling interval for --follow. Use typed to follow "
            "AgentLoopDecision cadence, or a value like 1, 500ms, or 5s."
        ),
    )
    cmd.add_argument(
        "--max-follow-snapshots",
        type=int,
        default=None,
        help="Stop --follow after this many snapshots; useful for probes.",
    )
    cmd.add_argument(
        "--repo-root",
        default=None,
        help="Optional repo root override.",
    )
    cmd.add_argument(
        "--actor",
        default="claude",
        help="Actor id for the scoped loop decision.",
    )
    cmd.add_argument(
        "--role",
        default="dashboard",
        help="Actor role/lane for the scoped loop decision.",
    )
    cmd.add_argument(
        "--session-id",
        default="",
        help="Optional concrete provider session id for scoped packet routing.",
    )
    cmd.add_argument(
        "--mode",
        choices=("auto", "wake", "iterate", "plan", "packet", "full-plan"),
        default="auto",
        help="Typed loop intent; reducers decide behavior from this request.",
    )
    cmd.add_argument(
        "--plan",
        default="",
        help="Optional typed plan target/ref to bind this loop decision.",
    )
    cmd.add_argument(
        "--plan377",
        action="store_true",
        default=False,
        help="Shortcut for --mode plan --plan MP-377.",
    )
    cmd.add_argument(
        "--packet",
        default="",
        help="Optional review packet id to bind this loop decision.",
    )
    cmd.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Reserved executor flag; current surface remains read-only.",
    )
    cmd.add_argument(
        "--operator-override",
        action="store_true",
        default=False,
        help=(
            "Request a typed edit-only operator override for the named packet "
            "or plan. Stage/commit/push remain blocked."
        ),
    )
    cmd.add_argument(
        "--override-reason",
        default="",
        help="Required reason when --operator-override is used.",
    )
    cmd.add_argument(
        "--override-scope",
        choices=("edit-only",),
        default="edit-only",
        help="Override scope. Only edit-only is currently supported.",
    )
    cmd.add_argument(
        "--override-by",
        default="operator",
        help="Actor/source that requested the typed override.",
    )


__all__ = ["add_agent_loop_parser", "add_claude_loop_parser"]
