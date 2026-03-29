"""Shared review-channel parser argument groups."""

from __future__ import annotations

from typing import Any, Callable

from .events import (
    DEFAULT_PACKET_TTL_MINUTES,
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
)
from .packet_contract import (
    VALID_PACKET_KINDS,
    VALID_PLAN_MUTATION_OPS,
    VALID_TARGET_KINDS,
)


def build_packet_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder("--from-agent", choices=("codex", "claude", "operator", "system"), help="Posting agent for packet writes"),
        arg_builder("--to-agent", choices=("codex", "claude", "operator", "system"), help="Target agent for packet writes"),
        arg_builder(
            "--kind",
            choices=sorted(VALID_PACKET_KINDS),
            help="Review packet kind for `--action post`",
        ),
        arg_builder("--summary", help="Short packet summary for post/watch/history views"),
        arg_builder("--body", help="Inline packet body for `--action post`"),
        arg_builder("--body-file", help="Optional UTF-8 markdown/text file used as the packet body"),
        arg_builder("--evidence-ref", action="append", default=[], help="Repeatable evidence reference"),
        arg_builder("--confidence", type=float, default=1.0, help="Packet confidence between 0.0 and 1.0"),
        arg_builder("--requested-action", default="review_only", help="Requested action on a packet"),
        arg_builder(
            "--policy-hint",
            choices=["review_only", "stage_draft", "operator_approval_required", "safe_auto_apply"],
            default="review_only",
            help="Policy hint attached to a packet",
        ),
        arg_builder(
            "--approval-required",
            action="store_true",
            help="Mark packet as requiring explicit operator approval",
        ),
        arg_builder(
            "--context-pack-ref",
            action="append",
            default=[],
            help=(
                "Repeatable attached memory-pack ref in kind:path form, for example "
                "`task_pack:.voiceterm/memory/exports/task_pack.json`"
            ),
        ),
        arg_builder(
            "--context-pack-adapter-profile",
            choices=["canonical", "codex", "claude", "gemini"],
            default="canonical",
            help="Adapter profile recorded on attached context-pack refs",
        ),
        arg_builder(
            "--target-kind",
            choices=sorted(VALID_TARGET_KINDS),
            help="Optional packet target kind; planning packets must use `plan`.",
        ),
        arg_builder("--target-ref", help="Canonical target ref for plan/policy/artifact review packets"),
        arg_builder(
            "--target-revision",
            help="Expected target revision or digest recorded on plan review packets",
        ),
        arg_builder(
            "--anchor-ref",
            action="append",
            default=[],
            help="Repeatable typed anchor ref, for example `checklist:phase_2a`",
        ),
        arg_builder(
            "--intake-ref",
            help="Canonical intake packet ref that authorized the current plan review or patch",
        ),
        arg_builder(
            "--mutation-op",
            choices=sorted(VALID_PLAN_MUTATION_OPS),
            help="Plan mutation operation for `plan_patch_review` packets",
        ),
    ]


def build_query_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder("--packet-id", help="Packet id for ack/dismiss/apply or explicit post id override"),
        arg_builder("--trace-id", help="Trace id for history queries or explicit post trace override"),
        arg_builder("--actor", choices=("codex", "claude", "operator", "system"), help="Actor applying an ack/dismiss/apply transition"),
        arg_builder("--target", choices=("codex", "claude", "operator", "system"), help="Target agent filter for inbox/watch"),
        arg_builder(
            "--status",
            choices=["pending", "acked", "dismissed", "applied", "expired"],
            help="Packet status filter for inbox/watch",
        ),
        arg_builder("--limit", type=int, default=20, help="Limit rows returned by inbox/history/watch"),
        arg_builder(
            "--follow",
            action="store_true",
            help="Stream NDJSON snapshots when the watched packet set changes",
        ),
        arg_builder(
            "--start-publisher-if-missing",
            action="store_true",
            help="For `ensure`, start the persistent heartbeat/status publisher when active mode requires it and no publisher is running",
        ),
        arg_builder("--max-follow-snapshots", type=int, default=0, help="Max snapshots in follow mode (0=unbounded)"),
        arg_builder(
            "--follow-interval-seconds",
            type=int,
            default=150,
            help="Heartbeat/status stream cadence for follow-enabled review-channel actions",
        ),
        arg_builder(
            "--follow-inactivity-timeout-seconds",
            type=int,
            default=3600,
            help=(
                "Maximum Claude-side inactivity window for follow-enabled "
                "review-channel actions. The loop keeps polling until Claude has "
                "shown no progress for this many seconds."
            ),
        ),
        arg_builder("--stale-minutes", type=int, default=30, help="Staleness threshold for watch views"),
        arg_builder(
            "--reviewer-overdue-seconds",
            type=int,
            default=900,
            help=(
                "Reviewer age threshold (seconds) for controller escalation. "
                "When the reviewer heartbeat is stale beyond this limit, the "
                "attention state escalates to `reviewer_overdue`."
            ),
        ),
        arg_builder(
            "--timeout-minutes",
            type=int,
            default=0,
            help=(
                "Absolute run budget for `ensure --follow`. When >0, the "
                "publisher stops cleanly after this many minutes and writes "
                "final state with stop_reason=timed_out. 0 = no timeout."
            ),
        ),
    ]


def build_event_context_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder(
            "--session-id",
            default=DEFAULT_REVIEW_CHANNEL_SESSION_ID,
            help="Stable session id for event-backed packet writes",
        ),
        arg_builder(
            "--plan-id",
            default=DEFAULT_REVIEW_CHANNEL_PLAN_ID,
            help="Plan id recorded on event-backed packet writes",
        ),
        arg_builder("--controller-run-id", help="Optional controller run id on packet writes"),
        arg_builder(
            "--expires-in-minutes",
            type=int,
            default=DEFAULT_PACKET_TTL_MINUTES,
            help="Expiry horizon for newly posted packets",
        ),
    ]
