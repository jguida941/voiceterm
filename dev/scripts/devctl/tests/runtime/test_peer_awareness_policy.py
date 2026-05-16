"""Tests for PeerAwarenessPolicy and agent-message boundary checks."""

from __future__ import annotations

import hashlib

from dev.scripts.devctl.runtime.peer_awareness_policy import (
    AGENT_MESSAGE_EMIT_BOUNDARY,
    PACKET_BODY_OBSERVATION,
    PEER_AGENT_MIND_OBSERVATION,
    REVIEW_CHANNEL_INBOX_OBSERVATION,
    SUBPROCESS_HEARTBEAT_BOUNDARY,
    agent_message_boundary_decision,
    default_peer_awareness_policy,
)


def _packet(*, observed: bool = False) -> dict[str, object]:
    body = "Codex must read this before continuing."
    packet = {
        "packet_id": "rev_pkt_101",
        "kind": "instruction",
        "from_agent": "claude",
        "to_agent": "codex",
        "target_role": "implementer",
        "target_session_id": "sess-codex",
        "status": "pending",
        "body": body,
        "posted_at": "2026-05-13T00:00:00Z",
        "expires_at_utc": "2999-01-01T00:00:00Z",
    }
    if observed:
        packet["body_observation_events"] = [
            {
                "body_observed_by": "codex",
                "body_observed_role": "implementer",
                "body_observed_session_id": "sess-codex",
                "body_digest": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            }
        ]
    return packet


def test_long_running_implementer_policy_requires_peer_and_body_observations() -> None:
    policy = default_peer_awareness_policy(
        role="implementer",
        work_class="long_running_subprocess",
        peer_provider="claude",
    )

    assert policy.contract_id == "PeerAwarenessPolicy"
    assert policy.cadence_seconds == 300
    assert policy.boundary_events == (
        AGENT_MESSAGE_EMIT_BOUNDARY,
        SUBPROCESS_HEARTBEAT_BOUNDARY,
    )
    assert policy.required_observations == (
        REVIEW_CHANNEL_INBOX_OBSERVATION,
        PEER_AGENT_MIND_OBSERVATION,
        PACKET_BODY_OBSERVATION,
    )


def test_agent_message_boundary_requires_packet_body_observation_first() -> None:
    decision = agent_message_boundary_decision(
        packets=[_packet(observed=False)],
        actor="codex",
        actor_role="implementer",
        session_id="sess-codex",
        policy=default_peer_awareness_policy(
            role="implementer",
            work_class="long_running_subprocess",
            peer_provider="claude",
        ),
        boundary_at_utc="2026-05-13T01:00:00Z",
    )

    assert decision.action == "open_packet_body"
    assert decision.body_open_required is True
    assert decision.blocking_packet_id == "rev_pkt_101"
    assert "--action show" in decision.next_commands[0]
    assert "--packet-id rev_pkt_101" in decision.next_commands[0]


def test_agent_message_boundary_polls_peer_after_body_observed() -> None:
    decision = agent_message_boundary_decision(
        packets=[_packet(observed=True)],
        actor="codex",
        actor_role="implementer",
        session_id="sess-codex",
        policy=default_peer_awareness_policy(
            role="implementer",
            work_class="long_running_subprocess",
            peer_provider="claude",
        ),
        boundary_at_utc="2026-05-13T01:00:00Z",
        last_peer_poll_at_utc="",
        pending_packet_count=1,
    )

    assert decision.action == "poll_peer_state"
    assert decision.poll_due is True
    assert any("review-channel --action inbox" in command for command in decision.next_commands)
    assert any("agent-mind --agent claude" in command for command in decision.next_commands)


def test_agent_message_boundary_launches_digest_sidecar_when_toggle_enabled() -> None:
    decision = agent_message_boundary_decision(
        packets=[_packet(observed=True)],
        actor="codex",
        actor_role="implementer",
        session_id="sess-codex",
        policy=default_peer_awareness_policy(
            role="implementer",
            work_class="long_running_subprocess",
            peer_provider="claude",
            digest_sidecar_enabled=True,
            digest_sidecar_provider="claude",
        ),
        boundary_at_utc="2026-05-13T01:00:00Z",
        last_peer_poll_at_utc="",
        pending_packet_count=1,
    )

    assert decision.action == "launch_digest_sidecar"
    assert decision.reason == "digest_sidecar_due_at_agent_message_emit"
    assert decision.sidecar_required is True
    assert decision.sidecar_provider == "claude"
    assert decision.poll_due is True
    assert any("review-channel --action inbox" in command for command in decision.next_commands)
    assert any("agent-mind --agent claude" in command for command in decision.next_commands)


def test_agent_message_boundary_polls_peer_after_cadence_expires() -> None:
    decision = agent_message_boundary_decision(
        packets=[],
        actor="codex",
        actor_role="implementer",
        session_id="sess-codex",
        policy=default_peer_awareness_policy(
            role="implementer",
            work_class="long_running_subprocess",
            peer_provider="claude",
        ),
        boundary_at_utc="2026-05-13T01:06:00Z",
        last_peer_poll_at_utc="2026-05-13T01:00:00Z",
    )

    assert decision.action == "poll_peer_state"
    assert decision.poll_due is True


def test_agent_message_boundary_continues_when_peer_awareness_current() -> None:
    decision = agent_message_boundary_decision(
        packets=[],
        actor="codex",
        actor_role="implementer",
        session_id="sess-codex",
        policy=default_peer_awareness_policy(
            role="implementer",
            work_class="long_running_subprocess",
            peer_provider="claude",
        ),
        boundary_at_utc="2026-05-13T01:00:00Z",
        last_peer_poll_at_utc="2026-05-13T01:00:01Z",
    )

    assert decision.action == "continue_current_work"
    assert decision.next_commands == ()


def test_agent_message_boundary_continues_when_recent_poll_is_within_cadence() -> None:
    decision = agent_message_boundary_decision(
        packets=[],
        actor="codex",
        actor_role="implementer",
        session_id="sess-codex",
        policy=default_peer_awareness_policy(
            role="implementer",
            work_class="long_running_subprocess",
            peer_provider="claude",
        ),
        boundary_at_utc="2026-05-13T01:04:59Z",
        last_peer_poll_at_utc="2026-05-13T01:00:00Z",
    )

    assert decision.action == "continue_current_work"
    assert decision.poll_due is False
