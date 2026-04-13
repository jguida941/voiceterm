"""Focused tests for review-channel runtime count projections."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.runtime_counts import build_runtime_counts


def test_build_runtime_counts_uses_distinct_live_provider_ids() -> None:
    counts = build_runtime_counts(
        collaboration={
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": True,
                    "planned_lane_count": 8,
                    "requested_worker_budget": 0,
                },
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "live": True,
                    "planned_lane_count": 8,
                    "requested_worker_budget": 0,
                },
                {
                    "agent_id": "claude-helper",
                    "provider": "claude",
                    "role": "implementer",
                    "live": True,
                    "planned_lane_count": 2,
                    "requested_worker_budget": 0,
                },
            ],
            "delegated_work": [],
        },
        publisher_running=True,
        reviewer_supervisor_running=False,
    )

    assert counts["live_participants_total"] == 3
    assert counts["active_conductor_count"] == 2
    assert "planned_lane_total" not in counts


def test_build_runtime_counts_omits_planned_lane_total_without_live_worker_evidence() -> None:
    counts = build_runtime_counts(
        collaboration={
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": False,
                    "planned_lane_count": 8,
                },
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "live": False,
                    "planned_lane_count": 8,
                },
            ],
            "delegated_work": [],
        },
    )

    assert counts["participants_total"] == 2
    assert counts["live_participants_total"] == 0
    assert counts["active_conductor_count"] == 0
    assert "planned_lane_total" not in counts


def test_build_runtime_counts_falls_back_to_bridge_liveness_without_participants() -> None:
    counts = build_runtime_counts(
        bridge_liveness={
            "active_conductor_providers": ["codex", "claude"],
            "publisher_running": True,
            "reviewer_supervisor_running": False,
        }
    )

    assert counts["live_participants_total"] == 2
    assert counts["active_conductor_count"] == 2
    assert counts["running_daemon_count"] == 1


def test_build_runtime_counts_excludes_operator_from_active_conductor_count() -> None:
    counts = build_runtime_counts(
        collaboration={
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": True,
                },
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "operator",
                    "live": True,
                },
            ],
            "delegated_work": [],
        }
    )

    assert counts["live_participants_total"] == 2
    assert counts["live_reviewer_total"] == 1
    assert counts["live_implementer_total"] == 0
    assert counts["active_conductor_count"] == 1


def test_build_runtime_counts_counts_live_single_agent_writer_from_role_assignments() -> None:
    counts = build_runtime_counts(
        collaboration={
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": True,
                },
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "operator",
                    "live": True,
                },
            ],
            "role_assignments": [
                {
                    "role_id": "review_agent",
                    "provider": "codex",
                    "live": True,
                },
                {
                    "role_id": "coding_agent",
                    "provider": "codex",
                    "live": True,
                },
                {
                    "role_id": "operator_agent",
                    "provider": "claude",
                    "live": True,
                },
            ],
            "delegated_work": [],
        }
    )

    assert counts["live_participants_total"] == 2
    assert counts["live_reviewer_total"] == 1
    assert counts["live_implementer_total"] == 1
    assert counts["active_conductor_count"] == 1
