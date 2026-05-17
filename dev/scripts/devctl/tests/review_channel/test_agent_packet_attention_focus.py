"""Focused tests for scoped packet attention/focus behavior."""

from __future__ import annotations

from dataclasses import asdict

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


def test_observed_communication_only_packet_does_not_keep_runtime_awake() -> None:
    packet = {
        "packet_id": "rev_pkt_notice",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "task_produced",
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "attention_urgency": "blocking",
        "body": "Review-only advisory body.",
        "status": "pending",
        "lifecycle_current_state": "task_produced",
        "latest_event_id": "rev_evt_50",
        "target_role": "implementer",
        "packet_creation_binding": {"binding_target_kind": "communication_only"},
    }
    digest = packet_body_digest(packet)
    packet["body_observation_events"] = [
        {
            "body_observed_by": "claude",
            "body_observed_role": "implementer",
            "body_observed_session_id": "s1",
            "body_digest": digest,
        }
    ]
    review_state = {
        "packets": [packet],
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "s1",
                    "active_packet_id": "rev_pkt_notice",
                    "attention_packet_id": "rev_pkt_notice",
                }
            ]
        },
    }

    attention = packet_attention_for_agent(
        review_state,
        actor="claude",
        role="implementer",
        session="s1",
    )
    focus = packet_focus_for_agent(
        review_state,
        actor="claude",
        role="implementer",
        session="s1",
        attention=asdict(attention),
    )

    assert attention.pending_packet_count == 0
    assert attention.wake_required is False
    assert attention.pivot_required is False
    assert attention.body_open_required is False
    assert attention.latest_attention_packet_id == ""
    assert focus.active_packet_id == ""
    assert focus.attention_packet_id == ""


def test_unobserved_communication_only_packet_still_requires_body_open() -> None:
    packet = {
        "packet_id": "rev_pkt_notice",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "task_produced",
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "body": "Review-only advisory body.",
        "status": "pending",
        "lifecycle_current_state": "task_produced",
        "latest_event_id": "rev_evt_51",
        "target_role": "implementer",
        "target_session_id": "s1",
        "packet_creation_binding": {"binding_target_kind": "communication_only"},
    }

    attention = packet_attention_for_agent(
        {"packets": [packet]},
        actor="claude",
        role="implementer",
        session="s1",
    )

    assert attention.pending_packet_count == 1
    assert attention.body_open_required is True
    assert attention.body_open_packet_id == "rev_pkt_notice"


def test_observed_actionable_packet_stays_runtime_attention() -> None:
    packet = {
        "packet_id": "rev_pkt_action",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "action_request",
        "requested_action": "apply",
        "body": "This remains actionable after body observation.",
        "status": "pending",
        "lifecycle_current_state": "delivery_pending",
        "latest_event_id": "rev_evt_52",
        "target_role": "implementer",
        "target_session_id": "s1",
    }
    digest = packet_body_digest(packet)
    packet["body_observation_events"] = [
        {
            "body_observed_by": "claude",
            "body_observed_role": "implementer",
            "body_observed_session_id": "s1",
            "body_digest": digest,
        }
    ]

    attention = packet_attention_for_agent(
        {"packets": [packet]},
        actor="claude",
        role="implementer",
        session="s1",
    )

    assert attention.pending_packet_count == 1
    assert attention.body_open_required is False
    assert attention.latest_attention_packet_id == "rev_pkt_action"
    assert attention.wake_required is True


def test_durably_ingested_finding_with_route_observation_does_not_remain_runtime_attention() -> None:
    packet = {
        "packet_id": "rev_pkt_finding",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "finding",
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "attention_urgency": "blocking",
        "body": "Finding has already been folded into durable plan state.",
        "status": "pending",
        "lifecycle_current_state": "pending",
        "latest_event_id": "rev_evt_53",
        "target_role": "implementer",
        "target_session_id": "s1",
        "durable_binding": {
            "binding_target_kind": "plan_row",
            "status": "inserted",
        },
    }
    digest = packet_body_digest(packet)
    packet["body_observation_events"] = [
        {
            "body_observed_by": "claude",
            "body_observed_role": "implementer",
            "body_observed_session_id": "s1",
            "body_digest": digest,
        }
    ]

    attention = packet_attention_for_agent(
        {"packets": [packet]},
        actor="claude",
        role="implementer",
        session="s1",
    )

    assert attention.pending_packet_count == 0
    assert attention.body_open_required is False
    assert attention.latest_attention_packet_id == ""
    assert attention.wake_required is False


def test_durably_ingested_finding_stays_visible_until_route_observed() -> None:
    packet = {
        "packet_id": "rev_pkt_finding",
        "from_agent": "claude",
        "to_agent": "codex",
        "kind": "finding",
        "requested_action": "review_only",
        "policy_hint": "review_only",
        "attention_urgency": "blocking",
        "body": "Finding has already been folded into durable plan state.",
        "status": "pending",
        "lifecycle_current_state": "pending",
        "latest_event_id": "rev_evt_54",
        "target_role": "reviewer",
        "target_session_id": "s1",
        "durable_binding": {
            "binding_target_kind": "plan_row",
            "status": "inserted",
        },
    }
    digest = packet_body_digest(packet)
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "",
            "body_observed_session_id": "",
            "body_digest": digest,
        }
    ]

    attention = packet_attention_for_agent(
        {"packets": [packet]},
        actor="codex",
        role="reviewer",
        session="s1",
    )

    assert attention.pending_packet_count == 1
    assert attention.body_open_required is True
    assert attention.body_open_packet_id == "rev_pkt_finding"
    assert "--target-role reviewer" in attention.body_open_command
    assert "--target-session-id s1" in attention.body_open_command


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
