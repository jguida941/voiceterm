import json
from argparse import Namespace
from pathlib import Path

from dev.scripts.devctl.runtime.control_decision_artifacts import (
    control_decision_input_for_route,
    control_decision_payload_from_mapping,
    load_control_decision_payload,
    write_control_decision_artifacts,
)


def test_control_decision_payload_selects_matching_actor_role_session() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "observer",
                "session_id": "old",
                "may_mutate": True,
                "source_latest_event_id": "rev_evt_1",
            },
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "may_mutate": False,
                "source_latest_event_id": "rev_evt_1",
            },
        ],
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision["session_id"] == "current"
    assert decision["may_mutate"] is False


def test_control_decision_input_for_route_returns_stable_artifact_path() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "source_latest_event_id": "rev_evt_2",
            }
        ],
    }

    path = control_decision_input_for_route(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert path == (
        "dev/reports/review_channel/control_decisions/"
        "rev_evt_2/codex-reviewer-current.json"
    )


def test_written_control_decision_artifact_survives_latest_state_change(
    tmp_path: Path,
) -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "decision": "wait",
                "may_mutate": False,
                "can_run_next_command": False,
                "absorption_required": True,
                "absorption_packet_id": "rev_pkt_old",
                "attention_packet_id": "rev_pkt_old",
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }
    written = write_control_decision_artifacts(payload, repo_root=tmp_path)
    latest = tmp_path / "dev/reports/review_channel/state/latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(
        json.dumps(
            {
                "contract_id": "ReviewState",
                "agent_runtime_clock": {"source_latest_event_id": "rev_evt_2"},
                "agent_loop_decisions": [
                    {
                        "contract_id": "AgentLoopDecision",
                        "actor_id": "codex",
                        "actor_role": "reviewer",
                        "session_id": "current",
                        "body_open_required": True,
                        "body_open_packet_id": "rev_pkt_new",
                        "source_latest_event_id": "rev_evt_2",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    decision = load_control_decision_payload(
        Namespace(
            actor="codex",
            role="reviewer",
            session_id="current",
            control_decision_input=str(written[0]),
        ),
        repo_root=tmp_path,
    )

    assert decision["source_latest_event_id"] == "rev_evt_1"
    assert decision["absorption_packet_id"] == "rev_pkt_old"


def test_load_control_decision_payload_reads_review_state_latest(tmp_path: Path) -> None:
    path = tmp_path / "dev/reports/review_channel/state/latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "contract_id": "ReviewState",
                "agent_loop_decisions": [
                    {
                        "contract_id": "AgentLoopDecision",
                        "actor_id": "codex",
                        "actor_role": "reviewer",
                        "session_id": "current",
                        "may_mutate": False,
                        "source_latest_event_id": "rev_evt_2",
                    }
                ],
                "agent_runtime_clock": {"source_latest_event_id": "rev_evt_2"},
            }
        ),
        encoding="utf-8",
    )

    decision = load_control_decision_payload(
        Namespace(actor="codex", role="reviewer", session_id="current"),
        repo_root=tmp_path,
    )

    assert decision["contract_id"] == "AgentLoopDecision"
    assert decision["may_mutate"] is False


def test_load_control_decision_payload_merges_matching_startup_authority_actions(
    tmp_path: Path,
) -> None:
    review_state_path = tmp_path / "dev/reports/review_channel/state/latest.json"
    review_state_path.parent.mkdir(parents=True, exist_ok=True)
    review_state_path.write_text(
        json.dumps(
            {
                "contract_id": "ReviewState",
                "agent_loop_decisions": [
                    {
                        "contract_id": "AgentLoopDecision",
                        "actor_id": "codex",
                        "actor_role": "reviewer",
                        "session_id": "current",
                        "may_mutate": False,
                        "can_run_next_command": False,
                        "allowed_actions": [],
                        "source_latest_event_id": "rev_evt_2",
                    }
                ],
                "agent_runtime_clock": {"source_latest_event_id": "rev_evt_2"},
            }
        ),
        encoding="utf-8",
    )
    startup_path = tmp_path / "dev/reports/startup/latest/receipt.json"
    startup_path.parent.mkdir(parents=True, exist_ok=True)
    startup_path.write_text(
        json.dumps(
            {
                "contract_id": "StartupReceipt",
                "authority_snapshot": {
                    "contract_id": "AuthoritySnapshot",
                    "actor_identity": "codex",
                    "actor_role": "reviewer",
                    "snapshot_id": "snap-startup",
                    "allowed_actions": [
                        "startup-context.summary",
                        "review-channel.post_finding",
                    ],
                    "blocked_actions": ["implementation.edit"],
                },
            }
        ),
        encoding="utf-8",
    )

    decision = load_control_decision_payload(
        Namespace(actor="codex", role="reviewer", session_id="current"),
        repo_root=tmp_path,
    )

    assert "review-channel.post_finding" in decision["allowed_actions"]
    assert "implementation.edit" in decision["blocked_actions"]
    assert decision["startup_authority_snapshot_id"] == "snap-startup"


def test_load_control_decision_payload_rejects_stale_startup_authority_head(
    tmp_path: Path,
) -> None:
    review_state_path = tmp_path / "dev/reports/review_channel/state/latest.json"
    review_state_path.parent.mkdir(parents=True, exist_ok=True)
    review_state_path.write_text(
        json.dumps(
            {
                "contract_id": "ReviewState",
                "source_identity": {"head_sha": "head-current"},
                "agent_loop_decisions": [
                    {
                        "contract_id": "AgentLoopDecision",
                        "actor_id": "codex",
                        "actor_role": "reviewer",
                        "session_id": "current",
                        "may_mutate": False,
                        "can_run_next_command": False,
                        "allowed_actions": [],
                        "source_latest_event_id": "rev_evt_2",
                    }
                ],
                "agent_runtime_clock": {"source_latest_event_id": "rev_evt_2"},
            }
        ),
        encoding="utf-8",
    )
    startup_path = tmp_path / "dev/reports/startup/latest/receipt.json"
    startup_path.parent.mkdir(parents=True, exist_ok=True)
    startup_path.write_text(
        json.dumps(
            {
                "contract_id": "StartupReceipt",
                "authority_snapshot": {
                    "contract_id": "AuthoritySnapshot",
                    "actor_identity": "codex",
                    "actor_role": "reviewer",
                    "snapshot_id": "snap-startup",
                    "source_identity": {"head_sha": "head-stale"},
                    "allowed_actions": ["review-channel.post_finding"],
                },
            }
        ),
        encoding="utf-8",
    )

    decision = load_control_decision_payload(
        Namespace(actor="codex", role="reviewer", session_id="current"),
        repo_root=tmp_path,
    )

    assert decision.get("source_head_sha") == "head-current"
    assert decision.get("allowed_actions") == []
    assert "startup_authority_snapshot_id" not in decision


def test_load_control_decision_payload_records_fresh_startup_authority_head(
    tmp_path: Path,
) -> None:
    review_state_path = tmp_path / "dev/reports/review_channel/state/latest.json"
    review_state_path.parent.mkdir(parents=True, exist_ok=True)
    review_state_path.write_text(
        json.dumps(
            {
                "contract_id": "ReviewState",
                "source_identity": {"head_sha": "head-current"},
                "agent_loop_decisions": [
                    {
                        "contract_id": "AgentLoopDecision",
                        "actor_id": "codex",
                        "actor_role": "reviewer",
                        "session_id": "current",
                        "may_mutate": False,
                        "can_run_next_command": False,
                        "allowed_actions": [],
                        "source_latest_event_id": "rev_evt_2",
                    }
                ],
                "agent_runtime_clock": {"source_latest_event_id": "rev_evt_2"},
            }
        ),
        encoding="utf-8",
    )
    startup_path = tmp_path / "dev/reports/startup/latest/receipt.json"
    startup_path.parent.mkdir(parents=True, exist_ok=True)
    startup_path.write_text(
        json.dumps(
            {
                "contract_id": "StartupReceipt",
                "authority_snapshot": {
                    "contract_id": "AuthoritySnapshot",
                    "actor_identity": "codex",
                    "actor_role": "reviewer",
                    "snapshot_id": "snap-startup",
                    "source_identity": {"head_sha": "head-current"},
                    "allowed_actions": ["review-channel.post_stop_anchor"],
                },
            }
        ),
        encoding="utf-8",
    )

    decision = load_control_decision_payload(
        Namespace(actor="codex", role="reviewer", session_id="current"),
        repo_root=tmp_path,
    )

    assert "review-channel.post_stop_anchor" in decision["allowed_actions"]
    assert decision["startup_authority_snapshot_id"] == "snap-startup"
    assert decision["startup_authority_source_head_sha"] == "head-current"


def test_load_control_decision_payload_does_not_merge_wrong_role_startup_authority(
    tmp_path: Path,
) -> None:
    review_state_path = tmp_path / "dev/reports/review_channel/state/latest.json"
    review_state_path.parent.mkdir(parents=True, exist_ok=True)
    review_state_path.write_text(
        json.dumps(
            {
                "contract_id": "ReviewState",
                "agent_loop_decisions": [
                    {
                        "contract_id": "AgentLoopDecision",
                        "actor_id": "codex",
                        "actor_role": "reviewer",
                        "session_id": "current",
                        "may_mutate": False,
                        "can_run_next_command": False,
                        "allowed_actions": [],
                        "source_latest_event_id": "rev_evt_2",
                    }
                ],
                "agent_runtime_clock": {"source_latest_event_id": "rev_evt_2"},
            }
        ),
        encoding="utf-8",
    )
    startup_path = tmp_path / "dev/reports/startup/latest/receipt.json"
    startup_path.parent.mkdir(parents=True, exist_ok=True)
    startup_path.write_text(
        json.dumps(
            {
                "contract_id": "StartupReceipt",
                "authority_snapshot": {
                    "contract_id": "AuthoritySnapshot",
                    "actor_identity": "codex",
                    "actor_role": "implementer",
                    "allowed_actions": ["review-channel.post_finding"],
                },
            }
        ),
        encoding="utf-8",
    )

    decision = load_control_decision_payload(
        Namespace(actor="codex", role="reviewer", session_id="current"),
        repo_root=tmp_path,
    )

    assert decision.get("allowed_actions") == []


def test_control_decision_payload_requires_unambiguous_scope() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "a",
                "source_latest_event_id": "rev_evt_1",
            },
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "b",
                "source_latest_event_id": "rev_evt_1",
            },
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="",
    )

    assert decision == {}


def test_control_decision_payload_requires_complete_actor_role_session_scope() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="",
    )

    assert decision == {}


def test_control_decision_payload_requires_source_metadata() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision == {}


def test_control_decision_payload_rejects_stale_event() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_2"},
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision == {}


def test_control_decision_payload_merges_packet_attention() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "packet_attention": {
            "body_open_required": True,
            "body_open_packet_id": "rev_pkt_1",
            "latest_attention_packet_id": "rev_pkt_2",
            "pending_packet_count": 3,
            "unopened_body_packet_ids": ["rev_pkt_1"],
            "pivot_required": True,
        },
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "may_mutate": False,
                "source_snapshot_id": "agent-runtime-clock:rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision["body_open_required"] is True
    assert decision["body_open_packet_id"] == "rev_pkt_1"
    assert decision["attention_packet_id"] == "rev_pkt_2"
    assert decision["pending_packet_count"] == 3
    assert decision["unopened_body_packet_ids"] == ["rev_pkt_1"]
    assert decision["pivot_required"] is True


def test_control_decision_payload_derives_body_open_from_decision_next_command() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "claude",
                "actor_role": "subagent",
                "session_id": "current",
                "decision": "run_next_command",
                "required_action": "open_packet_body",
                "reason_code": "packet_body_open_required",
                "may_mutate": False,
                "can_run_next_command": False,
                "active_packet_id": "rev_pkt_4300",
                "attention_packet_id": "rev_pkt_4300",
                "next_command": (
                    "python3 dev/scripts/devctl.py review-channel --action show "
                    "--packet-id rev_pkt_4300 --actor claude"
                ),
                "gate_failure": {
                    "violation_reason": "packet_body_open_required",
                },
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="claude",
        role="subagent",
        session_id="current",
    )

    assert decision["body_open_required"] is True
    assert decision["body_open_packet_id"] == "rev_pkt_4300"
    assert decision["attention_packet_id"] == "rev_pkt_4300"
    assert decision["unopened_body_packet_ids"] == ["rev_pkt_4300"]


def test_control_decision_payload_derives_semantic_ingestion_from_decision_next_command() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "claude",
                "actor_role": "dashboard",
                "session_id": "current",
                "decision": "run_next_command",
                "required_action": "ingest_packet_semantics",
                "reason_code": "packet_semantic_ingestion_required",
                "may_mutate": False,
                "can_run_next_command": False,
                "active_packet_id": "rev_pkt_4300",
                "attention_packet_id": "rev_pkt_4300",
                "next_command": (
                    "python3 dev/scripts/devctl.py review-channel --action ingest "
                    "--packet-id rev_pkt_4300 --actor claude"
                ),
                "gate_failure": {
                    "violation_reason": "packet_semantic_ingestion_required",
                },
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="claude",
        role="dashboard",
        session_id="current",
    )

    assert decision["semantic_ingestion_required"] is True
    assert decision["semantic_ingestion_packet_id"] == "rev_pkt_4300"
    assert decision["attention_packet_id"] == "rev_pkt_4300"


def test_control_decision_payload_derives_single_agent_sync_pending_packet() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "agent_sync": {
            "source_latest_event_id": "rev_evt_1",
            "agents": {
                "codex": {
                    "pending_packets_to_me": ["rev_pkt_4401"],
                }
            },
        },
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "may_mutate": False,
                "can_run_next_command": False,
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision["body_open_required"] is True
    assert decision["body_open_packet_id"] == "rev_pkt_4401"
    assert decision["attention_packet_id"] == "rev_pkt_4401"
    assert decision["pending_packet_count"] == 1


def test_control_decision_payload_prefers_rebuilt_inbox_over_stale_agent_sync() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "packet_attention": {
            "body_open_required": False,
            "body_open_packet_id": "",
            "latest_attention_packet_id": "rev_pkt_stale_global",
            "pending_packet_count": 95,
        },
        "agent_sync": {
            "source_latest_event_id": "rev_evt_1",
            "agents": {
                "codex": {
                    "pending_packets_to_me": ["rev_pkt_stale_sync"],
                }
            },
        },
        "packets": [
            {
                "packet_id": "rev_pkt_4429",
                "from_agent": "operator",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "summary": "Fresh inbox finding",
                "body": "The fresh inbox packet must authorize body-open.",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ],
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "decision": "wait",
                "required_action": "wait_for_scoped_packet",
                "may_mutate": False,
                "can_run_next_command": False,
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision["body_open_required"] is True
    assert decision["body_open_packet_id"] == "rev_pkt_4429"
    assert decision["attention_packet_id"] == "rev_pkt_4429"
    assert decision["unopened_body_packet_ids"] == ["rev_pkt_4429"]


def test_control_decision_payload_prefers_scoped_agent_sync_over_reviewer_runtime() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "agent_sync": {
            "source_latest_event_id": "rev_evt_1",
            "agents": {
                "codex": {
                    "pending_packets_to_me": ["rev_pkt_4401"],
                }
            },
        },
        "reviewer_runtime": {
            "packet_attention": {
                "body_open_required": False,
                "body_open_packet_id": "",
                "latest_attention_packet_id": "rev_pkt_stale",
                "pending_packet_count": 96,
            }
        },
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "may_mutate": False,
                "can_run_next_command": False,
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision["body_open_required"] is True
    assert decision["body_open_packet_id"] == "rev_pkt_4401"
    assert decision["attention_packet_id"] == "rev_pkt_4401"


def test_control_decision_payload_prefers_scoped_agent_sync_over_global_attention() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "packet_attention": {
            "body_open_required": False,
            "body_open_packet_id": "",
            "latest_attention_packet_id": "rev_pkt_stale",
            "pending_packet_count": 96,
        },
        "agent_sync": {
            "source_latest_event_id": "rev_evt_1",
            "agents": {
                "codex": {
                    "pending_packets_to_me": ["rev_pkt_4401"],
                }
            },
        },
        "packets": [
            {
                "packet_id": "rev_pkt_4401",
                "kind": "decision",
                "status": "pending",
                "body_digest": "digest-1",
                "body_observed_at_utc": "2026-05-18T00:00:00Z",
                "packet_semantic_ingestion_receipt": {
                    "contract_id": "PacketSemanticIngestionReceipt",
                    "receipt_id": "packet_semantic_ingestion:rev_pkt_4401:test",
                    "packet_id": "rev_pkt_4401",
                    "body_sha256": "digest-1",
                    "ingested_by_actor": "codex",
                    "ingested_by_role": "reviewer",
                    "ingested_by_session_id": "current",
                    "ingested_at_utc": "2026-05-18T00:01:00Z",
                    "resulting_decision": "semantic_ingestion_recorded",
                    "decision_rationale": "packet body parsed into typed rows",
                    "action_item_rows": [
                        {
                            "contract_id": "PacketSemanticActionItem",
                            "schema_version": 1,
                            "action_item_id": "rev_pkt_4401:item",
                            "kind": "next_slice_request",
                            "disposition": "accepted",
                            "target_ref": "checkpoint_staging_gate",
                            "slice_ref": "raw-publication-audit-and-lifecycle-gates",
                            "packet_ref": "rev_pkt_4401",
                            "reason": "Continue the scoped next slice.",
                            "evidence_refs": ["packet:rev_pkt_4401"],
                        }
                    ],
                },
            }
        ],
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "may_mutate": False,
                "can_run_next_command": False,
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision["absorption_required"] is True
    assert decision["absorption_packet_id"] == "rev_pkt_4401"
    assert decision["attention_packet_id"] == "rev_pkt_4401"
    assert decision["pending_packet_count"] == 1


def test_control_decision_payload_keeps_absorbed_action_request_as_checkpoint_pressure() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "agent_sync": {
            "source_latest_event_id": "rev_evt_1",
            "agents": {
                "codex": {
                    "pending_packets_to_me": ["rev_pkt_checkpoint"],
                }
            },
        },
        "packets": [
            {
                "packet_id": "rev_pkt_checkpoint",
                "kind": "action_request",
                "requested_action": "stage_commit_pipeline",
                "target_kind": "runtime",
                "target_ref": "devctl_commit:lifecycle_proxy_absorb_checkpoint",
                "status": "pending",
                "lifecycle_current_state": "absorbed",
                "disposition": {"sink": "absorbed"},
                "packet_absorption_receipt": {
                    "contract_id": "PacketAbsorptionReceipt",
                    "packet_id": "rev_pkt_checkpoint",
                    "body_sha256": "digest-1",
                    "absorbed_by_actor": "codex",
                    "absorbed_by_role": "reviewer",
                    "absorbed_by_session_id": "current",
                    "absorbed_at_utc": "2026-05-18T00:01:00Z",
                    "source_semantic_ingestion_receipt_id": (
                        "packet_semantic_ingestion:rev_pkt_checkpoint:test"
                    ),
                    "action_item_dispositions": [
                        "rev_pkt_checkpoint:stage_commit_pipeline:accepted"
                    ],
                    "resulting_decision": "stage_commit_pipeline_action_request_parsed",
                    "decision_rationale": (
                        "action_request still awaits governed commit consumption"
                    ),
                    "evidence_refs": ["packet:rev_pkt_checkpoint#body_observed"],
                },
            }
        ],
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "may_mutate": False,
                "can_run_next_command": False,
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision["attention_packet_id"] == "rev_pkt_checkpoint"
    assert decision["pending_packet_count"] == 1
    assert decision.get("absorption_required") is not True
    assert decision.get("semantic_ingestion_required") is not True


def test_control_decision_payload_rejects_ambiguous_agent_sync_pending_packets() -> None:
    payload = {
        "contract_id": "ReviewState",
        "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
        "agent_sync": {
            "source_latest_event_id": "rev_evt_1",
            "agents": {
                "codex": {
                    "pending_packets_to_me": ["rev_pkt_4401", "rev_pkt_4402"],
                }
            },
        },
        "agent_loop_decisions": [
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "current",
                "may_mutate": False,
                "can_run_next_command": False,
                "source_latest_event_id": "rev_evt_1",
            }
        ],
    }

    decision = control_decision_payload_from_mapping(
        payload,
        actor="codex",
        role="reviewer",
        session_id="current",
    )

    assert decision.get("body_open_required") is not True
    assert not decision.get("body_open_packet_id")
