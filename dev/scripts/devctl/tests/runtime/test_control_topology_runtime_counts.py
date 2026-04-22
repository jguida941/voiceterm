"""Focused tests for startup runtime-count projections."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.runtime.control_topology_runtime_counts import (
    startup_runtime_counts,
)
from dev.scripts.devctl.runtime.control_topology import derive_startup_control_truth


def test_startup_runtime_counts_count_live_single_agent_writer_from_role_assignments() -> None:
    review_state = SimpleNamespace(
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
        }
    )

    counts = startup_runtime_counts(
        review_state,
        bridge_liveness={"active_conductor_providers": ["codex"]},
    )

    assert counts["participants_total"] == 2
    assert counts["live_participants_total"] == 2
    assert counts["live_reviewer_total"] == 1
    assert counts["live_implementer_total"] == 1
    assert counts["active_conductor_count"] == 1


def test_startup_runtime_counts_ignore_operator_only_provider_role_assignment() -> None:
    review_state = SimpleNamespace(
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
                    "provider": "claude",
                    "live": True,
                },
                {
                    "role_id": "operator_agent",
                    "provider": "claude",
                    "live": True,
                },
            ],
        }
    )

    counts = startup_runtime_counts(
        review_state,
        bridge_liveness={"active_conductor_providers": ["codex"]},
    )

    assert counts["participants_total"] == 2
    assert counts["live_participants_total"] == 2
    assert counts["live_reviewer_total"] == 1
    assert counts["live_implementer_total"] == 0
    assert counts["active_conductor_count"] == 1


def test_startup_control_truth_coalesces_single_agent_role_assignments() -> None:
    review_state = SimpleNamespace(
        bridge={
            "reviewer_mode": "single_agent",
            "effective_reviewer_mode": "single_agent",
            "active_conductor_providers": ["codex"],
        },
        collaboration={
            "participants": [
                {
                    "agent_id": "codex",
                    "provider": "codex",
                    "role": "reviewer",
                    "live": True,
                }
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
            ],
        },
    )

    topology, permission = derive_startup_control_truth(review_state)

    assert topology == "single_agent"
    assert permission == "active"
