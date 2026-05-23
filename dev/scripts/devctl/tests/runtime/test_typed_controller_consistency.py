"""Typed-controller coherence tests for lane-barrier-driven attention.

Operator-asserted contradiction (May 22, 2026): ``review-channel
--action sync-status`` reported

    ## Lane Barriers (typed)
    - codex blocked by awaiting_reviewer_ack: target_packet=rev_pkt_4843
      target_actor=claude
    - operator blocked by awaiting_reviewer_ack: target_packet=rev_pkt_4804
      target_actor=claude

while ``develop next --actor agent`` (resolved to ``codex`` via fallback) at
the same source_latest_event_id emitted

    ## Inbox Attention
    - attention_required: False
    - pending_actionable_packet_ids: (none)

The typed work-board lane-barrier reducer
(``review_channel/agent_work_board_barriers.py``) reads
``agent_sync.agents[actor].awaiting_packet_id`` /
``agent_sync.agents[actor].awaiting_from_agent`` and emits an
``awaiting_reviewer_ack`` barrier, but
``commands/development/packet_attention.py::packet_attention_from_review_state``
only consults the actor's INBOUND ``packet_inbox`` record. An actor blocked
on OUTBOUND ``awaiting_reviewer_ack`` (their own packet awaiting peer ack)
is therefore invisible to the develop-controller's attention reducer, so
the controller declares ``attention_required=False`` while the same
review_state simultaneously asserts the actor's lane is blocked. This file
encodes the missing invariant.
"""

from __future__ import annotations

from dev.scripts.devctl.commands.development.packet_attention import (
    packet_attention_from_review_state,
)


def _baseline_packet(packet_id: str, *, to_agent: str, from_agent: str) -> dict:
    return {
        "packet_id": packet_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "kind": "action_request",
        "requested_action": "stage_commit_pipeline",
        "status": "pending",
        "expires_at_utc": "2999-01-01T00:00:00Z",
    }


def test_outbound_awaiting_reviewer_ack_drives_attention_required_for_codex() -> None:
    """Lane-barrier invariant: when agent_sync says ``codex`` is awaiting
    ``claude`` ack on rev_pkt_4843, codex's typed
    ``DevelopmentPacketAttention`` MUST surface
    ``attention_required=True`` so the controller cannot tell the actor
    "no work to do" while the lane is blocked on a peer ack.
    """
    review_state = {
        "packets": [
            _baseline_packet(
                "rev_pkt_4843",
                to_agent="claude",
                from_agent="codex",
            ),
        ],
        "agent_sync": {
            "agents": {
                "codex": {
                    "agent_id": "codex",
                    "awaiting_packet_id": "rev_pkt_4843",
                    "awaiting_from_agent": "claude",
                    "derived_status": "blocked",
                    "active_action_requests_to_me": [],
                    "pending_packets_to_me": [],
                },
            },
        },
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        agent="codex",
    )

    assert attention.attention_required is True, (
        "Codex lane is awaiting claude ack on rev_pkt_4843; "
        "controller must not return attention_required=False"
    )
    assert attention.attention_status != "none"
    assert attention.wake_reason == "awaiting_reviewer_ack"
    assert attention.latest_attention_packet_id == "rev_pkt_4843"
    assert "rev_pkt_4843" in attention.pending_actionable_packet_ids


def test_outbound_awaiting_reviewer_ack_drives_attention_required_for_operator() -> None:
    """Lane-barrier invariant: same coherence rule for the operator lane."""
    review_state = {
        "packets": [
            _baseline_packet(
                "rev_pkt_4804",
                to_agent="claude",
                from_agent="operator",
            ),
        ],
        "agent_sync": {
            "agents": {
                "operator": {
                    "agent_id": "operator",
                    "awaiting_packet_id": "rev_pkt_4804",
                    "awaiting_from_agent": "claude",
                    "derived_status": "blocked",
                    "active_action_requests_to_me": [],
                    "pending_packets_to_me": [],
                },
            },
        },
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        agent="operator",
    )

    assert attention.attention_required is True
    assert attention.wake_reason == "awaiting_reviewer_ack"
    assert attention.latest_attention_packet_id == "rev_pkt_4804"


def test_no_awaiting_packet_keeps_attention_required_false_when_inbox_empty() -> None:
    """Coherence-negative: when neither the inbox nor the lane barriers carry
    pending work for the actor, ``attention_required`` stays False so the
    fix does not over-trigger on healthy steady-state.
    """
    review_state = {
        "packets": [],
        "agent_sync": {
            "agents": {
                "codex": {
                    "agent_id": "codex",
                    "awaiting_packet_id": "",
                    "awaiting_from_agent": "",
                    "derived_status": "idle",
                    "active_action_requests_to_me": [],
                    "pending_packets_to_me": [],
                },
            },
        },
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        agent="codex",
    )

    assert attention.attention_required is False
    assert attention.wake_reason == ""
    assert attention.pending_actionable_packet_ids == ()


def test_awaiting_packet_dropped_from_live_inbox_does_not_force_attention() -> None:
    """When the awaited packet is no longer present in the live inbox (e.g.
    it was already acked / disposed), the lane-barrier reducer must not
    revive it as forced attention. This guards against stale agent_sync
    rows out-pacing live packet liveness.
    """
    review_state = {
        "packets": [],  # rev_pkt_4843 already cleared from inbox
        "agent_sync": {
            "agents": {
                "codex": {
                    "agent_id": "codex",
                    "awaiting_packet_id": "rev_pkt_4843",
                    "awaiting_from_agent": "claude",
                    "derived_status": "blocked",
                    "active_action_requests_to_me": [],
                    "pending_packets_to_me": [],
                },
            },
        },
    }

    attention = packet_attention_from_review_state(
        review_state,
        rows=(),
        agent="codex",
    )

    assert attention.attention_required is False
    assert attention.wake_reason == ""
