import json
from argparse import Namespace
from pathlib import Path

from dev.scripts.devctl.runtime.control_decision_artifacts import (
    control_decision_payload_from_mapping,
    load_control_decision_payload,
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
