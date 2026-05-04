"""Parser wiring for the typed relaunch-loop controller."""

from __future__ import annotations

import argparse

from ..common import add_standard_output_arguments


def add_relaunch_loop_parser(sub: argparse._SubParsersAction) -> None:
    """Register the ``relaunch-loop`` subcommand."""
    cmd = sub.add_parser(
        "relaunch-loop",
        help="Typed relaunch-loop trace, queue, and dry-run dispatch controller",
    )
    cmd.add_argument(
        "--action",
        choices=("status", "emit-closure", "watch-once", "dispatch-once"),
        default="status",
        help="Controller action to run.",
    )
    cmd.add_argument("--trace-path", default="", help="Override relaunch trace JSONL path.")
    cmd.add_argument("--queue-path", default="", help="Override relaunch queue JSONL path.")
    cmd.add_argument(
        "--receipts-path",
        default="",
        help="Override relaunch receipt JSONL path.",
    )
    cmd.add_argument(
        "--emitter-actor",
        default="",
        help="Actor that closed the slice, e.g. claude or codex.",
    )
    cmd.add_argument(
        "--target-actor",
        default="",
        help="Actor that owns the next slice, e.g. codex or claude.",
    )
    cmd.add_argument("--closed-slice-id", default="", help="Closed slice id.")
    cmd.add_argument("--next-slice-id", default="", help="Next slice id.")
    cmd.add_argument("--plan-ref", default="", help="Typed plan ref for the slice.")
    cmd.add_argument("--intent", default="", help="Next-slice intent summary.")
    cmd.add_argument(
        "--packet-id",
        action="append",
        default=[],
        help="Repeatable packet id used as next-session seed evidence.",
    )
    cmd.add_argument("--commit-sha", default="", help="HEAD after slice closure.")
    cmd.add_argument(
        "--push-decision-state",
        choices=("run_devctl_push", "await_review", "await_checkpoint", "no_push_needed"),
        default="no_push_needed",
        help="Typed push-state carried by SliceClosureEvent.",
    )
    cmd.add_argument(
        "--expected-instruction-revision",
        default="",
        help="Instruction revision expected by the relaunched actor.",
    )
    cmd.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview dispatcher launch commands without spawning providers.",
    )
    cmd.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum queue rows to render for status/dispatch views.",
    )
    add_standard_output_arguments(
        cmd,
        format_choices=("md", "json"),
        default_format="md",
    )


__all__ = ["add_relaunch_loop_parser"]
