"""Tests for the derived RuntimeTruthSnapshot reducer."""

from pathlib import Path

from dev.scripts.devctl.runtime.runtime_truth_snapshot import (
    build_runtime_truth_snapshot,
)


def test_runtime_truth_snapshot_reduces_review_state(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "dev.scripts.devctl.runtime.runtime_truth_snapshot.read_agent_mind_projection",
        lambda repo_root, *, provider: {"agent_provider": provider}
        if provider == "claude"
        else {},
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.runtime.runtime_truth_snapshot.load_startup_quality_signals",
        lambda repo_root: {"probe_report": {}},
    )
    review_state = {
        "contract_id": "ReviewState",
        "source_command": "review-channel status",
        "current_session": {"current_instruction": "implement"},
        "packet_inbox": {
            "agents": [
                {
                    "agent": "codex",
                    "attention_status": "checkpoint_required",
                    "pending_actionable_total": 2,
                }
            ]
        },
        "reviewer_runtime": {
            "remote_control_attachment": {
                "status": "attached",
                "remote_session_id": "session_123",
                "heartbeat_ttl_seconds": "-1",
                "physical_confirmation_method": "claude_session_state_bridge",
            },
            "session_posture": {
                "interaction_mode": "remote_control",
                "reviewer_mode": "single_agent",
                "actors": [
                    {"actor_id": "claude", "live": True},
                    {"actor_id": "codex", "live": False},
                ],
            },
        },
    }

    snapshot = build_runtime_truth_snapshot(
        repo_root=tmp_path,
        review_state=review_state,
        connectivity_registry={
            "connected_contracts": [{"contract_id": "ReviewState"}],
            "warnings": [],
        },
    )

    assert snapshot.interaction_mode == "remote_control"
    assert snapshot.remote_control_active is True
    assert snapshot.remote_control_session_id == "session_123"
    assert snapshot.packet_attention_required is True
    assert snapshot.pending_packet_count == 2
    assert snapshot.live_actor_ids == ("claude",)
    assert snapshot.agent_mind_providers == ("claude",)
    assert snapshot.connectivity_contract_count == 1


def test_runtime_truth_snapshot_uses_shared_remote_control_ttl_predicate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "dev.scripts.devctl.runtime.runtime_truth_snapshot.read_agent_mind_projection",
        lambda repo_root, *, provider: {},
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.runtime.runtime_truth_snapshot.load_startup_quality_signals",
        lambda repo_root: {},
    )
    review_state = {
        "reviewer_runtime": {
            "remote_control_attachment": {
                "status": "attached",
                "remote_session_id": "session_123",
                "last_seen_utc": "2020-01-01T00:00:00Z",
                "heartbeat_ttl_seconds": "900",
                "physical_confirmation_method": "claude_session_state_bridge",
            },
            "session_posture": {
                "interaction_mode": "remote_control",
                "actors": [],
            },
        },
    }

    snapshot = build_runtime_truth_snapshot(
        repo_root=tmp_path,
        review_state=review_state,
    )

    assert snapshot.remote_control_active is False
