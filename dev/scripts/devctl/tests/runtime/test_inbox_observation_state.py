"""Focused tests for InboxObservationState pivot-required contract.

Per rev_pkt_2486: typed packet-arrival/pivot signal that lets agents catch
new packets without voluntary polling. Composes with rev_pkt_2470/2476
actor/session discriminator (ambiguous actor ⇒ fail closed).
"""

from __future__ import annotations

from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    InboxObservationState,
    build_inbox_observation_state,
)


def _baseline_kwargs() -> dict:
    return {
        "actor_id": "coder-claude",
        "session_id": "session-coder-abc",
        "last_inbox_event_id": "rev_evt_0042",
        "last_inbox_event_at_utc": "2026-04-30T15:00:00Z",
        "last_inbox_observed_event_id": "rev_evt_0042",
        "last_inbox_observed_at_utc": "2026-04-30T15:00:01Z",
        "pending_packet_count": 0,
    }


def test_inbox_observed_in_sync_renders_no_pivot() -> None:
    """When the actor's last_inbox_observed_event_id matches the latest event,
    pivot_required must be False — no architectural ping needed.
    """
    state = build_inbox_observation_state(**_baseline_kwargs())
    assert state.pivot_required is False
    assert state.pivot_reasons == ()


def test_new_packet_event_flips_pivot_required_until_observed() -> None:
    """Per rev_pkt_2486 Scope 4 case 1: a new packet event flips
    pivot_required True until the actor observes/ACKs it. The reason
    'inbox_event_unobserved' is the machine-readable signal a pre-mutation
    gate consumes.
    """
    kwargs = _baseline_kwargs()
    kwargs["last_inbox_event_id"] = "rev_evt_0043"
    kwargs["last_inbox_observed_event_id"] = "rev_evt_0042"
    state = build_inbox_observation_state(**kwargs)
    assert state.pivot_required is True
    assert "inbox_event_unobserved" in state.pivot_reasons


def test_pending_packets_force_pivot_even_when_event_id_observed() -> None:
    """If pending_packet_count > 0 but the actor hasn't ACKed/dismissed,
    pivot_required must still fire. Observing the event id alone doesn't
    discharge the action; consumption does.
    """
    kwargs = _baseline_kwargs()
    kwargs["pending_packet_count"] = 3
    state = build_inbox_observation_state(**kwargs)
    assert state.pivot_required is True
    assert "pending_packets_unconsumed" in state.pivot_reasons


def test_superseded_packet_id_forces_pivot() -> None:
    """Per rev_pkt_2486 Scope 4 case 2: a superseding Codex packet must
    interrupt older Claude active work. superseded_packet_id surfaces
    that intent to the renderer / pre-mutation gate.
    """
    kwargs = _baseline_kwargs()
    kwargs["superseded_packet_id"] = "rev_pkt_2466"
    state = build_inbox_observation_state(**kwargs)
    assert state.pivot_required is True
    assert "active_packet_superseded" in state.pivot_reasons


def test_ambiguous_actor_identity_fails_closed() -> None:
    """Per rev_pkt_2486 Scope 4 case 3 + rev_pkt_2470/2476 compatibility:
    when actor_id is empty (e.g. dashboard-claude vs coder-claude can't be
    disambiguated yet), the observation MUST fail closed (pivot_required=True)
    rather than satisfy any session as if all agents observed it.
    """
    kwargs = _baseline_kwargs()
    kwargs["actor_id"] = ""
    state = build_inbox_observation_state(**kwargs)
    assert state.pivot_required is True
    assert "actor_identity_ambiguous" in state.pivot_reasons


def test_default_state_is_empty_and_not_pivot_required() -> None:
    """The dataclass default must be a non-pivot empty state so that adding
    InboxObservationState to ReviewerRuntimeContract doesn't false-positive
    a pivot signal on every default-constructed contract.
    """
    state = InboxObservationState()
    assert state.pivot_required is False
    assert state.pivot_reasons == ()
    assert state.actor_id == ""
    assert state.session_id == ""
