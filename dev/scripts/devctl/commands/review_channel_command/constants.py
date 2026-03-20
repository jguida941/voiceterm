"""Constants for the `devctl review-channel` command."""

from __future__ import annotations

from enum import StrEnum

PUBLISHER_FOLLOW_OUTPUT_FILENAME = "publisher_follow.ndjson"
PUBLISHER_FOLLOW_LOG_FILENAME = "publisher_follow.log"
PUBLISHER_FOLLOW_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action ensure "
    "--follow --terminal none --format json"
)
EVENT_STATUS_FALLBACK_DETAIL = "event-backed review-channel state was not ok"
RUNTIME_PATH_FIELD_NAMES = (
    "review_channel_path",
    "bridge_path",
    "rollover_dir",
    "status_dir",
    "promotion_plan_path",
    "script_dir",
)
CLI_RUNTIME_PATH_ARGS = (
    "review_channel_path",
    "bridge_path",
    "rollover_dir",
    "status_dir",
)
PUBLISHER_FOLLOW_COMMAND_ARGS = (
    "review-channel",
    "--action",
    "ensure",
    "--follow",
    "--terminal",
    "none",
    "--format",
    "json",
)
FAILED_START_HEARTBEAT_FIELDS = {
    "snapshots_emitted": 0,
    "reviewer_mode": "unknown",
    "stop_reason": "failed_start",
}
POST_REQUIRED_ARGS = (
    ("from_agent", "--from-agent is required for review-channel post."),
    ("to_agent", "--to-agent is required for review-channel post."),
    ("kind", "--kind is required for review-channel post."),
    ("summary", "--summary is required for review-channel post."),
)
REVIEWER_CHECKPOINT_REQUIRED_ARGS = (
    ("verdict", "--verdict is required for review-channel reviewer-checkpoint."),
    (
        "open_findings",
        "--open-findings is required for review-channel reviewer-checkpoint.",
    ),
    (
        "instruction",
        "--instruction is required for review-channel reviewer-checkpoint.",
    ),
    (
        "reviewed_scope_item",
        "--reviewed-scope-item is required for review-channel reviewer-checkpoint.",
    ),
)
COMMON_NONNEGATIVE_LIMITS = (
    ("--await-ack-seconds", "await_ack_seconds", 0),
    ("--max-follow-snapshots", "max_follow_snapshots", 0),
)
COMMON_POSITIVE_LIMITS = (
    ("--follow-interval-seconds", "follow_interval_seconds", 120),
    ("--stale-minutes", "stale_minutes", 30),
    ("--expires-in-minutes", "expires_in_minutes", 30),
)


class ReviewChannelAction(StrEnum):
    """Typed action ids for the transitional review-channel command surface."""

    LAUNCH = "launch"
    ROLLOVER = "rollover"
    STATUS = "status"
    IMPLEMENTER_WAIT = "implementer-wait"
    ENSURE = "ensure"
    REVIEWER_HEARTBEAT = "reviewer-heartbeat"
    REVIEWER_CHECKPOINT = "reviewer-checkpoint"
    PROMOTE = "promote"
    POST = "post"
    WATCH = "watch"
    INBOX = "inbox"
    ACK = "ack"
    DISMISS = "dismiss"
    APPLY = "apply"
    HISTORY = "history"
    BRIDGE_POLL = "bridge-poll"


EVENT_ACTION_SET = frozenset(
    {
        ReviewChannelAction.POST,
        ReviewChannelAction.WATCH,
        ReviewChannelAction.INBOX,
        ReviewChannelAction.ACK,
        ReviewChannelAction.DISMISS,
        ReviewChannelAction.APPLY,
        ReviewChannelAction.HISTORY,
    }
)
REVIEWER_STATE_ACTION_SET = frozenset(
    {
        ReviewChannelAction.REVIEWER_HEARTBEAT,
        ReviewChannelAction.REVIEWER_CHECKPOINT,
    }
)
FOLLOW_JSON_ACTIONS = frozenset(
    {
        ReviewChannelAction.WATCH,
        ReviewChannelAction.ENSURE,
        ReviewChannelAction.REVIEWER_HEARTBEAT,
    }
)
PACKET_TRANSITION_ACTIONS = frozenset(
    {
        ReviewChannelAction.ACK,
        ReviewChannelAction.DISMISS,
        ReviewChannelAction.APPLY,
    }
)
LIMITED_QUERY_ACTIONS = frozenset(
    {
        ReviewChannelAction.INBOX,
        ReviewChannelAction.WATCH,
        ReviewChannelAction.HISTORY,
    }
)
