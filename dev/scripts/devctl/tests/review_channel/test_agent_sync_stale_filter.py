"""Regression tests for stale-active-packet filter in agent_sync projection.

Per Codex rev_pkt_2386: closed Codex verifier sessions remained
``status=working`` because ``_classify_inbound_packets`` was returning 27
historical action_requests in ``active_action_requests_to_me`` for codex.
None of those packets had reached a terminal lifecycle, but their event-
id rank was thousands behind the head — they were NOT what the agent
was currently working on, just stale records that never resolved.

The fix mirrors the ``_STALE_LIFECYCLE_RANK_GAP`` filter from
``active_packet_authority.current_active_packet_for_agent``: skip any
candidate whose ``latest_event_id`` is more than 1000 ranks behind the
current event-log head.
"""

from __future__ import annotations

# Pre-load the commands package so cross-package imports resolve in CLI
# order — same workaround used by other typed-convergence regressions.
from dev.scripts.devctl import cli as _cli  # noqa: F401

from dev.scripts.devctl.review_channel.agent_sync_projection import (
    _classify_inbound_packets,
)


def _packet_row(
    *,
    packet_id: str,
    to_agent: str,
    lifecycle: str = "in_progress",
    kind: str = "action_request",
    latest_event_id: str = "rev_evt_1000",
) -> dict:
    return {
        "packet_id": packet_id,
        "to_agent": to_agent,
        "kind": kind,
        "lifecycle_current_state": lifecycle,
        "status": "",
        "latest_event_id": latest_event_id,
    }


def test_classify_inbound_filters_stale_historical_active_packets() -> None:
    rows = [
        _packet_row(packet_id="rev_pkt_0171", to_agent="codex",
                    latest_event_id="rev_evt_171"),
        _packet_row(packet_id="rev_pkt_0420", to_agent="codex",
                    latest_event_id="rev_evt_420"),
        _packet_row(packet_id="rev_pkt_2394", to_agent="codex",
                    latest_event_id="rev_evt_45642"),
    ]
    pending, active = _classify_inbound_packets(
        agent_id="codex", packet_rows=rows
    )
    assert pending == []
    # Only the recent packet survives; rev_pkt_0171/0420 are filtered as stale
    # (head=45642 - 171 = 45471 > 1000 gap; head - 420 = 45222 > 1000 gap).
    assert active == ["rev_pkt_2394"]


def test_classify_inbound_keeps_recent_active_packets() -> None:
    rows = [
        _packet_row(packet_id="rev_pkt_2390", to_agent="claude",
                    latest_event_id="rev_evt_45000"),
        _packet_row(packet_id="rev_pkt_2391", to_agent="claude",
                    latest_event_id="rev_evt_45100"),
        _packet_row(packet_id="rev_pkt_2392", to_agent="claude",
                    latest_event_id="rev_evt_45200"),
    ]
    pending, active = _classify_inbound_packets(
        agent_id="claude", packet_rows=rows
    )
    assert pending == []
    # All three within rank gap of 1000 — all stay active.
    assert sorted(active) == [
        "rev_pkt_2390",
        "rev_pkt_2391",
        "rev_pkt_2392",
    ]


def test_classify_inbound_does_not_drop_pending_packets() -> None:
    """Pending lifecycle packets are not subject to the rank-gap filter.

    The filter targets stale ACTIVE packets — pending ones are still in
    the inbound queue regardless of age. The whole point of the filter is
    that 'never resolved' active packets can pile up, but pending packets
    naturally clear out via ack/dismiss.
    """
    rows = [
        _packet_row(
            packet_id="rev_pkt_0500",
            to_agent="claude",
            lifecycle="pending",
            kind="plan_gap_review",
            latest_event_id="rev_evt_500",
        ),
        _packet_row(
            packet_id="rev_pkt_2400",
            to_agent="claude",
            lifecycle="pending",
            kind="plan_gap_review",
            latest_event_id="rev_evt_45500",
        ),
    ]
    pending, active = _classify_inbound_packets(
        agent_id="claude", packet_rows=rows
    )
    assert sorted(pending) == ["rev_pkt_0500", "rev_pkt_2400"]
    assert active == []


def test_classify_inbound_terminal_lifecycle_always_excluded() -> None:
    """Terminal lifecycle wins regardless of staleness filter."""
    rows = [
        _packet_row(packet_id="rev_pkt_2390", to_agent="claude",
                    lifecycle="applied", latest_event_id="rev_evt_45000"),
        _packet_row(packet_id="rev_pkt_2391", to_agent="claude",
                    lifecycle="dismissed", latest_event_id="rev_evt_45100"),
        _packet_row(packet_id="rev_pkt_2392", to_agent="claude",
                    lifecycle="in_progress", latest_event_id="rev_evt_45200"),
    ]
    pending, active = _classify_inbound_packets(
        agent_id="claude", packet_rows=rows
    )
    assert active == ["rev_pkt_2392"]
