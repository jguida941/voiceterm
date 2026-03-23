"""Canonical peer-heartbeat state names and stale-peer handling contract.

This module is the single source of truth for liveness state enums, threshold
constants, and documented recovery actions.  All code that checks or emits
peer-heartbeat states must import from here rather than inventing string
literals.  See ``dev/active/continuous_swarm.md`` Phase 0 for the governing
plan item.
"""

from __future__ import annotations

from ..runtime.enum_compat import StrEnum

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
    RUNTIME_MISSING = "runtime_missing"
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
    "polling.",
    "all green after codex's refactor. polling.",
    "waiting for codex review",
    "waiting for codex to review",
    "codex should review",
    "review and promote the next slice",
    "waiting for reviewer promotion",
)
"""Phrases in implementer status/ACK that indicate a completion-stall pattern."""

class ReviewerFreshness(StrEnum):
    """Explicit reviewer timing state derived from poll age and thresholds.

    Transitions:
    - ``FRESH``: poll age < CODEX_POLL_DUE_AFTER_SECONDS (180s)
    - ``POLL_DUE``: poll age ≥ DUE threshold but < STALE threshold (300s)
    - ``STALE``: poll age ≥ STALE threshold but < OVERDUE threshold (900s)
    - ``OVERDUE``: poll age ≥ OVERDUE threshold
    - ``MISSING``: no poll timestamp available
    """

    FRESH = "fresh"
    POLL_DUE = "poll_due"
    STALE = "stale"
    OVERDUE = "overdue"
    MISSING = "missing"


class AttentionStatus(StrEnum):
    """Machine-readable attention signals for operator/console consumers."""

    INACTIVE = "inactive"
    RUNTIME_MISSING = "runtime_missing"
    REVIEWER_HEARTBEAT_MISSING = "reviewer_heartbeat_missing"
    REVIEWER_HEARTBEAT_STALE = "reviewer_heartbeat_stale"
    REVIEWER_OVERDUE = "reviewer_overdue"
    REVIEWER_POLL_DUE = "reviewer_poll_due"
    CLAUDE_STATUS_MISSING = "claude_status_missing"
    CLAUDE_ACK_MISSING = "claude_ack_missing"
    CLAUDE_ACK_STALE = "claude_ack_stale"
    REVIEWER_SUPERVISOR_REQUIRED = "reviewer_supervisor_required"
    WAITING_ON_PEER = "waiting_on_peer"
    CHECKPOINT_REQUIRED = "checkpoint_required"
    REVIEW_FOLLOW_UP_REQUIRED = "review_follow_up_required"
    REVIEWED_HASH_STALE = "reviewed_hash_stale"
    IMPLEMENTER_COMPLETION_STALL = "implementer_completion_stall"
    DUAL_AGENT_IDLE = "dual_agent_idle"
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

def classify_reviewer_freshness(
    poll_age_seconds: int | float | None,
    *,
    due_after: int | float = CODEX_POLL_DUE_AFTER_SECONDS,
    stale_after: int | float = CODEX_POLL_STALE_AFTER_SECONDS,
    overdue_after: int | float = CODEX_POLL_OVERDUE_AFTER_SECONDS,
) -> ReviewerFreshness:
    """Classify reviewer timing from poll age into one explicit state."""
    if poll_age_seconds is None:
        return ReviewerFreshness.MISSING
    if poll_age_seconds >= overdue_after:
        return ReviewerFreshness.OVERDUE
    if poll_age_seconds >= stale_after:
        return ReviewerFreshness.STALE
    if poll_age_seconds >= due_after:
        return ReviewerFreshness.POLL_DUE
    return ReviewerFreshness.FRESH


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

from .peer_recovery import (
    ATTENTION_OWNER_ROLE,
    REVIEW_CHANNEL_ENSURE_START_PUBLISHER_COMMAND,
    REVIEW_CHANNEL_LIVE_RELAUNCH_COMMAND,
    REVIEW_CHANNEL_REVIEWER_FOLLOW_COMMAND,
    REVIEW_CHANNEL_STATUS_INSPECT_COMMAND,
    STALE_PEER_RECOVERY,
)
