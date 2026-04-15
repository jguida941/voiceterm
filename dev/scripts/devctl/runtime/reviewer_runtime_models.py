"""Typed reviewer-runtime models shared by review-channel runtime surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReviewerLastPollState:
    last_codex_poll_utc: str = ""
    last_codex_poll_age_seconds: int = 0
    last_reviewer_poll_utc: str = ""
    last_reviewer_poll_age_seconds: int = 0


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
    session_visibility: str = "unknown"


@dataclass(frozen=True, slots=True)
class ReviewerAcceptanceState:
    current_verdict: str = ""
    open_findings: str = ""
    review_accepted: bool = False
    reviewer_accepted_implementer_state_hash: str = ""


@dataclass(frozen=True, slots=True)
class RemoteControlAttachmentState:
    provider: str = ""
    role: str = "operator"
    attachment_id: str = ""
    session_name: str = ""
    remote_session_id: str = ""
    session_url: str = ""
    status: str = "unknown"
    transport: str = "review_channel_artifact"
    attached_at_utc: str = ""
    last_seen_utc: str = ""
    metadata_path: str = ""


_ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES = frozenset(
    {"attached", "unknown"}
)


def remote_control_attachment_from_mapping(
    value: object,
) -> RemoteControlAttachmentState | None:
    """Deserialize an optional remote-control attachment record."""
    if not isinstance(value, Mapping):
        return None
    attachment_id = str(value.get("attachment_id") or "").strip()
    session_name = str(value.get("session_name") or "").strip()
    remote_session_id = str(value.get("remote_session_id") or "").strip()
    session_url = str(value.get("session_url") or "").strip()
    if not any((attachment_id, session_name, remote_session_id, session_url)):
        return None
    return RemoteControlAttachmentState(
        provider=str(value.get("provider") or "").strip(),
        role=str(value.get("role") or "operator").strip() or "operator",
        attachment_id=attachment_id,
        session_name=session_name,
        remote_session_id=remote_session_id,
        session_url=session_url,
        status=str(value.get("status") or "unknown").strip() or "unknown",
        transport=(
            str(value.get("transport") or "review_channel_artifact").strip()
            or "review_channel_artifact"
        ),
        attached_at_utc=str(value.get("attached_at_utc") or "").strip(),
        last_seen_utc=str(value.get("last_seen_utc") or "").strip(),
        metadata_path=str(value.get("metadata_path") or "").strip(),
    )


def has_active_remote_control_attachment(
    attachment: RemoteControlAttachmentState | None,
) -> bool:
    """Return True when the external remote-control session should drive mode."""
    if attachment is None:
        return False
    status = str(attachment.status or "").strip().lower()
    return status in _ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES


@dataclass(frozen=True, slots=True)
class ReviewerRuntimeContract:
    reviewer_mode: str = "single_agent"
    effective_reviewer_mode: str = "single_agent"
    reviewer_freshness: str = "unknown"
    stale_reason: str = ""
    conductor_visibility: str = "unknown"
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
    remote_control_attachment: RemoteControlAttachmentState | None = None
