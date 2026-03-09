"""Shared state dataclasses for the Operator Console."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ApprovalRequest:
    """One pending structured approval request for the operator."""

    packet_id: str
    from_agent: str
    to_agent: str
    summary: str
    body: str
    policy_hint: str
    requested_action: str
    status: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentLaneData:
    """Structured key-value pairs for one agent lane."""

    provider_name: str
    lane_title: str
    role_label: str
    status_hint: str
    state_label: str
    rows: tuple[tuple[str, str], ...]
    raw_text: str
    risk_label: str | None = None
    confidence_label: str | None = None


@dataclass(frozen=True)
class OperatorConsoleSnapshot:
    """Current bridge/review state rendered for the Operator Console."""

    codex_panel_text: str
    claude_panel_text: str
    operator_panel_text: str
    codex_session_text: str
    claude_session_text: str
    raw_bridge_text: str
    review_mode: str | None
    last_codex_poll: str | None
    last_worktree_hash: str | None
    pending_approvals: tuple[ApprovalRequest, ...] = ()
    warnings: tuple[str, ...] = ()
    review_state_path: str | None = None
    codex_lane: AgentLaneData | None = None
    claude_lane: AgentLaneData | None = None
    operator_lane: AgentLaneData | None = None


@dataclass(frozen=True)
class OperatorDecisionArtifact:
    """Paths written for one operator approve/deny action."""

    json_path: str
    markdown_path: str
    latest_json_path: str
    latest_markdown_path: str


def utc_timestamp() -> str:
    """Return a UTC ISO-8601 timestamp with trailing `Z`."""
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
