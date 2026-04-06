"""Dataclass models and constants for reviewer follow-loop recovery automation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .peer_liveness import AttentionStatus


# ── Attention status sets for auto-recovery gating ───────────────

AUTO_RECOVERY_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED.value,
    }
)

AUTO_ROLLOVER_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.RUNTIME_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE.value,
        AttentionStatus.REVIEWER_OVERDUE.value,
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
    }
)

AUTO_RELAUNCH_ATTENTION_STATUSES = frozenset(
    {
        AttentionStatus.REVIEWER_HEARTBEAT_MISSING.value,
        AttentionStatus.REVIEWER_HEARTBEAT_STALE.value,
        AttentionStatus.REVIEWER_OVERDUE.value,
        AttentionStatus.REVIEW_LOOP_RELAUNCH_REQUIRED.value,
    }
)

AUTO_RELAUNCH_LAUNCH_TRUTHS = frozenset(
    {
        "runtime_missing",
        "detached_runtime_only",
        "hybrid_claude_only",
    }
)


# ── Input/state dataclasses ──────────────────────────────────────


@dataclass
class ReviewerFollowRecoveryState:
    """Mutable state for bounded stale-implementer auto-recovery."""

    last_progress_token: str = ""
    unchanged_progress_polls: int = 0
    last_recovery_key: str = ""


@dataclass
class ReviewerFollowRolloverState:
    """Mutable state for bounded stale-reviewer relaunch/rollover automation."""

    last_progress_token: str = ""
    unchanged_progress_polls: int = 0
    last_restore_key: str = ""


@dataclass(frozen=True)
class ReviewerFollowRecoveryInput:
    """Immutable inputs for one stale-implementer recovery decision."""

    args: object
    repo_root: Path
    paths: dict[str, object]
    report: dict[str, object]
    progress_token: str
    recovery_state: ReviewerFollowRecoveryState


@dataclass(frozen=True)
class ReviewerFollowRolloverInput:
    """Immutable inputs for one stale-reviewer rollover decision."""

    args: object
    repo_root: Path
    paths: dict[str, object]
    report: dict[str, object]
    rollover_state: ReviewerFollowRolloverState
    rollover_provider: str = ""


# ── Progress-tracking helper ─────────────────────────────────────


def refresh_stall_progress(
    state: ReviewerFollowRecoveryState | ReviewerFollowRolloverState,
    progress_token: str,
    *,
    key_attr: str,
) -> int:
    token = progress_token.strip()
    if token and token != state.last_progress_token:
        state.last_progress_token = token
        state.unchanged_progress_polls = 0
        setattr(state, key_attr, "")
        return 0

    state.unchanged_progress_polls += 1
    return state.unchanged_progress_polls
