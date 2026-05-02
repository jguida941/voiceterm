"""Collaboration contracts embedded in `/develop` reports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DevelopmentRuntimeRow:
    """One live actor row from typed review-channel runtime projections."""

    actor_id: str
    provider: str
    role: str
    session_id: str
    status: str
    confidence_class: str
    idle_seconds: int
    mutation_mode: str
    active_packet_id: str = ""
    attention_packet_id: str = ""
    executing_packet_id: str = ""
    plan_row_id: str = ""
    source_event_id: str = ""
    worktree_identity: str = ""
    branch: str = ""


@dataclass(frozen=True, slots=True)
class DevelopmentSessionDiscoveryRow:
    """One provider session file discovered outside the work-board projection."""

    provider: str
    session_id: str
    registered: bool
    age_seconds: int
    source_path: str = ""
    visibility: str = "session_jsonl"


@dataclass(frozen=True, slots=True)
class DevelopmentRuntimeSnapshot:
    """Shared-work runtime picture used by `/develop` coordination."""

    actor: str
    actor_source: str = ""
    authority_source: str = "AgentWorkBoardProjection+AgentSyncProjection"
    coordination_topology: str = ""
    authority_mode: str = ""
    safe_to_fanout: bool = False
    actor_sync_status: str = ""
    actor_pending_packet_count: int = 0
    fresh_row_count: int = 0
    stale_row_count: int = 0
    discovered_session_count: int = 0
    unregistered_session_count: int = 0
    rows: tuple[DevelopmentRuntimeRow, ...] = ()
    session_discovery: tuple[DevelopmentSessionDiscoveryRow, ...] = ()
    summary: str = ""


@dataclass(frozen=True, slots=True)
class DevelopmentPeerMindEvent:
    """One peer-mind event projected into `/develop` as auxiliary context."""

    timestamp: str
    event_type: str
    summary: str
    tool_name: str = ""
    is_error: bool = False
    is_escalation: bool = False


@dataclass(frozen=True, slots=True)
class DevelopmentPeerMindSnapshot:
    """Recent peer reasoning/testing context, never authority by itself."""

    provider: str
    session_id: str = ""
    coverage_scope: str = "provider_latest_projection"
    known_session_count: int = 0
    covered_session_count: int = 0
    omitted_session_count: int = 0
    event_count: int = 0
    age_seconds: int = -1
    confidence: str = "missing_auxiliary"
    authority_policy: str = "auxiliary_context_only"
    wake_hint: str = ""
    suggested_command: str = ""
    latest_summary: str = ""
    events: tuple[DevelopmentPeerMindEvent, ...] = ()


__all__ = [
    "DevelopmentPeerMindEvent",
    "DevelopmentPeerMindSnapshot",
    "DevelopmentRuntimeRow",
    "DevelopmentRuntimeSnapshot",
    "DevelopmentSessionDiscoveryRow",
]
