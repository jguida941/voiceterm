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

    STALE = "stale"
    WAITING_ON_PEER = "waiting_on_peer"
    FRESH = "fresh"


class AttentionStatus(StrEnum):
    """Machine-readable attention signals for operator/console consumers."""

    REVIEWER_HEARTBEAT_MISSING = "reviewer_heartbeat_missing"
    REVIEWER_HEARTBEAT_STALE = "reviewer_heartbeat_stale"
    REVIEWER_POLL_DUE = "reviewer_poll_due"
    CLAUDE_STATUS_MISSING = "claude_status_missing"
    CLAUDE_ACK_MISSING = "claude_ack_missing"
    WAITING_ON_PEER = "waiting_on_peer"
    HEALTHY = "healthy"


# ---------------------------------------------------------------------------
# Threshold constants
# ---------------------------------------------------------------------------

CODEX_POLL_DUE_AFTER_SECONDS = 180
"""Codex poll is 'due' when age exceeds the 2-3 minute reviewer cadence."""

CODEX_POLL_STALE_AFTER_SECONDS = 300
"""Codex poll is 'stale' when age exceeds the five-minute heartbeat window."""


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


# ---------------------------------------------------------------------------
# Stale-peer handling contract
# ---------------------------------------------------------------------------

STALE_PEER_RECOVERY: dict[str, dict[str, str | None]] = {
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
