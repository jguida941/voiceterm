"""Regressions for direct packet history lookup."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dev.scripts.devctl.commands.review_channel_command.constants import (
    ReviewChannelAction,
)
from dev.scripts.devctl.commands.review_channel_command.helpers import _validate_args
from dev.scripts.devctl.review_channel.event_reducer_inbox import (
    filter_history_events,
    filter_history_packets,
)


def test_history_packet_id_finds_live_pending_packet_body() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_100",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "summary": "Exact packet",
                "body": "The exact packet body must be readable.",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
            {
                "packet_id": "rev_pkt_101",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "summary": "Other packet",
                "body": "Wrong body",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
        ]
    }

    packets = filter_history_packets(review_state, packet_id="rev_pkt_100")

    assert [packet["packet_id"] for packet in packets] == ["rev_pkt_100"]
    assert packets[0]["body"] == "The exact packet body must be readable."


def test_history_events_filter_by_packet_id() -> None:
    events = [
        {"event_id": "rev_evt_1", "packet_id": "rev_pkt_100"},
        {"event_id": "rev_evt_2", "packet_id": "rev_pkt_101"},
        {"event_id": "rev_evt_3", "packet_id": "rev_pkt_100"},
    ]

    filtered = filter_history_events(events, packet_id="rev_pkt_100")

    assert [event["event_id"] for event in filtered] == ["rev_evt_1", "rev_evt_3"]


def _show_args(**overrides: object) -> SimpleNamespace:
    args = {
        "action": "show",
        "await_ack_seconds": 0,
        "expires_in_minutes": 30,
        "follow": False,
        "follow_interval_seconds": 120,
        "format": "md",
        "limit": 20,
        "max_follow_snapshots": 0,
        "packet_id": "rev_pkt_100",
        "rollover_threshold_pct": 50,
        "stale_minutes": 30,
        "start_publisher_if_missing": False,
        "stop_grace_seconds": 0.0,
        "to_agent": None,
    }
    args.update(overrides)
    return SimpleNamespace(**args)


def test_show_validation_requires_packet_id() -> None:
    with pytest.raises(ValueError, match="--packet-id is required"):
        _validate_args(_show_args(packet_id=None), ReviewChannelAction.SHOW)


def test_show_validation_still_rejects_post_only_to_agent() -> None:
    with pytest.raises(ValueError, match="--to-agent is only valid"):
        _validate_args(_show_args(to_agent="codex"), ReviewChannelAction.SHOW)
