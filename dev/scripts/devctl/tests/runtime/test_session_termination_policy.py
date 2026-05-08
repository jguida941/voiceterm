"""Tests for typed task-complete continuation policy."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dev.scripts.devctl.review_channel.packet_contract import (
    VALID_PACKET_KINDS,
)
from dev.scripts.devctl.runtime.review_packet_inbox_actionable import is_actionable
from dev.scripts.devctl.runtime.session_termination_policy import (
    CONTINUATION_ANCHOR_PACKET_KIND,
    SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE,
    SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
    STOP_ANCHOR_PACKET_KIND,
    SessionTerminationPolicy,
    task_complete_decision,
)


def _stamp(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) + delta).isoformat()


def _anchor(**overrides: object) -> dict[str, object]:
    packet = {
        "packet_id": "rev_pkt_anchor",
        "kind": CONTINUATION_ANCHOR_PACKET_KIND,
        "status": "pending",
        "lifecycle_current_state": "pending",
        "to_agent": "codex",
        "target_session_id": "session-1",
        "posted_at": "2026-05-08T12:00:00+00:00",
        "latest_event_id": "rev_evt_1",
        "expires_at_utc": _stamp(timedelta(minutes=30)),
    }
    packet.update(overrides)
    return packet


def test_anchor_packet_kinds_are_valid_but_not_actionable() -> None:
    assert CONTINUATION_ANCHOR_PACKET_KIND in VALID_PACKET_KINDS
    assert STOP_ANCHOR_PACKET_KIND in VALID_PACKET_KINDS
    assert is_actionable(_anchor()) is False
    assert is_actionable({"kind": STOP_ANCHOR_PACKET_KIND, "status": "pending"}) is False


def test_default_policy_terminates_task_complete() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(_anchor(),),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )
    assert decision.terminate is True
    assert decision.reason == "policy_default"
    assert decision.policy_mode == SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE
    assert decision.next_command == ""


def test_keep_awake_policy_continues_with_active_anchor() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(_anchor(),),
        policy=SessionTerminationPolicy(
            mode=SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
            target_session_id="session-1",
        ),
        actor="codex",
    )
    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"
    assert decision.anchor_packet_id == "rev_pkt_anchor"
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py develop next --actor codex --format md"
    )


def test_keep_awake_policy_ignores_expired_anchor() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(_anchor(expires_at_utc=_stamp(timedelta(minutes=-1))),),
        policy=SessionTerminationPolicy(
            mode=SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
            target_session_id="session-1",
        ),
        actor="codex",
    )
    assert decision.terminate is True
    assert decision.reason == "no_active_anchor"


def test_stop_anchor_terminates_even_when_continuation_anchor_exists() -> None:
    stop_anchor = {
        "packet_id": "rev_pkt_stop",
        "kind": STOP_ANCHOR_PACKET_KIND,
        "status": "pending",
        "lifecycle_current_state": "pending",
        "target_session_id": "session-1",
        "posted_at": "2026-05-08T12:01:00+00:00",
        "expires_at_utc": _stamp(timedelta(minutes=30)),
    }
    decision = task_complete_decision(
        session_id="session-1",
        packets=(_anchor(), stop_anchor),
        policy=SessionTerminationPolicy(
            mode=SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
            target_session_id="session-1",
        ),
        actor="codex",
    )
    assert decision.terminate is True
    assert decision.reason == "operator_stop_anchor"
