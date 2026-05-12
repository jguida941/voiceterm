"""Tests for queue-derived agent-loop target decisions."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.agent_loop_decision_queue_targets import (
    queue_target_decisions,
)


def test_queue_target_skips_dead_session_scoped_packet() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "reviewer",
                    "session_id": "live-reviewer-session",
                    "status": "polling",
                    "confidence_class": "derived_typed_event",
                }
            ]
        },
        "queue": {"pending_codex": 1},
        "agent_sync": {
            "agents": {
                "codex": {"pending_packets_to_me": ["rev_pkt_old_session"]}
            }
        },
        "packets": [
            {
                "packet_id": "rev_pkt_old_session",
                "kind": "finding",
                "to_agent": "codex",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "target_role": "reviewer",
                "target_session_id": "dead-reviewer-session",
                "attention_urgency": "urgent",
            }
        ],
    }

    decisions = queue_target_decisions(
        review_state=review_state,
        dashboard={},
        target_agent="codex",
        seen_keys=set(),
    )

    assert decisions == []


def test_queue_target_keeps_fresh_session_scoped_packet() -> None:
    review_state = {
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "reviewer",
                    "session_id": "live-reviewer-session",
                    "status": "polling",
                    "confidence_class": "derived_typed_event",
                }
            ]
        },
        "queue": {"pending_codex": 1},
        "agent_sync": {
            "agents": {
                "codex": {"pending_packets_to_me": ["rev_pkt_live_session"]}
            }
        },
        "packets": [
            {
                "packet_id": "rev_pkt_live_session",
                "kind": "finding",
                "to_agent": "codex",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "target_role": "reviewer",
                "target_session_id": "live-reviewer-session",
                "attention_urgency": "urgent",
            }
        ],
    }

    decisions = queue_target_decisions(
        review_state=review_state,
        dashboard={},
        target_agent="codex",
        seen_keys=set(),
    )

    assert [key for key, _decision in decisions] == [
        ("codex", "reviewer", "live-reviewer-session")
    ]
