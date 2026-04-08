"""Focused tests for review-channel current-session projection helpers."""

from __future__ import annotations

from hashlib import sha256

from dev.scripts.devctl.review_channel.current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
    event_agent_status,
)
from dev.scripts.devctl.review_channel.handoff import BridgeSnapshot


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


def test_bridge_and_event_paths_produce_same_ack_state_when_stale() -> None:
    """Regression: stale_label must be identical across projection paths.

    Before the fix, build_bridge_current_session used stale_label="stale"
    while build_event_current_session used stale_label="unknown". The
    divergence caused _implementer_ack_current in reviewer_runtime_parser
    to fall through to a different code path for the event projection,
    producing a different implementation_blocked result.
    """
    bridge_state = build_bridge_current_session(
        snapshot=BridgeSnapshot(
            metadata={},
            sections={
                "Current Instruction For Claude": "Fix the layout bug.",
                "Claude Status": "working on layout",
                "Claude Questions": "",
                "Claude Ack": "Acknowledged: working on layout",
                "Open Findings": "none",
                "Last Reviewed Scope": "MP-400",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "rev-abc",
            "claude_ack_revision": "rev-OLD",
            "claude_ack_current": False,
        },
    )

    event_state = build_event_current_session(
        review_state={
            "review": {"plan_id": "MP-400"},
            "queue": {
                "pending_total": 0,
                "pending_claude": 0,
                "derived_next_instruction": "Fix the layout bug.",
            },
            "registry": {
                "agents": [
                    {"agent_id": "claude", "job_state": "working on layout"}
                ]
            },
        },
        bridge_liveness={
            "current_instruction_revision": "rev-abc",
            "claude_ack_revision": "rev-OLD",
            "claude_ack_current": False,
        },
    )

    assert bridge_state.implementer_ack_state == "stale", (
        "bridge path should label a non-current ack as 'stale'"
    )
    assert event_state.implementer_ack_state == "stale", (
        "event path should label a non-current ack as 'stale' (was 'unknown' before fix)"
    )
    assert bridge_state.implementer_ack_state == event_state.implementer_ack_state, (
        "both projection paths must produce the same implementer_ack_state "
        "so that implementation_blocked computes identically"
    )


def test_build_bridge_current_session_rederives_revision_when_instruction_changes() -> None:
    current_instruction = "Implement the repaired reviewer authority slice."
    bridge_state = build_bridge_current_session(
        snapshot=BridgeSnapshot(
            metadata={"current_instruction_revision": "abc123def456"},
            sections={
                "Current Instruction For Claude": current_instruction,
                "Claude Status": "working on the current slice",
                "Claude Questions": "",
                "Claude Ack": "Acknowledged instruction revision `abc123def456`",
                "Open Findings": "none",
                "Last Reviewed Scope": "MP-355",
            },
        ),
        bridge_liveness={
            "current_instruction_revision": "abc123def456",
            "claude_ack_revision": "abc123def456",
            "claude_ack_current": True,
        },
        prior_review_state={
            "current_session": {
                "current_instruction": "Implement the previous slice.",
                "current_instruction_revision": "abc123def456",
            }
        },
    )

    expected_revision = sha256(current_instruction.encode("utf-8")).hexdigest()[:12]

    assert bridge_state.current_instruction_revision == expected_revision
    assert bridge_state.implementer_ack_revision == "abc123def456"
    assert bridge_state.implementer_ack_state == "stale"
