"""Typed reviewer-runtime models shared by review-channel runtime surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReviewerLastPollState:
    last_codex_poll_utc: str = ""
    last_codex_poll_age_seconds: int = 0


@dataclass(frozen=True, slots=True)
class ReviewerRolloverState:
    rollover_id: str = ""
    ack_pending: bool = False
    trigger: str = ""


@dataclass(frozen=True, slots=True)
class ReviewerSessionOwnerState:
    provider: str = ""
    session_name: str = ""
    session_pid: int | None = None
    terminal_window_id: int | None = None
    script_path: str = ""


@dataclass(frozen=True, slots=True)
class ReviewerAcceptanceState:
    current_verdict: str = ""
    open_findings: str = ""
    review_accepted: bool = False


@dataclass(frozen=True, slots=True)
class ReviewerRuntimeContract:
    reviewer_mode: str = "single_agent"
    effective_reviewer_mode: str = "single_agent"
    reviewer_freshness: str = "unknown"
    stale_reason: str = ""
    implementer_ack_current: bool = False
    implementation_blocked: bool = False
    implementation_block_reason: str = ""
    last_poll: ReviewerLastPollState = field(default_factory=ReviewerLastPollState)
    rollover: ReviewerRolloverState = field(default_factory=ReviewerRolloverState)
    session_owner: ReviewerSessionOwnerState = field(
        default_factory=ReviewerSessionOwnerState
    )
    recovery_action_allowed: str = ""
    review_acceptance: ReviewerAcceptanceState = field(
        default_factory=ReviewerAcceptanceState
    )
    publish_clear: bool = False
