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
        *_agent_packet_arguments(arg_builder),
        arg_builder(
            "--kind",
            choices=sorted(VALID_PACKET_KINDS),
            help=(
                "Review packet kind for `--action post`. "
                "`plan_gap_review` and `plan_patch_review` also require "
                "`--target-kind plan`, `--target-ref`, `--target-revision`, "
                "at least one `--anchor-ref`, and `--intake-ref`; "
                "`plan_patch_review` also requires `--mutation-op`."
            ),
        ),
        arg_builder("--summary", help="Short packet summary for post/watch/history views"),
        arg_builder("--body", help="Inline packet body for `--action post`"),
        arg_builder(
            "--body-file",
            help="Optional UTF-8 markdown/text file used as the packet body",
        ),
        arg_builder(
            "--evidence-ref",
            action="append",
            default=[],
            help="Repeatable evidence reference",
        ),
        arg_builder(
            "--confidence",
            type=float,
            default=1.0,
            help="Packet confidence between 0.0 and 1.0",
        ),
        arg_builder(
            "--requested-action",
            default="review_only",
            help="Requested action on a packet",
        ),
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
                "`task_pack:<local-state-dir>/exports/task_pack.json`"
            ),
        ),
        arg_builder(
            "--context-pack-adapter-profile",
            choices=["canonical", "codex", "claude", "gemini"],
            default="canonical",
            help="Adapter profile recorded on attached context-pack refs",
        ),
        *_packet_target_arguments(arg_builder),
        *_packet_runtime_approval_arguments(arg_builder),
    ]


def _packet_target_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder(
            "--target-kind",
            choices=sorted(VALID_TARGET_KINDS),
            help=(
                "Optional packet target kind; planning packets must use `plan`. "
                "`plan_gap_review` and `plan_patch_review` require "
                "`--target-kind plan`."
            ),
        ),
        arg_builder(
            "--target-ref",
            help=(
                "Canonical target ref for plan/policy/artifact review packets. "
                "Required for `plan_gap_review` and `plan_patch_review`, for "
                "example `plan://MP-377/platform_authority_loop`."
            ),
        ),
        arg_builder(
            "--target-revision",
            help=(
                "Expected target revision or digest recorded on plan review "
                "packets. Required for `plan_gap_review` and "
                "`plan_patch_review`, for example `sha256:abc123`."
            ),
        ),
        arg_builder(
            "--anchor-ref",
            action="append",
            default=[],
            help=(
                "Repeatable typed plan anchor ref. `plan_gap_review` and "
                "`plan_patch_review` require at least one. Format "
                "`<anchor-type>:<anchor-token>` where `<anchor-type>` is one "
                "of `checklist`, `section`, `session_resume`, `progress`, or "
                "`audit`; `<anchor-token>` must start alphanumeric and may "
                "then use letters, digits, `.`, `_`, or `-`. Examples: "
                "`checklist:phase_2a`, `progress:finding_closure_gate`."
            ),
        ),
        arg_builder(
            "--intake-ref",
            help=(
                "Canonical intake packet ref that authorized the current plan "
                "review or patch. Required for `plan_gap_review` and "
                "`plan_patch_review`, for example "
                "`intake://session-2026-03-19`."
            ),
        ),
        arg_builder(
            "--mutation-op",
            choices=sorted(VALID_PLAN_MUTATION_OPS),
            help=(
                "Plan mutation operation for `plan_patch_review` packets. "
                "Required on `plan_patch_review` and invalid on "
                "`plan_gap_review`."
            ),
        ),
        arg_builder(
            "--target-role",
            help=(
                "Optional role discriminator for the target agent (e.g. "
                "`coder`, `dashboard`). Per rev_pkt_2472: when an agent name "
                "like `claude` is shared by multiple session-roles, this "
                "narrows the packet to exactly one of them. Consumers fail "
                "closed on mismatch when the field is set."
            ),
        ),
        arg_builder(
            "--target-session-id",
            help=(
                "Optional session-id discriminator for the target agent. "
                "Per rev_pkt_2472: pins the packet to one specific provider "
                "session so a dashboard role and implementer role on the same "
                "provider cannot both consume the same packet. "
                "Consumers fail closed on mismatch when the field is set."
            ),
        ),
        arg_builder(
            "--requested-session-visibility",
            choices=["dashboard_only", "headless", "visible"],
            help=(
                "Optional visibility request for the targeted actor/session. "
                "`dashboard_only` records typed attention for the bound "
                "dashboard poller, `visible` requests a user-visible session, "
                "and `headless` requires explicit typed approval/proof before "
                "any detached launch can satisfy the packet."
            ),
        ),
    ]


def _packet_runtime_approval_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder(
            "--pipeline-generation",
            help="Runtime pipeline generation for `commit_approval` packets",
        ),
        arg_builder(
            "--staged-snapshot-hash",
            help="Staged snapshot hash bound to a runtime approval packet",
        ),
        arg_builder(
            "--guard-results-summary",
            help="Typed guard summary carried on a runtime approval packet",
        ),
        arg_builder(
            "--full-guard-bundle-evidence",
            help=(
                "Typed guard-bundle evidence label required for "
                "`stage_commit_pipeline` action_request packets. Use one of "
                "`bundle.runtime`, `bundle.tooling`, `bundle.docs`, "
                "`bundle.release`, or `--profile ci`."
            ),
        ),
    ]


def _agent_packet_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
    return [
        arg_builder(
            "--from-agent",
            help=(
                "Posting agent id for packet writes; validated against typed "
                "collaboration/runtime state"
            ),
        ),
        arg_builder(
            "--to-agent",
            help=(
                "Target agent id for packet writes; validated against typed "
                "collaboration/runtime state"
            ),
        ),
    ]


def build_query_arguments(arg_builder: Callable[..., Any]) -> list[Any]:
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
                "Actor id applying an ack/dismiss/apply transition; validated "
                "against typed collaboration/runtime state"
            ),
        ),
        arg_builder("--attestation-kind", help="PacketGuardAttestation kind for apply transitions"),
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
            help="Repeatable ActionResult id proving an apply transition",
        ),
        arg_builder(
            "--commit-sha",
            help="Commit SHA bound to code-changing apply transitions",
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
            help="Repeatable evidence artifact path for apply attestation",
        ),
        arg_builder(
            "--operator-signature",
            help="Operator signature for approval apply transitions",
        ),
        arg_builder("--target", help="Target agent id filter for inbox/watch"),
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
                "Maximum Claude-side inactivity window for follow-enabled "
                "review-channel actions. The loop keeps polling until Claude has "
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
