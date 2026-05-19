"""Review-channel query and follow parser arguments."""

from __future__ import annotations

from typing import Any, Callable


def build_query_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        *_packet_lookup_arguments(arg_builder),
        *_apply_attestation_arguments(arg_builder),
        *_query_filter_arguments(arg_builder),
        *_follow_control_arguments(arg_builder),
    ]


def _packet_lookup_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder(
            "--packet-id",
            help="Packet id for ack/dismiss/apply or explicit post id override",
        ),
        arg_builder(
            "--trace-id",
            help="Trace id for history queries or explicit post trace override",
        ),
        arg_builder(
            "--actor",
            help=(
                "Actor id applying a packet transition or typed role action; "
                "validated against typed collaboration/runtime state"
            ),
        ),
        arg_builder(
            "--actor-role",
            help=(
                "Role for --actor when the action subject differs from the "
                "packet target role, such as reviewer posting a finding to a "
                "dashboard or implementer lane."
            ),
        ),
        arg_builder(
            "--control-decision-input",
            default="",
            help=(
                "AgentLoopDecision/control decision JSON path enforced before "
                "state-changing review-channel actions."
            ),
        ),
        arg_builder(
            "--executor-actor",
            help=(
                "Optional local executor actor when a typed lifecycle command "
                "is run as an authorized proxy for --actor."
            ),
        ),
        arg_builder(
            "--executor-role",
            help="Optional local executor role for proxied lifecycle commands.",
        ),
        arg_builder(
            "--executor-session-id",
            help=(
                "Optional local executor session id for proxied lifecycle "
                "commands."
            ),
        ),
        arg_builder(
            "--proxy-authority-ref",
            help=(
                "Typed authority reference that permits executor_actor to run "
                "the scoped lifecycle action for --actor."
            ),
        ),
        arg_builder(
            "--revision",
            help=(
                "Expected current instruction revision for typed role actions "
                "such as `implementer-ack`."
            ),
        ),
        arg_builder(
            "--notes",
            help="Optional notes for typed role actions such as `implementer-ack`.",
        ),
        arg_builder(
            "--semantic-action-item",
            action="append",
            default=[],
            help=(
                "Repeatable JSON object for `--action ingest` describing one "
                "PacketSemanticActionItem extracted from the packet body."
            ),
        ),
    ]


def _apply_attestation_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder(
            "--attestation-kind",
            help="PacketGuardAttestation kind for apply transitions",
        ),
        arg_builder(
            "--run-record-id",
            action="append",
            default=[],
            help="Repeatable RunRecord id proving an apply transition",
        ),
        arg_builder(
            "--action-result-id",
            action="append",
            default=[],
            help=(
                "Repeatable ActionResult id proving an apply transition or "
                "typed-evidence-required packet post."
            ),
        ),
        arg_builder(
            "--commit-sha",
            help=(
                "Commit SHA bound to code-changing apply transitions or "
                "typed-evidence-required packet posts."
            ),
        ),
        arg_builder(
            "--plan-revision-before",
            help="MasterPlan revision before a plan-mutating apply",
        ),
        arg_builder(
            "--plan-revision-after",
            help="MasterPlan revision after a plan-mutating apply",
        ),
        arg_builder(
            "--evidence-artifact-path",
            action="append",
            default=[],
            help=(
                "Repeatable evidence artifact path for apply attestation or "
                "typed-evidence-required packet post."
            ),
        ),
        arg_builder(
            "--operator-signature",
            help="Operator signature for approval apply transitions",
        ),
    ]


def _query_filter_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder(
            "--target",
            help=(
                "Legacy delivery endpoint id filter for inbox/watch. Prefer "
                "`--target-role` and `--target-session-id` for typed lane "
                "routing."
            ),
        ),
        arg_builder(
            "--status",
            choices=["pending", "acked", "dismissed", "applied", "expired"],
            help="Packet status filter for inbox/watch",
        ),
        arg_builder(
            "--limit",
            type=int,
            default=20,
            help="Limit rows returned by inbox/history/watch",
        ),
        arg_builder(
            "--for",
            "--for-agent",
            dest="for_agent",
            help="Scope agent_sync sync-status output to one agent_id row",
        ),
        arg_builder(
            "--since-event-id",
            dest="since_event_id",
            help=(
                "Diff mode for sync-status: include only rows whose emission "
                "or consumption cursor advanced past this rev_evt_NNNN id"
            ),
        ),
        arg_builder(
            "--include-outcomes",
            action="store_true",
            help="Attach a typed PacketOutcomeLedger to history rows.",
        ),
        arg_builder(
            "--grouped",
            action="store_true",
            help=(
                "Render review-channel history as an OperationalSummaryView "
                "with grouped pipeline transit, orphan action requests, and "
                "lifecycle buckets."
            ),
        ),
    ]


def _follow_control_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder(
            "--follow",
            action="store_true",
            help="Stream NDJSON snapshots when the watched packet set changes",
        ),
        arg_builder(
            "--start-publisher-if-missing",
            action="store_true",
            help=(
                "For `ensure`, start the persistent heartbeat/status publisher "
                "when active mode requires it and no publisher is running"
            ),
        ),
        arg_builder(
            "--max-follow-snapshots",
            type=int,
            default=0,
            help="Max snapshots in follow mode (0=unbounded)",
        ),
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
                "Maximum peer-side inactivity window for follow-enabled "
                "review-channel actions. The loop keeps polling until the peer has "
                "shown no progress for this many seconds."
            ),
        ),
        arg_builder(
            "--stale-minutes",
            type=int,
            default=30,
            help="Staleness threshold for watch views",
        ),
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
