"""Focused regression tests for collaboration-session wake-field parsing."""

from __future__ import annotations

from dev.scripts.devctl.runtime.review_state_collaboration_parse import (
    collaboration_state_from_payload,
)
from dev.scripts.devctl.runtime.review_state_models import (
    AgentRegistryState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
)
from dev.scripts.devctl.runtime.review_state_packet_models import (
    AgentRegistryEntryState,
)


def _current_session() -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction="",
        current_instruction_revision="",
        implementer_status="",
        implementer_ack="",
        implementer_ack_revision="",
        implementer_ack_state="unknown",
    )


def _bridge_state() -> ReviewBridgeState:
    return ReviewBridgeState(
        overall_state="healthy",
        codex_poll_state="fresh",
        reviewer_freshness="fresh",
        reviewer_mode="active_dual_agent",
        last_codex_poll_utc="2026-04-19T00:00:00Z",
        last_codex_poll_age_seconds=0,
        last_worktree_hash="",
        current_instruction="",
        open_findings="",
        claude_status="",
        claude_ack="",
        claude_ack_current=False,
        current_instruction_revision="",
        claude_ack_revision="",
        last_reviewed_scope="",
        effective_reviewer_mode="active_dual_agent",
    )


def _registry(*agents: AgentRegistryEntryState) -> AgentRegistryState:
    return AgentRegistryState(
        timestamp="2026-04-19T00:00:00Z",
        agents=agents,
    )


def test_collaboration_state_from_typed_payload_preserves_wake_fields() -> None:
    state = collaboration_state_from_payload(
        collaboration={
            "session_id": "review-channel",
            "status": "live",
            "reviewer_mode": "active_dual_agent",
            "review_agent": "codex",
            "coding_agent": "claude",
            "mutation_owner": "claude",
            "verification_owner": "codex",
            "watcher_owner": "codex",
            "participants": [
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "display_name": "Claude",
                    "role": "implementer",
                    "session_name": "claude-main",
                    "live": True,
                    "status": "live",
                    "host_wake_mode": "tick_based",
                    "wake_interval_seconds": 30,
                    "host_wake_summary": "Phone-polled implementer lane.",
                },
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "display_name": "Codex",
                    "role": "reviewer",
                    "session_name": "codex-main",
                    "live": True,
                    "status": "live",
                    "host_wake_mode": "continuous",
                    "wake_interval_seconds": 0,
                    "host_wake_summary": "Local reviewer loop is continuous.",
                },
            ],
            "mutation_wake_mode": "tick_based",
            "verification_wake_mode": "continuous",
            "watcher_wake_mode": "continuous",
            "wake_continuity_ok": False,
            "wake_gap_summary": "mutation lane is phone-polled",
            "loop_wake_mode": "tick_based",
            "loop_wake_interval_seconds": 30,
            "loop_driver_agent": "claude",
            "loop_autonomy_ok": True,
            "loop_gap_summary": "",
        },
        review={"session_id": "review-channel"},
        current_session=_current_session(),
        bridge=_bridge_state(),
        registry=_registry(),
    )

    assert state.mutation_wake_mode == "tick_based"
    assert state.verification_wake_mode == "continuous"
    assert state.watcher_wake_mode == "continuous"
    assert state.wake_continuity_ok is False
    assert state.loop_wake_mode == "tick_based"
    assert state.loop_wake_interval_seconds == 30
    assert state.loop_driver_agent == "claude"
    assert state.loop_autonomy_ok is True
    assert state.participants[0].host_wake_mode == "tick_based"
    assert state.participants[0].wake_interval_seconds == 30
    assert state.participants[0].host_wake_summary == "Phone-polled implementer lane."


def test_collaboration_state_legacy_fallback_builds_wake_fields_without_type_error() -> None:
    state = collaboration_state_from_payload(
        collaboration={},
        review={"session_id": "review-channel"},
        current_session=_current_session(),
        bridge=_bridge_state(),
        registry=_registry(
            AgentRegistryEntryState(
                agent_id="codex",
                provider="codex",
                display_name="Codex",
                lane="reviewer",
                lane_title="Reviewer",
                current_job="review",
                job_state="live",
                waiting_on="",
                last_packet_seen="",
                last_packet_applied="",
                script_profile="",
                mp_scope="",
                worktree="",
                branch="",
                updated_at="2026-04-19T00:00:00Z",
            ),
            AgentRegistryEntryState(
                agent_id="claude",
                provider="claude",
                display_name="Claude",
                lane="implementer",
                lane_title="Implementer",
                current_job="implement",
                job_state="live",
                waiting_on="",
                last_packet_seen="",
                last_packet_applied="",
                script_profile="",
                mp_scope="",
                worktree="",
                branch="",
                updated_at="2026-04-19T00:00:00Z",
            ),
        ),
    )

    assert state.mutation_wake_mode == "continuous"
    assert state.verification_wake_mode == "continuous"
    assert state.watcher_wake_mode == "continuous"
    assert state.wake_continuity_ok is True
    assert state.loop_wake_mode == "continuous"
    assert state.loop_driver_agent
    assert state.loop_autonomy_ok is True
    assert state.participants
    assert state.participants[0].host_wake_mode == "continuous"
