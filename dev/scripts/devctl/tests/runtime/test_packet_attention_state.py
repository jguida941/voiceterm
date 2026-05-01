"""Focused tests for AgentRuntimeClock + PacketAttentionState.

Per rev_pkt_2498: typed shared wake/attention runtime that supersedes the
env-var pivot workaround. Tests cover the 7 required cases:
- new packet wakes Claude AND blocks old work until observed
- superseding Codex packet interrupts active Claude work
- dashboard observation cannot satisfy coder Claude
- stale/missing wake snapshot blocks (this is the gate-side concern; tested
  separately via the commit gate suite)
- all agents render from the same source_latest_event_id
"""

from __future__ import annotations

from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    AgentRuntimeClock,
    PacketAttentionState,
    build_agent_runtime_clock,
    build_packet_attention_state,
)


def _baseline_kwargs() -> dict:
    return {
        "observation_actor_id": "coder-claude",
        "observation_session_id": "session-coder-abc",
        "latest_inbox_event_id": "evt-100",
        "latest_attention_packet_id": "rev_pkt_2498",
        "latest_attention_changed_at_utc": "2026-04-30T16:00:00Z",
        "last_observed_event_id": "evt-100",
        "last_observed_at_utc": "2026-04-30T16:00:01Z",
        "pending_packet_count": 0,
    }


def test_attention_state_observed_in_sync_renders_no_wake() -> None:
    """When the actor's last_observed_event_id matches latest_inbox_event_id
    AND there are no pending packets, neither wake_required nor pivot_required
    fires. Healthy steady-state.
    """
    state = build_packet_attention_state(**_baseline_kwargs())
    assert state.wake_required is False
    assert state.pivot_required is False
    assert state.stale_reason == ""
    assert state.pivot_reasons == ()


def test_new_packet_wakes_claude_and_blocks_old_work() -> None:
    """Per rev_pkt_2498 (7) test 1: a new packet event MUST flip wake_required
    True for an actor whose last_observed_event_id is behind the shared clock.
    pivot_required MUST also fire so the mutation gate blocks until observed.
    """
    kwargs = _baseline_kwargs()
    kwargs["latest_inbox_event_id"] = "evt-101"
    kwargs["last_observed_event_id"] = "evt-100"
    state = build_packet_attention_state(**kwargs)
    assert state.wake_required is True
    assert state.pivot_required is True
    assert "inbox_event_unobserved" in state.pivot_reasons
    assert state.stale_reason == "wake_required"


def test_superseding_codex_packet_interrupts_active_claude_work() -> None:
    """Per rev_pkt_2498 (7) test 2: a superseding packet (Codex dismissed
    Claude's prior active and routed a new one) MUST mark wake_required so
    the runtime can interrupt the older work. superseded_packet_id surfaces
    the interrupt cause as machine-readable.
    """
    kwargs = _baseline_kwargs()
    kwargs["superseded_packet_id"] = "rev_pkt_2466"
    state = build_packet_attention_state(**kwargs)
    assert state.wake_required is True
    assert "active_packet_superseded" in state.pivot_reasons
    assert state.superseded_packet_id == "rev_pkt_2466"


def test_dashboard_observation_cannot_satisfy_coder_claude() -> None:
    """Per rev_pkt_2498 (7) test 3 + (5): when actor identity is empty
    (typed routing not enforced or env doesn't disambiguate), the
    observation MUST fail closed. dashboard-claude marking attention
    cannot satisfy coder-claude's wake requirement.
    """
    kwargs = _baseline_kwargs()
    kwargs["observation_actor_id"] = ""
    kwargs["observation_session_id"] = ""
    state = build_packet_attention_state(**kwargs)
    assert state.pivot_required is True
    assert "actor_identity_ambiguous" in state.pivot_reasons
    # Even when no pending events, ambiguous identity alone fails closed.


def test_attention_state_pending_packets_force_wake() -> None:
    """When pending_packet_count > 0, wake_required and pivot_required MUST
    fire regardless of event id matching. Observation of event id alone
    doesn't discharge the action; consumption does.
    """
    kwargs = _baseline_kwargs()
    kwargs["pending_packet_count"] = 4
    state = build_packet_attention_state(**kwargs)
    assert state.wake_required is True
    assert "pending_packets_unconsumed" in state.pivot_reasons


def test_runtime_clock_carries_source_event_evidence() -> None:
    """Per rev_pkt_2498 (1): AgentRuntimeClock binds all agents to one
    source_latest_event_id. Builder threads through typed evidence cleanly.
    """
    clock = build_agent_runtime_clock(
        source_latest_event_id="evt-101",
        source_latest_event_at_utc="2026-04-30T16:00:00Z",
        cadence_seconds=30,
        last_published_at_utc="2026-04-30T16:00:30Z",
        snapshot_id="snap-abc",
    )
    assert clock.source_latest_event_id == "evt-101"
    assert clock.cadence_seconds == 30
    assert clock.snapshot_id == "snap-abc"


def test_default_attention_state_is_empty_no_wake() -> None:
    """Default-constructed PacketAttentionState must NOT spuriously fire
    wake_required so that adding it to ReviewerRuntimeContract doesn't
    false-positive on every default contract.
    """
    state = PacketAttentionState()
    assert state.wake_required is False
    assert state.pivot_required is False
    assert state.stale_reason == ""
    assert state.pivot_reasons == ()


def test_default_runtime_clock_is_empty() -> None:
    """Default-constructed AgentRuntimeClock has empty cursor and is safe
    as a default field on ReviewerRuntimeContract.
    """
    clock = AgentRuntimeClock()
    assert clock.source_latest_event_id == ""
    assert clock.cadence_seconds == 0
    assert clock.snapshot_id == ""


# Per rev_pkt_2498 (3): wake-evidence derivation tests
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    WakeEvidence,
    derive_wake_evidence_for_actor,
)


def test_wake_evidence_finds_latest_packet_for_actor() -> None:
    """Per rev_pkt_2498 (3): typed derivation finds the latest packet event
    targeting the actor, regardless of intervening events for other actors.
    """
    events = [
        {
            "event_type": "packet_posted",
            "event_id": "evt-001",
            "timestamp_utc": "2026-04-30T15:00:00Z",
            "to_agent": "codex",
            "packet_id": "rev_pkt_aaa",
        },
        {
            "event_type": "packet_posted",
            "event_id": "evt-002",
            "timestamp_utc": "2026-04-30T15:01:00Z",
            "to_agent": "claude",
            "packet_id": "rev_pkt_bbb",
        },
        {
            "event_type": "packet_posted",
            "event_id": "evt-003",
            "timestamp_utc": "2026-04-30T15:02:00Z",
            "to_agent": "codex",
            "packet_id": "rev_pkt_ccc",
        },
    ]
    evidence = derive_wake_evidence_for_actor(
        events=events,
        actor_id="claude",
        session_id="session-1",
    )
    assert evidence.latest_relevant_event_id == "evt-002"
    assert evidence.latest_relevant_packet_id == "rev_pkt_bbb"
    assert evidence.arrival_kind == "packet_arrival"


def test_wake_evidence_respects_target_session_id_discriminator() -> None:
    """Per rev_pkt_2498 (5): when target_session_id is set on an event,
    only the matching session sees it as wake-relevant. Different session
    receives no relevant evidence even if to_agent matches.
    """
    events = [
        {
            "event_type": "packet_posted",
            "event_id": "evt-100",
            "timestamp_utc": "2026-04-30T15:00:00Z",
            "to_agent": "claude",
            "target_session_id": "session-coder",
            "packet_id": "rev_pkt_coder_only",
        },
    ]
    coder_evidence = derive_wake_evidence_for_actor(
        events=events,
        actor_id="claude",
        session_id="session-coder",
    )
    dashboard_evidence = derive_wake_evidence_for_actor(
        events=events,
        actor_id="claude",
        session_id="session-dashboard",
    )
    assert coder_evidence.latest_relevant_event_id == "evt-100"
    assert dashboard_evidence.latest_relevant_event_id == ""


def test_wake_evidence_empty_actor_id_fails_closed() -> None:
    """Per rev_pkt_2498 (5): empty actor_id is ambiguous; derivation MUST
    return empty WakeEvidence so the PacketAttentionState consumer marks
    pivot_required. No bypass via "I observed it as everyone".
    """
    events = [
        {
            "event_type": "packet_posted",
            "event_id": "evt-001",
            "to_agent": "claude",
        },
    ]
    evidence = derive_wake_evidence_for_actor(
        events=events,
        actor_id="",
        session_id="",
    )
    assert evidence.latest_relevant_event_id == ""
    assert evidence.arrival_kind == "none"


def test_wake_evidence_active_packet_changed_event_marks_correct_kind() -> None:
    """Per rev_pkt_2498 (3): active_packet_changed events must be classified
    distinctly from packet_arrival, so consumers can render the interrupt
    intent correctly.
    """
    events = [
        {
            "event_type": "active_packet_changed",
            "event_id": "evt-200",
            "timestamp_utc": "2026-04-30T15:00:00Z",
            "to_agent": "claude",
            "packet_id": "rev_pkt_2498",
        },
    ]
    evidence = derive_wake_evidence_for_actor(
        events=events,
        actor_id="claude",
        session_id="any",
    )
    assert evidence.arrival_kind == "active_packet_changed"
    assert evidence.latest_relevant_event_id == "evt-200"


def test_wake_evidence_default_is_empty() -> None:
    """Default WakeEvidence is safe: arrival_kind='none', empty fields."""
    evidence = WakeEvidence()
    assert evidence.arrival_kind == "none"
    assert evidence.latest_relevant_event_id == ""
    assert evidence.actor_id == ""
