"""Shared state dataclasses for the Operator Console core package."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ContextPackRef:
    """One attached memory/context pack reference on a review packet."""

    pack_kind: str
    pack_ref: str
    adapter_profile: str = ""
    generated_at_utc: str = ""

    def summary_line(self) -> str:
        """Render one compact operator-facing context-pack label."""
        line = f"{self.pack_kind}: {self.pack_ref}"
        if self.adapter_profile:
            line += f" ({self.adapter_profile})"
        if self.generated_at_utc:
            line += f" @ {self.generated_at_utc}"
        return line


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
    context_pack_refs: tuple[ContextPackRef, ...] = ()


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
class QualityPrioritySignal:
    """One prioritized file-level quality hotspot from the guard backlog."""

    path: str
    severity: str
    score: int
    signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class QualityBacklogSnapshot:
    """Compact quality-backlog signal set for desktop snapshot rendering."""

    captured_at_utc: str
    ok: bool
    source_files_scanned: int
    guard_failures: int
    critical_paths: int
    high_paths: int
    medium_paths: int
    low_paths: int
    ranked_paths: int
    failing_checks: tuple[str, ...] = ()
    top_priorities: tuple[QualityPrioritySignal, ...] = ()
    warning: str | None = None


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
    projection_notice: str | None = None
    codex_session_stats_text: str = ""
    codex_session_registry_text: str = ""
    claude_session_stats_text: str = ""
    claude_session_registry_text: str = ""
    cursor_panel_text: str = ""
    cursor_session_text: str = ""
    cursor_lane: AgentLaneData | None = None
    cursor_session_stats_text: str = ""
    cursor_session_registry_text: str = ""
    quality_backlog: QualityBacklogSnapshot | None = None


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
