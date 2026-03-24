"""Recovery-command templates and stale-peer attention contract."""

from __future__ import annotations

import os
import sys

from ..runtime.role_profile import TandemRole

_DEVCTL_INTERPRETER = os.path.basename(sys.executable)
"""Interpreter name matching the runtime that loaded this module."""

REVIEW_CHANNEL_STATUS_INSPECT_COMMAND = f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action status --terminal none --format json --execution-mode markdown-bridge --refresh-bridge-heartbeat-if-stale"
REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND = f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action launch --terminal terminal-app --format json --execution-mode markdown-bridge --refresh-bridge-heartbeat-if-stale"
REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND = f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action ensure --start-publisher-if-missing --terminal none --format json --execution-mode markdown-bridge"
REVIEW_CHANNEL_ENSURE_FOLLOW_COMMAND = f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action ensure --follow --terminal none --format json --execution-mode markdown-bridge"
REVIEW_CHANNEL_REVIEWER_FOLLOW_COMMAND = f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action reviewer-heartbeat --follow --terminal none --format json --execution-mode markdown-bridge --auto-promote --follow-interval-seconds 150 --follow-inactivity-timeout-seconds 3600"

ATTENTION_OWNER_ROLE: dict[str, TandemRole] = {
    "codex": TandemRole.REVIEWER,
    "claude": TandemRole.IMPLEMENTER,
    "operator": TandemRole.OPERATOR,
}

_STALE_PEER_RECOVERY_ROWS: tuple[tuple[str, dict[str, str | None | TandemRole]], ...] = (
    ("inactive", {
        "guard_behavior": "none",
        "owner": "system",
        "summary": (
            "Review loop is in an inactive mode; live heartbeat enforcement is suspended."
        ),
        "recovery": (
            "Resume with `reviewer_mode=active_dual_agent` before expecting live reviewer freshness."
        ),
        "recommended_command": None,
    }),
    ("runtime_missing", {
        "guard_behavior": "block_loop",
        "owner": "system",
        "summary": (
            "Reviewer runtime is missing while dual-agent mode is still declared active."
        ),
        "recovery": (
            "Restart the repo-owned follow runtime. Do not rewrite `Reviewer mode`; "
            "the daemon is a publisher/supervisor path, not the workflow authority."
        ),
        "recommended_command": REVIEW_CHANNEL_ENSURE_FOLLOW_COMMAND,
    }),
    ("reviewer_heartbeat_missing", {
        "guard_behavior": "block_launch",
        "owner": "codex",
        "summary": "Codex reviewer heartbeat is missing; the loop is not safely live.",
        "recovery": (
            "Refresh or relaunch the reviewer lane; do not trust the bridge until "
            "Last Codex poll is visible again."
        ),
        "recommended_command": REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND,
    }),
    ("reviewer_heartbeat_stale", {
        "guard_behavior": "block_launch",
        "owner": "codex",
        "summary": (
            "Codex reviewer heartbeat is stale; do not treat the current review loop as live."
        ),
        "recovery": (
            "Relaunch or restore the reviewer lane, then confirm Last Codex poll "
            "advances before trusting the bridge again."
        ),
        "recommended_command": REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND,
    }),
    ("reviewer_overdue", {
        "guard_behavior": "block_launch",
        "owner": "codex",
        "summary": (
            "Codex reviewer is overdue; the controller should escalate or attempt automatic recovery."
        ),
        "recovery": (
            "Relaunch the reviewer lane. If the reviewer cannot be restored, "
            "consider downgrading to single_agent mode."
        ),
        "recommended_command": REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND,
    }),
    ("reviewer_poll_due", {
        "guard_behavior": "warn",
        "owner": "codex",
        "summary": (
            "Codex reviewer poll is due; refresh the bridge before the five-minute heartbeat window expires."
        ),
        "recovery": (
            "Refresh Last Codex poll, the reviewed worktree hash, and the current verdict before continuing side work."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    }),
    ("claude_status_missing", {
        "guard_behavior": "warn",
        "owner": "claude",
        "summary": (
            "Claude lane has not published Claude Status; the next loop cycle is waiting on implementer state."
        ),
        "recovery": (
            "Claude should rewrite Claude Status and keep polling for the next instruction instead of silently idling."
        ),
        "recommended_command": None,
    }),
    ("claude_ack_missing", {
        "guard_behavior": "warn",
        "owner": "claude",
        "summary": (
            "Claude has not acknowledged the live instruction yet; the loop is waiting on implementer ACK."
        ),
        "recovery": (
            "Claude should write Claude Ack for the current instruction before starting the next coding slice."
        ),
        "recommended_command": None,
    }),
    ("claude_ack_stale", {
        "guard_behavior": "block_loop",
        "owner": "claude",
        "summary": "Claude ACK does not match the current reviewer instruction revision.",
        "recovery": (
            "Claude must repoll the bridge, acknowledge the current instruction revision in Claude Ack, and only then continue coding."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    }),
    ("reviewer_supervisor_required", {
        "guard_behavior": "block_loop",
        "owner": "codex",
        "summary": (
            "Review is pending but the repo-owned reviewer supervisor follow loop is not running."
        ),
        "recovery": (
            "Start the reviewer supervisor follow loop so pending review work is driven through repo-owned reviewer actions instead of passive status."
        ),
        "recommended_command": REVIEW_CHANNEL_REVIEWER_FOLLOW_COMMAND,
    }),
    ("waiting_on_peer", {
        "guard_behavior": "warn",
        "owner": "system",
        "summary": (
            "The review loop is waiting on peer-visible bridge state before the next cycle can begin."
        ),
        "recovery": (
            "Inspect the bridge-owned sections and restore the missing peer state before promoting another slice."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    }),
    ("checkpoint_required", {
        "guard_behavior": "block_launch",
        "owner": "system",
        "summary": (
            "The current worktree has exceeded the checkpoint budget; do not keep editing until a checkpoint is cut."
        ),
        "recovery": (
            "Cut a checkpoint before continuing to edit. Re-check the repo-governance push budget after the checkpoint lands."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    }),
    ("review_follow_up_required", {
        "guard_behavior": "warn",
        "owner": "codex",
        "summary": (
            "Implementer-owned state changed; reviewer follow-up is required before the verdict and current instruction can advance."
        ),
        "recovery": (
            "Codex should inspect the current diff, refresh bridge verdict/findings/hash, and then let the reviewer follow loop resume."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    }),
    ("reviewed_hash_stale", {
        "guard_behavior": "warn",
        "owner": "codex",
        "summary": (
            "The worktree has changed since the last reviewed hash; verdict and findings may be stale."
        ),
        "recovery": (
            "Codex should re-review the current tree and refresh the bridge verdict/findings/hash before promotion."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    }),
    ("implementer_completion_stall", {
        "guard_behavior": "warn",
        "owner": "claude",
        "summary": (
            "Implementer appears parked on reviewer polling while the current instruction is still active."
        ),
        "recovery": (
            "The implementer should resume coding on the active instruction instead of waiting for the next reviewer promotion."
        ),
        "recommended_command": None,
    }),
    ("dual_agent_idle", {
        "guard_behavior": "warn",
        "owner": "codex",
        "summary": (
            "Reviewer and implementer both look idle while active_dual_agent is enabled."
        ),
        "recovery": (
            "Run reviewer-follow with auto-promotion so the bridge promotes the next concrete scoped checklist task instead of repeating generic continue instructions."
        ),
        "recommended_command": REVIEW_CHANNEL_REVIEWER_FOLLOW_COMMAND,
    }),
    ("publisher_missing", {
        "guard_behavior": "warn",
        "owner": "system",
        "summary": (
            "Persistent heartbeat publisher is required but not running; status projections are not being pushed automatically."
        ),
        "recovery": (
            "Start the publisher with `review-channel ensure --start-publisher-if-missing` or manually with `review-channel ensure --follow`."
        ),
        "recommended_command": REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND,
    }),
    ("publisher_failed_start", {
        "guard_behavior": "warn",
        "owner": "system",
        "summary": (
            "Publisher was started but exited immediately; the bridge or runtime environment may be misconfigured."
        ),
        "recovery": (
            "Check the publisher log for startup errors, then retry with `review-channel ensure --start-publisher-if-missing`."
        ),
        "recommended_command": REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND,
    }),
    ("publisher_detached_exit", {
        "guard_behavior": "warn",
        "owner": "system",
        "summary": (
            "Publisher was running but exited unexpectedly; the last heartbeat file records the pre-exit state."
        ),
        "recovery": (
            "Restart the publisher with `review-channel ensure --start-publisher-if-missing`. Check the log for the exit cause."
        ),
        "recommended_command": REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND,
    }),
    ("healthy", {
        "guard_behavior": "none",
        "owner": "system",
        "summary": "Review loop signals are fresh.",
        "recovery": "Continue the scoped review/coding loop.",
        "recommended_command": None,
    }),
)

STALE_PEER_RECOVERY: dict[str, dict[str, str | None | TandemRole]] = dict(
    _STALE_PEER_RECOVERY_ROWS
)
