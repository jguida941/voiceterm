from __future__ import annotations

from dev.scripts.devctl.commands.review_channel.sync_status_agent_loop import (
    agent_loop_decisions_for_work_board,
    inbox_observation_for_sync_status,
    packet_attention_for_sync_status,
)
from dev.scripts.devctl.commands.review_channel.sync_status_queue import (
    sync_status_queue,
)


def test_sync_status_agent_loop_decisions_preserve_checkpoint_blocker() -> None:
    review_state = {
        "attention": {"status": "checkpoint_required"},
        "recovery_assessment": {
            "diagnosis": {"supporting_causes": ["checkpoint_budget_exhausted"]},
            "decision": {"command": "python3 dev/scripts/devctl.py commit -m x"},
        },
        "current_session": {"current_instruction_revision": "rev-current"},
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_1",
                "snapshot_id": "agent-runtime-clock:rev_evt_1",
                "cadence_seconds": 30,
            },
            "packet_attention": {},
        },
        "authority_snapshot": {
            "actor_authorities": [
                {
                    "actor_id": "codex",
                    "granted_capabilities": ["repo.stage", "repo.commit"],
                }
            ],
            "allowed_actions": ["implementation.edit"],
            "blocked_actions": ["vcs.stage", "vcs.commit", "vcs.push"],
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "reviewer",
                    "session_id": "s-codex",
                    "status": "blocked",
                    "source_event_id": "rev_evt_1",
                    "confidence_class": "direct_typed_event",
                }
            ]
        },
        "packets": [],
    }

    decisions = agent_loop_decisions_for_work_board(
        review_state=review_state,
        work_board=review_state["agent_work_board"],
    )

    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["actor_id"] == "codex"
    assert decision["session_id"] == "s-codex"
    assert decision["required_action"] == "repair_startup_authority"
    assert decision["top_blocker"] == "startup authority: staged_index_budget_exceeded"
    assert decision["source_latest_event_id"] == "rev_evt_1"
    assert decision["current_instruction_revision"] == "rev-current"
    assert decision["source_work_board_row"]["route_key"] == "codex|reviewer|s-codex"


def test_sync_status_agent_loop_decisions_filter_target_agent() -> None:
    review_state = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "reviewer_runtime": {
            "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"}
        },
        "agent_work_board": {
            "rows": [
                {"actor_id": "codex", "role": "reviewer", "session_id": "s1"},
                {"actor_id": "claude", "role": "implementer", "session_id": "s2"},
            ]
        },
        "packets": [],
    }

    decisions = agent_loop_decisions_for_work_board(
        review_state=review_state,
        work_board=review_state["agent_work_board"],
        target_agent="claude",
    )

    assert [row["actor_id"] for row in decisions] == ["claude"]


def test_sync_status_agent_loop_ignores_stale_visibility_rows_without_packets() -> None:
    review_state = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "reviewer_runtime": {
            "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"}
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "dashboard",
                    "session_id": "s-stale",
                    "status": "idle",
                    "idle_seconds": 999,
                    "stale_after_seconds": 300,
                    "confidence_class": "stale",
                }
            ]
        },
        "packets": [],
    }

    decisions = agent_loop_decisions_for_work_board(
        review_state=review_state,
        work_board=review_state["agent_work_board"],
    )

    assert decisions == []


def test_sync_status_agent_loop_accepts_typed_tuple_packet_rows() -> None:
    review_state = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "reviewer_runtime": {
            "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"}
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "s2",
                    "active_packet_id": "rev_pkt_1",
                    "attention_packet_id": "rev_pkt_1",
                    "source_event_id": "rev_evt_1",
                },
            ]
        },
        "agent_sync": {
            "agents": {
                "claude": {
                    "last_consumed_event_id_lower_bound": "rev_evt_0",
                }
            }
        },
        "packets": (
            {
                "packet_id": "rev_pkt_1",
                "to_agent": "claude",
                "kind": "action_request",
                "status": "pending",
                "lifecycle_current_state": "delivery_pending",
                "latest_event_id": "rev_evt_1",
            },
        ),
    }

    decisions = agent_loop_decisions_for_work_board(
        review_state=review_state,
        work_board=review_state["agent_work_board"],
        target_agent="claude",
    )

    assert decisions[0]["active_packet_id"] == "rev_pkt_1"
    assert decisions[0]["attention_packet_id"] == "rev_pkt_1"
    assert decisions[0]["wake_required"] is True
    assert decisions[0]["pending_packet_count"] == 1


def test_sync_status_agent_loop_synthesizes_agent_sync_finding_wake() -> None:
    review_state = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "reviewer_runtime": {
            "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
            "packet_attention": {
                "observation_actor_id": "",
                "pending_packet_count": 0,
                "wake_required": False,
                "stale_reason": "actor_identity_ambiguous",
            },
        },
        "agent_sync": {
            "agents": {
                "claude": {
                    "pending_packets_to_me": ["rev_pkt_finding"],
                    "last_consumed_event_id_lower_bound": "rev_evt_0",
                }
            }
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "reviewer",
                    "session_id": "s-codex",
                    "status": "idle",
                    "source_event_id": "rev_evt_1",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_finding",
                "to_agent": "claude",
                "kind": "finding",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "requested_action": "review_only",
                "policy_hint": "review_only",
                "approval_required": False,
                "latest_event_id": "rev_evt_2",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
    }

    decisions = agent_loop_decisions_for_work_board(
        review_state=review_state,
        work_board=review_state["agent_work_board"],
    )

    claude = next(row for row in decisions if row["actor_id"] == "claude")
    assert claude["attention_packet_id"] == "rev_pkt_finding"
    assert claude["wake_required"] is True
    assert claude["pending_packet_count"] == 1
    assert (
        claude["source_work_board_row"]["source_surface"]
        == "agent_sync.pending_packets_to_me"
    )


def test_sync_status_agent_loop_keeps_operator_review_only_notice_receipt_only() -> None:
    review_state = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "reviewer_runtime": {
            "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"}
        },
        "agent_sync": {
            "agents": {
                "operator": {
                    "pending_packets_to_me": ["rev_pkt_notice"],
                }
            }
        },
        "agent_work_board": {"rows": []},
        "packets": [
            {
                "packet_id": "rev_pkt_notice",
                "to_agent": "operator",
                "kind": "system_notice",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "requested_action": "review_only",
                "policy_hint": "review_only",
                "approval_required": False,
                "latest_event_id": "rev_evt_2",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
    }

    decisions = agent_loop_decisions_for_work_board(
        review_state=review_state,
        work_board=review_state["agent_work_board"],
    )

    assert decisions == []


def test_packet_attention_uses_unique_actor_pending_inventory() -> None:
    review_state = {
        "agent_sync": {
            "agents": {
                "claude": {
                    "pending_packets_to_me": ["rev_pkt_new", "rev_pkt_old"],
                }
            }
        },
        "reviewer_runtime": {"packet_attention": {}},
    }
    decisions = [
        {
            "actor_id": "claude",
            "session_id": "s-old",
            "attention_packet_id": "rev_pkt_old",
            "pending_packet_count": 12,
            "wake_required": True,
            "pivot_required": True,
            "latest_inbox_event_id": "rev_evt_1",
        },
        {
            "actor_id": "claude",
            "session_id": "s-new",
            "attention_packet_id": "rev_pkt_new",
            "pending_packet_count": 12,
            "wake_required": True,
            "pivot_required": True,
            "latest_inbox_event_id": "rev_evt_2",
        },
    ]

    attention = packet_attention_for_sync_status(
        review_state,
        target_agent="claude",
        agent_loop_decisions=decisions,
    )

    assert attention["pending_packet_count"] == 2
    assert attention["scope_state"] == "session_ambiguous"
    assert set(attention["scoped_attention_packet_ids"]) == {
        "rev_pkt_new",
        "rev_pkt_old",
    }


def test_packet_attention_fails_closed_when_same_packet_hits_two_sessions() -> None:
    review_state = {
        "agent_sync": {
            "agents": {
                "claude": {
                    "pending_packets_to_me": ["rev_pkt_shared"],
                }
            }
        },
        "reviewer_runtime": {"packet_attention": {}},
    }
    decisions = [
        {
            "actor_id": "claude",
            "session_id": "s-a",
            "attention_packet_id": "rev_pkt_shared",
            "pending_packet_count": 1,
            "wake_required": True,
            "pivot_required": True,
            "latest_inbox_event_id": "rev_evt_10",
        },
        {
            "actor_id": "claude",
            "session_id": "s-b",
            "attention_packet_id": "rev_pkt_shared",
            "pending_packet_count": 1,
            "wake_required": True,
            "pivot_required": True,
            "latest_inbox_event_id": "rev_evt_10",
        },
    ]

    attention = packet_attention_for_sync_status(
        review_state,
        target_agent="claude",
        agent_loop_decisions=decisions,
    )

    assert attention["latest_attention_packet_id"] == ""
    assert attention["observation_session_id"] == ""
    assert attention["scope_state"] == "session_ambiguous"
    assert attention["scoped_attention_packet_ids"] == ["rev_pkt_shared"]
    assert set(attention["scoped_session_ids"]) == {"s-a", "s-b"}


def test_packet_attention_uses_inbound_event_not_outbound_fallback() -> None:
    review_state = {
        "agent_sync": {
            "agents": {
                "claude": {
                    "pending_packets_to_me": ["rev_pkt_old"],
                }
            }
        },
        "reviewer_runtime": {
            "packet_attention": {
                "latest_inbox_event_id": "rev_evt_99",
                "latest_attention_packet_id": "rev_pkt_outbound",
            }
        },
    }
    decisions = [
        {
            "actor_id": "claude",
            "session_id": "s-old",
            "attention_packet_id": "rev_pkt_old",
            "pending_packet_count": 1,
            "wake_required": True,
            "pivot_required": True,
            "latest_inbox_event_id": "rev_evt_2",
            "source_latest_event_id": "rev_evt_99",
        },
    ]

    attention = packet_attention_for_sync_status(
        review_state,
        target_agent="claude",
        agent_loop_decisions=decisions,
    )

    assert attention["latest_inbox_event_id"] == "rev_evt_2"
    assert attention["latest_attention_packet_id"] == "rev_pkt_old"


def test_sync_status_queue_reports_target_scoped_stale_count() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_live",
                "to_agent": "codex",
                "kind": "action_request",
                "status": "pending",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
            {
                "packet_id": "rev_pkt_stale",
                "to_agent": "codex",
                "kind": "action_request",
                "status": "pending",
                "expires_at_utc": "2000-01-01T00:00:00Z",
            },
            {
                "packet_id": "rev_pkt_other",
                "to_agent": "claude",
                "kind": "action_request",
                "status": "pending",
                "expires_at_utc": "2000-01-01T00:00:00Z",
            },
        ]
    }
    _, queue = sync_status_queue(
        review_state=review_state,
        agents_block={
            "codex": {
                "pending_packets_to_me": ["rev_pkt_live"],
            }
        },
        target_agent="codex",
    )

    assert queue["pending_total"] == 1
    assert queue["stale_packet_count"] == 1


def test_inbox_observation_uses_target_scoped_pending_inventory() -> None:
    review_state = {
        "agent_sync": {
            "agents": {
                "claude": {
                    "pending_packets_to_me": ["rev_pkt_new", "rev_pkt_old"],
                }
            }
        },
        "reviewer_runtime": {
            "inbox_observation": {
                "actor_id": "",
                "last_inbox_observed_event_id": "rev_evt_1",
                "pending_packet_count": 0,
            }
        },
    }
    decisions = [
        {
            "actor_id": "claude",
            "session_id": "s-old",
            "latest_inbox_event_id": "rev_evt_1",
            "pending_packet_count": 12,
        },
        {
            "actor_id": "claude",
            "session_id": "s-new",
            "latest_inbox_event_id": "rev_evt_2",
            "pending_packet_count": 12,
        },
    ]

    observation = inbox_observation_for_sync_status(
        review_state,
        target_agent="claude",
        agent_loop_decisions=decisions,
    )

    assert observation["actor_id"] == "claude"
    assert observation["session_id"] == ""
    assert observation["pending_packet_count"] == 2
    assert observation["last_inbox_event_id"] == "rev_evt_2"
    assert observation["pivot_required"] is True
    assert observation["scope_state"] == "session_ambiguous"
