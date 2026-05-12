"""Focused tests for scoped packet attention/focus behavior."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.agent_packet_attention import (
    packet_attention_for_agent,
)
from dev.scripts.devctl.review_channel.agent_packet_focus import packet_focus_for_agent
from dev.scripts.devctl.review_channel.packet_body_observation import (
    packet_body_digest,
    packet_body_observed_by,
)


def test_attention_preserves_fallback_body_open_fields_without_authoritative_rows() -> None:
    fallback = {
        "observation_actor_id": "codex",
        "observation_session_id": "s1",
        "latest_inbox_event_id": "rev_evt_10",
        "latest_attention_packet_id": "rev_pkt_body",
        "latest_attention_changed_at_utc": "2026-05-11T18:00:00Z",
        "body_open_required": True,
        "body_open_packet_id": "rev_pkt_body",
        "body_open_command": "show rev_pkt_body",
        "unopened_body_packet_ids": ["rev_pkt_body"],
    }

    attention = packet_attention_for_agent(
        {"agent_sync": {"agents": {"codex": {}}}},
        actor="codex",
        role="reviewer",
        session="s1",
        fallback_attention=fallback,
    )

    assert attention.body_open_required is True
    assert attention.body_open_packet_id == "rev_pkt_body"
    assert attention.body_open_command == "show rev_pkt_body"
    assert attention.unopened_body_packet_ids == ("rev_pkt_body",)


def test_body_observation_requires_actor_role_session_tuple() -> None:
    packet = {
        "packet_id": "rev_pkt_body",
        "body": "Scoped packet body.",
    }
    digest = packet_body_digest(packet)
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "reviewer",
            "body_observed_session_id": "s1",
            "body_digest": digest,
        }
    ]

    assert packet_body_observed_by(
        packet,
        actor="codex",
        role="reviewer",
        session="s1",
    )
    assert not packet_body_observed_by(
        packet,
        actor="codex",
        role="implementer",
        session="s1",
    )
    assert not packet_body_observed_by(
        packet,
        actor="codex",
        role="reviewer",
        session="s2",
    )


def test_body_observation_accepts_frozen_event_tuple() -> None:
    packet = {
        "packet_id": "rev_pkt_body",
        "body": "Scoped packet body from a frozen dashboard snapshot.",
    }
    digest = packet_body_digest(packet)
    packet["body_observation_events"] = (
        {
            "body_observed_by": "codex",
            "body_observed_role": "reviewer",
            "body_observed_session_id": "s1",
            "body_digest": digest,
        },
    )

    assert packet_body_observed_by(
        packet,
        actor="codex",
        role="reviewer",
        session="s1",
    )


def test_frozen_body_observation_tuple_suppresses_body_open_gate() -> None:
    packet = {
        "packet_id": "rev_pkt_body",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "task_progress",
        "body": "Frozen dashboard snapshots keep events as tuples.",
        "status": "pending",
        "lifecycle_current_state": "task_progress",
        "latest_event_id": "rev_evt_40",
        "target_role": "reviewer",
        "target_session_id": "s1",
    }
    digest = packet_body_digest(packet)
    packet["body_observation_events"] = (
        {
            "body_observed_by": "codex",
            "body_observed_role": "reviewer",
            "body_observed_session_id": "s1",
            "body_digest": digest,
        },
    )

    attention = packet_attention_for_agent(
        {"packets": [packet]},
        actor="codex",
        role="reviewer",
        session="s1",
    )

    assert attention.body_open_required is False
    assert attention.body_open_packet_id == ""


def test_attention_body_open_gate_ignores_observation_from_other_session() -> None:
    packet = {
        "packet_id": "rev_pkt_body",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "action_request",
        "body": "Open me in the matching session.",
        "status": "pending",
        "lifecycle_current_state": "delivery_pending",
        "latest_event_id": "rev_evt_20",
        "target_role": "reviewer",
        "target_session_id": "s2",
    }
    digest = packet_body_digest(packet)
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "reviewer",
            "body_observed_session_id": "s1",
            "body_digest": digest,
        }
    ]

    attention = packet_attention_for_agent(
        {"packets": [packet]},
        actor="codex",
        role="reviewer",
        session="s2",
    )

    assert attention.body_open_required is True
    assert attention.body_open_packet_id == "rev_pkt_body"
    assert "--target-role reviewer" in attention.body_open_command
    assert "--target-session-id s2" in attention.body_open_command


def test_failed_durable_ingestion_receipt_does_not_suppress_body_open_gate() -> None:
    packet = {
        "packet_id": "rev_pkt_failed_ingest",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "action_request",
        "body": "Durable ingestion failed; body still must be opened.",
        "status": "pending",
        "lifecycle_current_state": "delivery_pending",
        "latest_event_id": "rev_evt_30",
        "target_role": "reviewer",
        "target_session_id": "s1",
        "packet_durable_ingestion_receipt": {"status": "failed"},
    }

    attention = packet_attention_for_agent(
        {"packets": [packet]},
        actor="codex",
        role="reviewer",
        session="s1",
    )

    assert attention.body_open_required is True
    assert attention.body_open_packet_id == "rev_pkt_failed_ingest"


def test_successful_durable_ingestion_receipt_suppresses_body_open_gate() -> None:
    packet = {
        "packet_id": "rev_pkt_ingested",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "action_request",
        "body": "Already durably ingested.",
        "status": "pending",
        "lifecycle_current_state": "delivery_pending",
        "latest_event_id": "rev_evt_31",
        "target_role": "reviewer",
        "target_session_id": "s1",
        "packet_durable_ingestion_receipt": {"status": "inserted"},
    }

    attention = packet_attention_for_agent(
        {"packets": [packet]},
        actor="codex",
        role="reviewer",
        session="s1",
    )

    assert attention.body_open_required is False


def test_urgent_attention_preempts_newer_active_packet() -> None:
    active = {
        "packet_id": "rev_pkt_active",
        "to_agent": "codex",
        "kind": "action_request",
        "status": "pending",
        "lifecycle_current_state": "delivery_pending",
        "latest_event_id": "rev_evt_200",
        "target_role": "reviewer",
        "target_session_id": "s1",
    }
    urgent = {
        "packet_id": "rev_pkt_urgent",
        "to_agent": "codex",
        "kind": "task_progress",
        "status": "pending",
        "lifecycle_current_state": "task_progress",
        "latest_event_id": "rev_evt_100",
        "target_role": "reviewer",
        "target_session_id": "s1",
        "attention_urgency": "urgent",
    }
    review_state = {
        "packets": [active, urgent],
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "codex",
                    "role": "reviewer",
                    "session_id": "s1",
                    "active_packet_id": "rev_pkt_active",
                    "attention_packet_id": "rev_pkt_active",
                }
            ]
        },
    }

    focus = packet_focus_for_agent(
        review_state,
        actor="codex",
        role="reviewer",
        session="s1",
        attention={"latest_attention_packet_id": "rev_pkt_urgent"},
    )

    assert focus.active_packet_id == "rev_pkt_active"
    assert focus.attention_packet_id == "rev_pkt_urgent"
