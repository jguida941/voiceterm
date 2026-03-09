"""Parser wiring for the transitional `devctl review-channel` surface.

This parser exists for the current bridge-gated flow described in:

- `AGENTS.md`
- `dev/active/INDEX.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/review_channel.md`
- `code_audit.md`
"""

from __future__ import annotations

import argparse

from .common import add_standard_output_arguments
from .review_channel import (
    DEFAULT_ROLLOVER_ACK_WAIT_SECONDS,
    DEFAULT_BRIDGE_REL,
    DEFAULT_ROLLOVER_DIR_REL,
    DEFAULT_ROLLOVER_THRESHOLD_PCT,
    DEFAULT_REVIEW_CHANNEL_REL,
    DEFAULT_TERMINAL_PROFILE,
)
from .review_channel_events import (
    DEFAULT_PACKET_TTL_MINUTES,
    DEFAULT_REVIEW_ARTIFACT_ROOT_REL,
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    DEFAULT_REVIEW_PROJECTIONS_DIR_REL,
    DEFAULT_REVIEW_STATE_JSON_REL,
)
from .review_channel_state import DEFAULT_REVIEW_STATUS_DIR_REL


def _build_review_channel_parser(
    sub: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    cmd = sub.add_parser(
        "review-channel",
        help="Manage review-channel launch, status, and packet state",
    )
    cmd.add_argument(
        "--action",
        choices=[
            "launch",
            "rollover",
            "status",
            "post",
            "watch",
            "inbox",
            "ack",
            "dismiss",
            "apply",
            "history",
        ],
        required=True,
        help="Review-channel action",
    )
    cmd.add_argument(
        "--execution-mode",
        choices=["auto", "markdown-bridge", "overlay"],
        default="auto",
        help=(
            "Auto-detect the current review-channel transport. Today only the "
            "markdown bridge is implemented; overlay mode is reserved for later."
        ),
    )
    return cmd


def _add_review_channel_launch_arguments(cmd: argparse.ArgumentParser) -> None:
    cmd.add_argument(
        "--terminal",
        choices=["terminal-app", "none"],
        default="terminal-app",
        help="Launch via Terminal.app on macOS or just emit scripts/report output",
    )
    cmd.add_argument(
        "--terminal-profile",
        default=DEFAULT_TERMINAL_PROFILE,
        help=(
            "Terminal.app profile to apply on live launch. "
            "`auto-dark` picks a dark built-in profile when available; "
            "`default` leaves Terminal.app unchanged."
        ),
    )
    cmd.add_argument(
        "--review-channel-path",
        default=DEFAULT_REVIEW_CHANNEL_REL,
        help="Path to the active review-channel plan markdown",
    )
    cmd.add_argument(
        "--bridge-path",
        default=DEFAULT_BRIDGE_REL,
        help="Path to the live markdown bridge file",
    )
    cmd.add_argument(
        "--rollover-dir",
        default=DEFAULT_ROLLOVER_DIR_REL,
        help="Directory where repo-visible rollover handoff bundles are written",
    )
    cmd.add_argument(
        "--status-dir",
        default=DEFAULT_REVIEW_STATUS_DIR_REL,
        help="Directory where latest bridge-backed status projections are written",
    )
    cmd.add_argument(
        "--artifact-root",
        default=DEFAULT_REVIEW_ARTIFACT_ROOT_REL,
        help="Root directory for canonical event-backed review-channel artifacts",
    )
    cmd.add_argument(
        "--state-json",
        default=DEFAULT_REVIEW_STATE_JSON_REL,
        help="Canonical reduced review-channel state JSON path",
    )
    cmd.add_argument(
        "--emit-projections",
        default=DEFAULT_REVIEW_PROJECTIONS_DIR_REL,
        help="Directory where canonical event-backed projections are written",
    )
    cmd.add_argument(
        "--rollover-threshold-pct",
        type=int,
        default=DEFAULT_ROLLOVER_THRESHOLD_PCT,
        help=(
            "Context-remaining percentage that should trigger a planned self-relaunch "
            "before compaction"
        ),
    )
    cmd.add_argument(
        "--rollover-trigger",
        choices=["context-threshold", "manual", "peer-stale"],
        default="context-threshold",
        help="Reason recorded in the rollover handoff bundle",
    )
    cmd.add_argument(
        "--await-ack-seconds",
        type=int,
        default=DEFAULT_ROLLOVER_ACK_WAIT_SECONDS,
        help=(
            "How long a live rollover should wait for visible Codex/Claude ACK lines "
            "from the fresh conductor sessions before failing closed. "
            "Must be greater than zero for rollover."
        ),
    )
    cmd.add_argument(
        "--codex-workers",
        type=int,
        default=8,
        help="Requested Codex reviewer-worker budget advertised to the conductor",
    )
    cmd.add_argument(
        "--claude-workers",
        type=int,
        default=8,
        help="Requested Claude coding-worker budget advertised to the conductor",
    )
    cmd.add_argument(
        "--dangerous",
        action="store_true",
        help=(
            "Use no-prompt provider flags (`codex --dangerously-bypass-...`, "
            "`claude --dangerously-skip-permissions`) instead of the safer auto modes"
        ),
    )
    cmd.add_argument(
        "--script-dir",
        help="Optional directory for generated conductor launch scripts",
    )
    cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the launch bundle without opening Terminal.app windows",
    )


def _add_review_channel_packet_arguments(cmd: argparse.ArgumentParser) -> None:
    cmd.add_argument(
        "--from-agent",
        choices=["codex", "claude", "operator", "system"],
        help="Posting agent for event-backed packet writes",
    )
    cmd.add_argument(
        "--to-agent",
        choices=["codex", "claude", "operator", "system"],
        help="Target agent for event-backed packet writes",
    )
    cmd.add_argument(
        "--kind",
        choices=[
            "finding",
            "question",
            "draft",
            "action_request",
            "approval_request",
            "decision",
            "system_notice",
        ],
        help="Review packet kind for `--action post`",
    )
    cmd.add_argument(
        "--summary",
        help="Short packet summary for post/watch/history views",
    )
    cmd.add_argument(
        "--body",
        help="Inline packet body for `--action post`",
    )
    cmd.add_argument(
        "--body-file",
        help="Optional UTF-8 markdown/text file used as the packet body",
    )
    cmd.add_argument(
        "--evidence-ref",
        action="append",
        default=[],
        help="Repeatable evidence reference attached to a packet",
    )
    cmd.add_argument(
        "--confidence",
        type=float,
        default=1.0,
        help="Packet confidence value between 0.0 and 1.0",
    )
    cmd.add_argument(
        "--requested-action",
        default="review_only",
        help="Requested action attached to a packet",
    )
    cmd.add_argument(
        "--policy-hint",
        choices=[
            "review_only",
            "stage_draft",
            "operator_approval_required",
            "safe_auto_apply",
        ],
        default="review_only",
        help="Policy hint attached to a packet",
    )
    cmd.add_argument(
        "--approval-required",
        action="store_true",
        help="Mark the packet as requiring explicit operator approval",
    )


def _add_review_channel_query_arguments(cmd: argparse.ArgumentParser) -> None:
    cmd.add_argument(
        "--packet-id",
        help="Packet id for ack/dismiss/apply or explicit post id override",
    )
    cmd.add_argument(
        "--trace-id",
        help="Trace id for history queries or explicit post trace override",
    )
    cmd.add_argument(
        "--actor",
        choices=["codex", "claude", "operator", "system"],
        help="Actor applying an ack/dismiss/apply transition",
    )
    cmd.add_argument(
        "--target",
        choices=["codex", "claude", "operator", "system"],
        help="Target agent filter for inbox/watch",
    )
    cmd.add_argument(
        "--status",
        choices=["pending", "acked", "dismissed", "applied", "expired"],
        help="Packet status filter for inbox/watch",
    )
    cmd.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit rows returned by inbox/history/watch",
    )
    cmd.add_argument(
        "--follow",
        action="store_true",
        help="Request a watch/follow view; current CLI emits one snapshot per run",
    )
    cmd.add_argument(
        "--stale-minutes",
        type=int,
        default=30,
        help="Staleness threshold used by watch projections",
    )


def _add_review_channel_event_context_arguments(cmd: argparse.ArgumentParser) -> None:
    cmd.add_argument(
        "--session-id",
        default=DEFAULT_REVIEW_CHANNEL_SESSION_ID,
        help="Stable session id for event-backed packet writes",
    )
    cmd.add_argument(
        "--plan-id",
        default=DEFAULT_REVIEW_CHANNEL_PLAN_ID,
        help="Plan id recorded on event-backed packet writes",
    )
    cmd.add_argument(
        "--controller-run-id",
        help="Optional controller run id recorded on event-backed packet writes",
    )
    cmd.add_argument(
        "--expires-in-minutes",
        type=int,
        default=DEFAULT_PACKET_TTL_MINUTES,
        help="Expiry horizon for newly posted packets",
    )


def add_review_channel_parser(sub: argparse._SubParsersAction) -> None:
    """Register the review-channel parser."""
    cmd = _build_review_channel_parser(sub)
    _add_review_channel_launch_arguments(cmd)
    _add_review_channel_packet_arguments(cmd)
    _add_review_channel_query_arguments(cmd)
    _add_review_channel_event_context_arguments(cmd)
    add_standard_output_arguments(cmd)
