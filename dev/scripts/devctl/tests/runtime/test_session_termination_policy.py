"""Tests for typed task-complete continuation policy."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dev.scripts.devctl.review_channel.packet_contract import (
    VALID_PACKET_KINDS,
)
from dev.scripts.devctl.runtime.review_packet_inbox_actionable import is_actionable
from dev.scripts.devctl.runtime.session_termination_policy import (
    CONTINUATION_ANCHOR_MISSING_ERROR,
    CONTINUATION_ANCHOR_PACKET_KIND,
    PACKET_ATTENTION_PENDING_ERROR,
    PENDING_REVIEW_PACKET_ERROR,
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


def test_default_policy_blocks_task_complete_when_review_packet_is_pending() -> None:
    review_packet = _anchor(
        packet_id="rev_pkt_review",
        kind="review_started",
        lifecycle_current_state="review_in_progress",
        to_agent="codex",
        target_session_id="session-1",
    )

    decision = task_complete_decision(
        session_id="session-1",
        packets=(review_packet,),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )

    assert decision.terminate is False
    assert decision.reason == PENDING_REVIEW_PACKET_ERROR
    assert decision.error_kind == PENDING_REVIEW_PACKET_ERROR
    assert decision.blocking_packet_id == "rev_pkt_review"
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py develop next --actor codex --format md"
    )


def test_default_policy_blocks_task_complete_when_packet_attention_is_pending() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(),
        policy=SessionTerminationPolicy(),
        actor="codex",
        packet_attention={
            "observation_actor_id": "codex",
            "observation_session_id": "session-1",
            "latest_attention_packet_id": "rev_pkt_wake",
            "pending_packet_count": 1,
            "wake_required": True,
            "pivot_required": True,
        },
    )

    assert decision.terminate is False
    assert decision.reason == PACKET_ATTENTION_PENDING_ERROR
    assert decision.error_kind == PACKET_ATTENTION_PENDING_ERROR
    assert decision.blocking_packet_id == "rev_pkt_wake"
    assert decision.pending_packet_count == 1
    assert decision.wake_required is True
    assert decision.pivot_required is True
    assert decision.next_command == (
        "python3 dev/scripts/devctl.py develop next --actor codex --format md"
    )


def test_stop_anchor_overrides_pending_packet_attention() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(
            _anchor(
                packet_id="rev_pkt_stop",
                kind=STOP_ANCHOR_PACKET_KIND,
                lifecycle_current_state="pending",
                to_agent="codex",
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        packet_attention={
            "observation_actor_id": "codex",
            "observation_session_id": "session-1",
            "latest_attention_packet_id": "rev_pkt_wake",
            "pending_packet_count": 1,
            "wake_required": True,
            "pivot_required": True,
        },
    )

    assert decision.terminate is True
    assert decision.reason == "operator_stop_anchor"
    assert decision.error_kind == ""
    assert decision.blocking_packet_id == ""


def test_pending_review_packet_respects_route_role() -> None:
    review_packet = _anchor(
        packet_id="rev_pkt_review",
        kind="review_started",
        lifecycle_current_state="review_in_progress",
        to_agent="codex",
        target_role="implementer",
        target_session_id="session-1",
    )

    decision = task_complete_decision(
        session_id="session-1",
        packets=(review_packet,),
        policy=SessionTerminationPolicy(),
        actor="codex",
        actor_role="reviewer",
    )

    assert decision.terminate is True
    assert decision.reason == "policy_default"
    assert decision.error_kind == ""
    assert decision.blocking_packet_id == ""


def test_pending_instruction_blocks_task_complete() -> None:
    instruction_packet = _anchor(
        packet_id="rev_pkt_instruction",
        kind="instruction",
        lifecycle_current_state="pending",
        to_agent="codex",
        target_role="reviewer",
        target_session_id="session-1",
    )

    decision = task_complete_decision(
        session_id="session-1",
        packets=(instruction_packet,),
        policy=SessionTerminationPolicy(),
        actor="codex",
        actor_role="reviewer",
    )

    assert decision.terminate is False
    assert decision.reason == PENDING_REVIEW_PACKET_ERROR
    assert decision.error_kind == PENDING_REVIEW_PACKET_ERROR
    assert decision.blocking_packet_id == "rev_pkt_instruction"


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


def test_keep_awake_policy_ignores_other_actor_anchor() -> None:
    decision = task_complete_decision(
        session_id="shared-session",
        packets=(
            _anchor(
                to_agent="claude",
                target_role="implementer",
                target_session_id="shared-session",
            ),
        ),
        policy=SessionTerminationPolicy(
            mode=SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
            target_session_id="shared-session",
        ),
        actor="codex",
        actor_role="reviewer",
    )
    assert decision.terminate is False
    assert decision.reason == CONTINUATION_ANCHOR_MISSING_ERROR
    assert decision.error_kind == CONTINUATION_ANCHOR_MISSING_ERROR
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
    assert decision.terminate is False
    assert decision.reason == CONTINUATION_ANCHOR_MISSING_ERROR
    assert decision.error_kind == CONTINUATION_ANCHOR_MISSING_ERROR


def test_continuation_command_fails_closed_without_actor_or_anchor_route() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(),
        policy=SessionTerminationPolicy(
            mode=SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
            target_session_id="session-1",
        ),
    )
    assert decision.terminate is False
    assert decision.error_kind == CONTINUATION_ANCHOR_MISSING_ERROR
    assert decision.next_command == ""


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
