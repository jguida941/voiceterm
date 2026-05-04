from __future__ import annotations

from dev.scripts.devctl.review_channel.projection_bundle import (
    canonicalize_projection_review_state,
)
from dev.scripts.devctl.review_channel.status_bundle import (
    _attach_agent_loop_decisions,
    _preserve_typed_runtime_addenda,
)
from dev.scripts.devctl.commands.review_channel.status_runtime_projection import (
    _refresh_report_work_board_identity,
)
from dev.scripts.devctl.review_channel.agent_work_board_posture import (
    apply_work_board_session_posture,
)


def test_status_bundle_preserves_event_runtime_addenda() -> None:
    review_state = {
        "packets": [],
        "reviewer_runtime": {
            "agent_runtime_clock": {"source_latest_event_id": ""},
        }
    }
    prior = {
        "packets": [{"packet_id": "rev_pkt_1"}],
        "round_proofs": [
            {
                "contract_id": "RoundProof",
                "proof_id": "round-1",
                "actor_id": "claude",
                "status": "missing",
                "proof_state": "missing",
            }
        ],
        "agent_sync": {"contract_id": "AgentSyncProjection"},
        "agent_work_board": {"contract_id": "AgentWorkBoardProjection"},
        "agent_loop_decisions": [{"actor_id": "claude"}],
        "coordination_state": {
            "coordination_topology": "multi_agent_active",
        },
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_1",
                "snapshot_id": "agent-runtime-clock:rev_evt_1",
            },
            "packet_attention": {
                "latest_inbox_event_id": "rev_evt_1",
            },
            "inbox_observation": {
                "last_inbox_event_id": "rev_evt_1",
            },
        },
    }

    merged = _preserve_typed_runtime_addenda(
        review_state,
        prior_review_state=prior,
    )

    assert merged["agent_sync"] == {"contract_id": "AgentSyncProjection"}
    assert merged["packets"] == [{"packet_id": "rev_pkt_1"}]
    assert merged["agent_work_board"] == {"contract_id": "AgentWorkBoardProjection"}
    assert merged["agent_loop_decisions"] == [{"actor_id": "claude"}]
    assert merged["coordination_state"]["coordination_topology"] == "multi_agent_active"
    assert (
        merged["reviewer_runtime"]["agent_runtime_clock"]["source_latest_event_id"]
        == "rev_evt_1"
    )
    assert merged["reviewer_runtime"]["packet_attention"]["latest_inbox_event_id"] == "rev_evt_1"
    assert merged["reviewer_runtime"]["inbox_observation"]["last_inbox_event_id"] == "rev_evt_1"


def test_status_bundle_refreshes_preserved_work_board_runtime_identity() -> None:
    review_state = {
        "collaboration": {
            "participants": (
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "worktree": "/repo/worktree",
                    "branch": "feature/live",
                    "workspace_root": "/repo/worktree",
                },
            )
        },
        "reviewer_runtime": {},
    }
    prior = {
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "dashboard",
                    "session_id": "s-claude",
                    "worktree_identity": "",
                    "branch": "",
                    "path_scope": [],
                }
            ]
        }
    }

    merged = _preserve_typed_runtime_addenda(
        review_state,
        prior_review_state=prior,
    )

    row = merged["agent_work_board"]["rows"][0]
    assert row["worktree_identity"] == "/repo/worktree"
    assert row["branch"] == "feature/live"
    assert row["path_scope"] == ["/repo/worktree"]


def test_status_report_refreshes_work_board_runtime_identity() -> None:
    report = {
        "collaboration": {
            "participants": (
                {
                    "agent_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "worktree": "/repo/worktree",
                    "branch": "feature/live",
                    "workspace_root": "/repo/worktree",
                },
            )
        },
        "current_session": {"current_instruction_revision": "rev-current"},
        "reviewer_runtime": {
            "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"}
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "dashboard",
                    "session_id": "s-claude",
                    "worktree_identity": "",
                    "branch": "",
                    "path_scope": [],
                }
            ]
        },
        "packets": [],
    }

    _refresh_report_work_board_identity(report)

    row = report["agent_work_board"]["rows"][0]
    assert row["worktree_identity"] == "/repo/worktree"
    assert row["branch"] == "feature/live"
    assert row["path_scope"] == ["/repo/worktree"]
    assert report["agent_loop_decisions"][0]["actor_id"] == "claude"


def test_status_runtime_addenda_reconciles_session_posture_liveness() -> None:
    review_state = {
        "reviewer_runtime": {
            "session_posture": {
                "actors": [
                    {
                        "actor_id": "claude",
                        "provider": "claude",
                        "live": False,
                        "presence": "configured",
                        "source": "collaboration_participant",
                    }
                ]
            }
        }
    }
    prior = {
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "status": "working",
                    "idle_seconds": 5,
                    "stale_after_seconds": 600,
                    "confidence_class": "direct_typed_event",
                    "attention_packet_id": "rev_pkt_2592",
                }
            ]
        }
    }

    merged = _preserve_typed_runtime_addenda(
        review_state,
        prior_review_state=prior,
    )
    merged = apply_work_board_session_posture(merged)

    actor = merged["reviewer_runtime"]["session_posture"]["actors"][0]
    assert actor["live"] is True
    assert actor["presence"] == "live"
    assert actor["source"] == "agent_work_board"
    assert actor["current_target"] == "rev_pkt_2592"


def test_projection_canonicalize_keeps_typed_runtime_addenda() -> None:
    payload = {
        "agent_sync": {"contract_id": "AgentSyncProjection"},
        "agent_work_board": {"contract_id": "AgentWorkBoardProjection"},
        "agent_loop_decisions": [{"actor_id": "claude"}],
        "coordination_state": {
            "coordination_topology": "multi_agent_active",
        },
        "round_proofs": [
            {
                "contract_id": "RoundProof",
                "proof_id": "round-1",
                "actor_id": "claude",
                "status": "missing",
                "proof_state": "missing",
            }
        ],
    }

    canonical = canonicalize_projection_review_state(payload)

    assert canonical["agent_sync"] == {"contract_id": "AgentSyncProjection"}
    assert canonical["agent_work_board"] == {"contract_id": "AgentWorkBoardProjection"}
    assert canonical["agent_loop_decisions"] == [{"actor_id": "claude"}]
    assert canonical["coordination_state"]["coordination_topology"] == "multi_agent_active"
    assert canonical["round_proofs"][0]["contract_id"] == "RoundProof"
    assert canonical["round_proofs"][0]["proof_id"] == "round-1"


def test_status_bundle_persists_agent_loop_decisions_from_work_board() -> None:
    payload = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "attention": {"status": "ok"},
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_2",
                "snapshot_id": "agent-runtime-clock:rev_evt_2",
            }
        },
        "agent_sync": {
            "agents": {
                "claude": {
                    "last_consumed_event_id_lower_bound": "rev_evt_1",
                    "pending_packets_to_me": ["rev_pkt_1"],
                }
            }
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "s-claude",
                    "active_packet_id": "rev_pkt_1",
                    "attention_packet_id": "rev_pkt_1",
                    "source_event_id": "rev_evt_2",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_1",
                "to_agent": "claude",
                "kind": "action_request",
                "status": "pending",
                "lifecycle_current_state": "delivery_pending",
                "latest_event_id": "rev_evt_2",
                "target_role": "implementer",
                "target_session_id": "s-claude",
            }
        ],
    }

    projected = _attach_agent_loop_decisions(payload)

    assert projected["agent_loop_decisions"][0]["actor_id"] == "claude"
    assert projected["agent_loop_decisions"][0]["active_packet_id"] == "rev_pkt_1"
    assert projected["agent_loop_decisions"][0]["attention_packet_id"] == "rev_pkt_1"
    assert projected["agent_loop_decisions"][0]["wake_required"] is True
    attention = projected["reviewer_runtime"]["packet_attention"]
    assert attention["wake_required"] is True
    assert attention["pending_packet_count"] == 1
    assert attention["stale_reason"] == "actor_identity_ambiguous_with_pending_wake"
    assert "scoped_agent_attention_pending" in attention["pivot_reasons"]


def test_status_bundle_keeps_actor_pending_pressure_without_session_match() -> None:
    payload = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "attention": {
            "status": "checkpoint_required",
        },
        "recovery_assessment": {
            "diagnosis": {
                "supporting_causes": ["checkpoint_budget_exhausted"],
            }
        },
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_4",
                "snapshot_id": "agent-runtime-clock:rev_evt_4",
            }
        },
        "agent_sync": {
            "agents": {
                "codex": {
                    "last_consumed_event_id_lower_bound": "rev_evt_3",
                    "pending_packets_to_me": ["rev_pkt_reviewer"],
                }
            }
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "implementer",
                    "session_id": "s-codex-current",
                    "source_event_id": "rev_evt_4",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_reviewer",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "lifecycle_current_state": "pending",
                "latest_event_id": "rev_evt_4",
                "target_role": "reviewer",
                "target_session_id": "s-codex-old",
            }
        ],
    }

    projected = _attach_agent_loop_decisions(payload)

    decision = projected["agent_loop_decisions"][0]
    assert decision["actor_id"] == "codex"
    assert decision["required_action"] == "triage_pending_packet"
    assert decision["active_packet_id"] == ""
    assert decision["pending_packet_count"] == 1
    assert decision["wake_required"] is True
    assert decision["safe_to_continue"] is False

    attention = projected["reviewer_runtime"]["packet_attention"]
    assert attention["wake_required"] is True
    assert attention["pending_packet_count"] == 1
    assert attention["stale_reason"] == "actor_identity_ambiguous_with_pending_wake"


def test_status_bundle_clears_agent_sync_attention_when_sessions_disagree() -> None:
    payload = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "attention": {"status": "ok"},
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_11",
                "snapshot_id": "agent-runtime-clock:rev_evt_11",
            }
        },
        "agent_sync": {
            "agents": {
                "claude": {
                    "attention_packet_id": "rev_pkt_old",
                    "pending_packets_to_me": ["rev_pkt_old"],
                }
            }
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "s-old",
                    "active_packet_id": "rev_pkt_old",
                    "attention_packet_id": "rev_pkt_old",
                    "source_event_id": "rev_evt_10",
                },
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "s-new",
                    "active_packet_id": "rev_pkt_new",
                    "attention_packet_id": "rev_pkt_new",
                    "source_event_id": "rev_evt_11",
                },
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_old",
                "to_agent": "claude",
                "kind": "action_request",
                "status": "pending",
                "lifecycle_current_state": "execution_pending",
                "latest_event_id": "rev_evt_10",
                "target_role": "implementer",
                "target_session_id": "s-old",
            },
            {
                "packet_id": "rev_pkt_new",
                "to_agent": "claude",
                "kind": "action_request",
                "status": "pending",
                "lifecycle_current_state": "delivery_pending",
                "latest_event_id": "rev_evt_11",
                "target_role": "implementer",
                "target_session_id": "s-new",
            },
        ],
    }

    projected = _attach_agent_loop_decisions(payload)

    claude_sync = projected["agent_sync"]["agents"]["claude"]
    assert claude_sync["attention_packet_id"] == ""
    assert claude_sync["attention_scope_state"] == "session_ambiguous"


def test_status_bundle_adds_queue_targeted_agent_loop_decision() -> None:
    payload = {
        "current_session": {"current_instruction_revision": "rev-current"},
        "attention": {"status": "checkpoint_required"},
        "queue": {
            "derived_next_instruction_source": {
                "packet_id": "rev_pkt_new",
                "to_agent": "claude",
                "target_role": "implementer",
                "target_session_id": "s-new",
            }
        },
        "reviewer_runtime": {
            "agent_runtime_clock": {
                "source_latest_event_id": "rev_evt_12",
                "snapshot_id": "agent-runtime-clock:rev_evt_12",
            }
        },
        "agent_sync": {
            "agents": {
                "claude": {
                    "attention_packet_id": "rev_pkt_old",
                    "pending_packets_to_me": ["rev_pkt_old", "rev_pkt_new"],
                }
            }
        },
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "s-old",
                    "active_packet_id": "rev_pkt_old",
                    "attention_packet_id": "rev_pkt_old",
                    "source_event_id": "rev_evt_10",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_old",
                "to_agent": "claude",
                "kind": "action_request",
                "status": "pending",
                "lifecycle_current_state": "execution_pending",
                "latest_event_id": "rev_evt_10",
            },
            {
                "packet_id": "rev_pkt_new",
                "to_agent": "claude",
                "kind": "action_request",
                "status": "pending",
                "lifecycle_current_state": "execution_pending",
                "latest_event_id": "rev_evt_12",
                "target_role": "implementer",
                "target_session_id": "s-new",
            },
        ],
    }

    projected = _attach_agent_loop_decisions(payload)

    decisions = {
        row["session_id"]: row
        for row in projected["agent_loop_decisions"]
        if row["actor_id"] == "claude"
    }
    assert decisions["s-new"]["active_packet_id"] == "rev_pkt_new"
    assert decisions["s-new"]["source_work_board_row"]["status"] == "queue_targeted"
    claude_sync = projected["agent_sync"]["agents"]["claude"]
    assert claude_sync["attention_packet_id"] == ""
    assert set(claude_sync["route_attention_packet_ids"]) == {
        "rev_pkt_new",
        "rev_pkt_old",
    }
    assert set(claude_sync["route_attention_packet_ids"]) == {
        "rev_pkt_new",
        "rev_pkt_old",
    }
