"""Focused regression tests for collaboration-session wake-field parsing."""

from __future__ import annotations

from dev.scripts.devctl.runtime.control_plane_loop_wake import (
    resolve_control_plane_loop_wake,
)
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
from dev.scripts.devctl.runtime.review_state_parser import review_state_from_payload


def _current_session() -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction="",
        current_instruction_revision="",
        implementer_status="",
        implementer_ack="",
        implementer_ack_revision="",
        implementer_ack_state="unknown",
    )


def _bridge_state(*, reviewer_mode: str = "active_dual_agent") -> ReviewBridgeState:
    return ReviewBridgeState(
        overall_state="healthy",
        codex_poll_state="fresh",
        reviewer_freshness="fresh",
        reviewer_mode=reviewer_mode,
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
        effective_reviewer_mode=reviewer_mode,
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
            "actor_authorities": [
                {
                    "actor_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "live": True,
                    "status": "live",
                    "source": "test",
                    "grants": [
                        {
                            "capability": "repo.commit",
                            "granted": True,
                            "source": "test",
                            "worktree_identity": "main",
                        }
                    ],
                }
            ],
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
    assert state.actor_authorities[0].actor_id == "claude"
    assert state.actor_authorities[0].grants[0].capability == "repo.commit"
    assert state.participants[0].host_wake_mode == "tick_based"
    assert state.participants[0].wake_interval_seconds == 30
    assert state.participants[0].host_wake_summary == "Phone-polled implementer lane."


def test_collaboration_state_legacy_fallback_builds_wake_fields_without_type_error() -> (
    None
):
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


def test_sparse_collaboration_without_typed_participants_leaves_loop_fields_unset() -> (
    None
):
    state = collaboration_state_from_payload(
        collaboration={"review_agent": "codex"},
        review={"session_id": "review-channel"},
        current_session=_current_session(),
        bridge=_bridge_state(reviewer_mode="single_agent"),
        registry=_registry(),
    )

    assert state.mutation_wake_mode == "unknown"
    assert state.verification_wake_mode == "unknown"
    assert state.watcher_wake_mode == "unknown"
    assert state.wake_continuity_ok is True
    assert state.wake_gap_summary == ""
    assert state.loop_wake_mode == "unknown"
    assert state.loop_wake_interval_seconds == 0
    assert state.loop_driver_agent == ""
    assert state.loop_autonomy_ok is False
    assert state.loop_gap_summary == ""


def test_sparse_collaboration_round_trip_preserves_loop_fallback() -> None:
    raw_payload = {
        "schema_version": 1,
        "command": "review-channel",
        "action": "status",
        "timestamp": "2026-04-20T00:00:00Z",
        "ok": True,
        "review": {"session_id": "review-channel"},
        "queue": {"pending_total": 0},
        "bridge": {"reviewer_mode": "single_agent"},
        "collaboration": {"review_agent": "codex"},
    }

    expected = resolve_control_plane_loop_wake(
        review_state_payload=raw_payload,
        reviewer_mode="single_agent",
        remote_control_attachment=None,
        codex_conductor_alive=True,
        claude_conductor_alive=False,
    )
    parsed = review_state_from_payload(raw_payload)

    assert parsed is not None
    observed = resolve_control_plane_loop_wake(
        review_state_payload=parsed.to_dict(),
        reviewer_mode="single_agent",
        remote_control_attachment=None,
        codex_conductor_alive=True,
        claude_conductor_alive=False,
    )

    assert expected.loop_wake_mode == "continuous"
    assert expected.loop_driver_agent == "codex"
    assert expected.loop_autonomy_ok is True
    assert observed == expected
