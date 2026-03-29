"""Focused tests for review-channel current-session projection helpers."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.current_session_projection import (
    build_event_current_session,
    event_agent_status,
)


def test_event_agent_status_prefers_typed_registry_rows() -> None:
    review_state = {
        "registry": {
            "agents": [
                {
                    "agent_id": "claude",
                    "job_state": "active",
                }
            ]
        },
        "_compat": {
            "agents": [
                {
                    "agent_id": "claude",
                    "status": "waiting",
                }
            ]
        },
    }

    assert event_agent_status(review_state, "claude") == "active"


def test_build_event_current_session_uses_registry_without_compat_agents() -> None:
    state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-355"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "Fix the producer parity gap.",
            },
            "registry": {
                "agents": [
                    {
                        "agent_id": "claude",
                        "job_state": "active",
                    }
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "abc123def456",
            "claude_ack_revision": "",
            "claude_ack_current": False,
        },
    )

    assert state.current_instruction == "Fix the producer parity gap."
    assert state.implementer_status == "active"
    assert state.implementer_ack == "acknowledged"
    assert state.last_reviewed_scope == "MP-355"
