"""Canonical peer-heartbeat state names and stale-peer handling contract.

This module is the single source of truth for liveness state enums, threshold
constants, and documented recovery actions.  All code that checks or emits
peer-heartbeat states must import from here rather than inventing string
literals.  See ``dev/active/continuous_swarm.md`` Phase 0 for the governing
plan item.
"""

from __future__ import annotations

import os
import sys
from enum import StrEnum

from ..runtime.role_profile import TandemRole

# ---------------------------------------------------------------------------
# Peer-heartbeat state enums
# ---------------------------------------------------------------------------

class CodexPollState(StrEnum):
    """Reviewer-side poll freshness derived from ``Last Codex poll`` age."""

    MISSING = "missing"
    STALE = "stale"
    POLL_DUE = "poll_due"
    FRESH = "fresh"

class OverallLivenessState(StrEnum):
    """Aggregate loop health derived from both peer signals."""

    INACTIVE = "inactive"
    STALE = "stale"
    WAITING_ON_PEER = "waiting_on_peer"
    FRESH = "fresh"

class ReviewerMode(StrEnum):
    """Top-level reviewer operating modes for the bridge-backed loop."""

    ACTIVE_DUAL_AGENT = "active_dual_agent"
    SINGLE_AGENT = "single_agent"
    TOOLS_ONLY = "tools_only"
    PAUSED = "paused"
    OFFLINE = "offline"

REVIEWER_MODE_ALIASES: dict[str, ReviewerMode] = {
    "agents": ReviewerMode.ACTIVE_DUAL_AGENT,
    "developer": ReviewerMode.SINGLE_AGENT,
    "dev": ReviewerMode.SINGLE_AGENT,
    "tools": ReviewerMode.TOOLS_ONLY,
}
"""Human-facing shorthand accepted by CLI surfaces and normalized on write."""

REVIEWER_MODE_CLI_CHOICES = tuple(mode.value for mode in ReviewerMode) + tuple(
    REVIEWER_MODE_ALIASES.keys()
)
"""Allowed CLI values for reviewer-mode arguments."""

IMPLEMENTER_STALL_MARKERS = (
    "instruction unchanged",
    "continuing to poll",
    "waiting for codex review",
    "waiting for codex to review",
    "codex should review",
    "review and promote the next slice",
    "waiting for reviewer promotion",
)
"""Phrases in implementer status/ACK that indicate a completion-stall pattern."""

class AttentionStatus(StrEnum):
    """Machine-readable attention signals for operator/console consumers."""

    INACTIVE = "inactive"
    REVIEWER_HEARTBEAT_MISSING = "reviewer_heartbeat_missing"
    REVIEWER_HEARTBEAT_STALE = "reviewer_heartbeat_stale"
    REVIEWER_OVERDUE = "reviewer_overdue"
    REVIEWER_POLL_DUE = "reviewer_poll_due"
    CLAUDE_STATUS_MISSING = "claude_status_missing"
    CLAUDE_ACK_MISSING = "claude_ack_missing"
    WAITING_ON_PEER = "waiting_on_peer"
    REVIEWED_HASH_STALE = "reviewed_hash_stale"
    IMPLEMENTER_COMPLETION_STALL = "implementer_completion_stall"
    PUBLISHER_MISSING = "publisher_missing"
    PUBLISHER_FAILED_START = "publisher_failed_start"
    PUBLISHER_DETACHED_EXIT = "publisher_detached_exit"
    HEALTHY = "healthy"

# ---------------------------------------------------------------------------
# Threshold constants
# ---------------------------------------------------------------------------

CODEX_POLL_DUE_AFTER_SECONDS = 180
"""Codex poll is 'due' when age exceeds the 2-3 minute reviewer cadence."""

CODEX_POLL_STALE_AFTER_SECONDS = 300
"""Codex poll is 'stale' when age exceeds the five-minute heartbeat window."""

CODEX_POLL_OVERDUE_AFTER_SECONDS = 900
"""Reviewer is 'overdue' when age exceeds the controller escalation threshold."""

ACTIVE_REVIEWER_MODES = frozenset({ReviewerMode.ACTIVE_DUAL_AGENT})
INACTIVE_REVIEWER_MODES = frozenset(
    {
        ReviewerMode.SINGLE_AGENT,
        ReviewerMode.TOOLS_ONLY,
        ReviewerMode.PAUSED,
        ReviewerMode.OFFLINE,
    }
)

def normalize_reviewer_mode(value: str | None) -> ReviewerMode:
    """Normalize metadata text into one canonical reviewer mode."""
    raw = (value or "").strip().lower()
    alias = REVIEWER_MODE_ALIASES.get(raw)
    if alias is not None:
        return alias
    for mode in ReviewerMode:
        if raw == mode.value:
            return mode
    return ReviewerMode.ACTIVE_DUAL_AGENT

def reviewer_mode_is_active(value: str | None) -> bool:
    """Return True only when the bridge declares an actively enforced dual-agent loop."""
    return normalize_reviewer_mode(value) in ACTIVE_REVIEWER_MODES

# ---------------------------------------------------------------------------
# Recommended-command templates used by the recovery contract
# ---------------------------------------------------------------------------

_DEVCTL_INTERPRETER = os.path.basename(sys.executable)
"""Interpreter name matching the runtime that loaded this module."""

REVIEW_CHANNEL_STATUS_INSPECT_COMMAND = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json --refresh-bridge-heartbeat-if-stale"
)

REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action launch "
    "--terminal terminal-app --format json --refresh-bridge-heartbeat-if-stale"
)

REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND = (
    f"{_DEVCTL_INTERPRETER} dev/scripts/devctl.py review-channel --action ensure "
    "--start-publisher-if-missing --terminal none --format json"
)

# ---------------------------------------------------------------------------
# Stale-peer handling contract
# ---------------------------------------------------------------------------

ATTENTION_OWNER_ROLE: dict[str, TandemRole] = {
    "codex": TandemRole.REVIEWER,
    "claude": TandemRole.IMPLEMENTER,
    "operator": TandemRole.OPERATOR,
}

STALE_PEER_RECOVERY: dict[str, dict[str, str | None | TandemRole]] = {
    AttentionStatus.INACTIVE: {
        "guard_behavior": "none",
        "owner": "system",
        "summary": (
            "Review loop is in an inactive mode; live heartbeat enforcement is suspended."
        ),
        "recovery": (
            "Resume with `reviewer_mode=active_dual_agent` before expecting live reviewer freshness."
        ),
        "recommended_command": None,
    },
    AttentionStatus.REVIEWER_HEARTBEAT_MISSING: {
        "guard_behavior": "block_launch",
        "owner": "codex",
        "summary": (
            "Codex reviewer heartbeat is missing; the loop is not safely live."
        ),
        "recovery": (
            "Refresh or relaunch the reviewer lane; do not trust the bridge "
            "until Last Codex poll is visible again."
        ),
        "recommended_command": REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND,
    },
    AttentionStatus.REVIEWER_HEARTBEAT_STALE: {
        "guard_behavior": "block_launch",
        "owner": "codex",
        "summary": (
            "Codex reviewer heartbeat is stale; do not treat the current "
            "review loop as live."
        ),
        "recovery": (
            "Relaunch or restore the reviewer lane, then confirm Last Codex "
            "poll advances before trusting the bridge again."
        ),
        "recommended_command": REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND,
    },
    AttentionStatus.REVIEWER_OVERDUE: {
        "guard_behavior": "block_launch",
        "owner": "codex",
        "summary": (
            "Codex reviewer is overdue; the controller should escalate "
            "or attempt automatic recovery."
        ),
        "recovery": (
            "Relaunch the reviewer lane. If the reviewer cannot be restored, "
            "consider downgrading to single_agent mode."
        ),
        "recommended_command": REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND,
    },
    AttentionStatus.REVIEWER_POLL_DUE: {
        "guard_behavior": "warn",
        "owner": "codex",
        "summary": (
            "Codex reviewer poll is due; refresh the bridge before the "
            "five-minute heartbeat window expires."
        ),
        "recovery": (
            "Refresh Last Codex poll, the reviewed worktree hash, and the "
            "current verdict before continuing side work."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    },
    AttentionStatus.CLAUDE_STATUS_MISSING: {
        "guard_behavior": "warn",
        "owner": "claude",
        "summary": (
            "Claude lane has not published Claude Status; the next loop "
            "cycle is waiting on implementer state."
        ),
        "recovery": (
            "Claude should rewrite Claude Status and keep polling for the "
            "next instruction instead of silently idling."
        ),
        "recommended_command": None,
    },
    AttentionStatus.CLAUDE_ACK_MISSING: {
        "guard_behavior": "warn",
        "owner": "claude",
        "summary": (
            "Claude has not acknowledged the live instruction yet; the loop "
            "is waiting on implementer ACK."
        ),
        "recovery": (
            "Claude should write Claude Ack for the current instruction "
            "before starting the next coding slice."
        ),
        "recommended_command": None,
    },
    AttentionStatus.WAITING_ON_PEER: {
        "guard_behavior": "warn",
        "owner": "system",
        "summary": (
            "The review loop is waiting on peer-visible bridge state before "
            "the next cycle can begin."
        ),
        "recovery": (
            "Inspect the bridge-owned sections and restore the missing peer "
            "state before promoting another slice."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    },
    AttentionStatus.REVIEWED_HASH_STALE: {
        "guard_behavior": "warn",
        "owner": "codex",
        "summary": (
            "The worktree has changed since the last reviewed hash; "
            "verdict and findings may be stale."
        ),
        "recovery": (
            "Codex should re-review the current tree and refresh the "
            "bridge verdict/findings/hash before promotion."
        ),
        "recommended_command": REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    },
    AttentionStatus.IMPLEMENTER_COMPLETION_STALL: {
        "guard_behavior": "warn",
        "owner": "claude",
        "summary": (
            "Implementer appears parked on reviewer polling while the "
            "current instruction is still active."
        ),
        "recovery": (
            "The implementer should resume coding on the active instruction "
            "instead of waiting for the next reviewer promotion."
        ),
        "recommended_command": None,
    },
    AttentionStatus.PUBLISHER_MISSING: {
        "guard_behavior": "warn",
        "owner": "system",
        "summary": (
            "Persistent heartbeat publisher is required but not running; "
            "status projections are not being pushed automatically."
        ),
        "recovery": (
            "Start the publisher with `review-channel ensure "
            "--start-publisher-if-missing` or manually with "
            "`review-channel ensure --follow`."
        ),
        "recommended_command": REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND,
    },
    AttentionStatus.PUBLISHER_FAILED_START: {
        "guard_behavior": "warn",
        "owner": "system",
        "summary": (
            "Publisher was started but exited immediately; the bridge "
            "or runtime environment may be misconfigured."
        ),
        "recovery": (
            "Check the publisher log for startup errors, then retry with "
            "`review-channel ensure --start-publisher-if-missing`."
        ),
        "recommended_command": REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND,
    },
    AttentionStatus.PUBLISHER_DETACHED_EXIT: {
        "guard_behavior": "warn",
        "owner": "system",
        "summary": (
            "Publisher was running but exited unexpectedly; the last "
            "heartbeat file records the pre-exit state."
        ),
        "recovery": (
            "Restart the publisher with `review-channel ensure "
            "--start-publisher-if-missing`. Check the log for the exit cause."
        ),
        "recommended_command": REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND,
    },
    AttentionStatus.HEALTHY: {
        "guard_behavior": "none",
        "owner": "system",
        "summary": "Review loop signals are fresh.",
        "recovery": "Continue the scoped review/coding loop.",
        "recommended_command": None,
    },
}
"""Maps each attention state to guard behavior, operator summary, and recovery.

``guard_behavior`` values:
- ``block_launch``: launcher refuses to open fresh conductor sessions
- ``warn``: status report warns but does not block
- ``none``: no action required

``summary``: one-line operator-facing description of the attention state.
``recovery``: actionable next step for the responsible party.
``recommended_command``: devctl command to run, or ``None``.
"""
