"""Regression tests for typed attention-vs-execution split (rev_pkt_2414/2420).

Codex required the split: ``attention_packet_id`` is the highest-priority
live work for an actor (where claude-loop should point operator
attention), while ``executing_packet_id`` is what the actor has its
hands on right now. They can diverge: a new ``delivery_pending`` packet
arrives while the actor is still executing an older ``in_progress`` —
attention flips, executing stays. The legacy ``active_packet_id`` and
``active_action_requests_to_me`` are kept as deprecated aliases for one
release cycle so legacy consumers don't break.
"""

from __future__ import annotations

# Pre-load CLI to avoid the pre-existing circular import at test-time.
from dev.scripts.devctl import cli as _cli  # noqa: F401

from dev.scripts.devctl.review_channel.agent_sync_projection import (
    _classify_active_split,
    _select_attention_packet,
)
from dev.scripts.devctl.review_channel.agent_work_board_projection import (
    _select_executing_packet_id,
    _select_current_active_packet_id,
)


def _row(
    *,
    packet_id: str,
    to_agent: str,
    lifecycle: str,
    latest_event_id: str,
    execution_started_by: str = "",
    kind: str = "action_request",
    target_role: str = "",
    target_session_id: str = "",
) -> dict:
    return {
        "packet_id": packet_id,
        "to_agent": to_agent,
        "kind": kind,
        "lifecycle_current_state": lifecycle,
        "latest_event_id": latest_event_id,
        "execution_started_by": execution_started_by,
        "target_role": target_role,
        "target_session_id": target_session_id,
    }


def test_attention_picks_delivery_pending_when_executing_an_older_packet() -> None:
    """The split's headline scenario: a new delivery_pending arrives while
    the actor is still mid-execution on an older in_progress. Attention
    must flip; executing must NOT."""
    rows = [
        _row(packet_id="rev_pkt_old_progress", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_5000",
             execution_started_by="claude"),
        _row(packet_id="rev_pkt_new_delivery", to_agent="claude",
             lifecycle="delivery_pending", latest_event_id="rev_evt_5500"),
    ]
    assert _select_attention_packet(agent_id="claude", packet_rows=rows) == "rev_pkt_new_delivery"
    assert _select_executing_packet_id(actor_id="claude", packet_rows=rows) == "rev_pkt_old_progress"


def test_attention_and_executing_agree_when_only_one_active_packet() -> None:
    """When the actor is executing the highest-priority packet, both fields
    point at the same packet — the common case."""
    rows = [
        _row(packet_id="rev_pkt_solo", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_5000",
             execution_started_by="claude"),
    ]
    assert _select_attention_packet(agent_id="claude", packet_rows=rows) == "rev_pkt_solo"
    assert _select_executing_packet_id(actor_id="claude", packet_rows=rows) == "rev_pkt_solo"


def test_executing_requires_execution_started_by_match() -> None:
    """A packet with lifecycle=in_progress but no execution_started_by is
    acked-but-not-acted; it belongs to attention only, not executing."""
    rows = [
        _row(packet_id="rev_pkt_acked_only", to_agent="claude",
             lifecycle="acknowledged", latest_event_id="rev_evt_5000",
             execution_started_by=""),
        _row(packet_id="rev_pkt_no_started_by", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_4900",
             execution_started_by=""),
    ]
    # Attention picks acknowledged (priority 2) over in_progress (1).
    assert _select_attention_packet(agent_id="claude", packet_rows=rows) == "rev_pkt_acked_only"
    # Executing rejects both: started_by is empty.
    assert _select_executing_packet_id(actor_id="claude", packet_rows=rows) == ""


def test_executing_rejects_packet_started_by_other_actor() -> None:
    """If execution_started_by names another actor, the row does NOT
    appear in this actor's executing_packet_id."""
    rows = [
        _row(packet_id="rev_pkt_codex_executing", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_5000",
             execution_started_by="codex"),
    ]
    assert _select_executing_packet_id(actor_id="claude", packet_rows=rows) == ""


def test_classify_active_split_separates_delivery_and_executing() -> None:
    """The agent_sync row exposes both lists; their union is the legacy
    ``active_action_requests_to_me`` (for one cycle)."""
    rows = [
        _row(packet_id="rev_pkt_d1", to_agent="claude",
             lifecycle="delivery_pending", latest_event_id="rev_evt_5000"),
        _row(packet_id="rev_pkt_d2", to_agent="claude",
             lifecycle="delivery_pending", latest_event_id="rev_evt_4990"),
        _row(packet_id="rev_pkt_e1", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_4980",
             execution_started_by="claude"),
        _row(packet_id="rev_pkt_e2", to_agent="claude",
             lifecycle="execution_pending", latest_event_id="rev_evt_4970",
             execution_started_by="claude"),
        _row(packet_id="rev_pkt_acked", to_agent="claude",
             lifecycle="acknowledged", latest_event_id="rev_evt_4960"),
    ]
    delivery_pending, executing = _classify_active_split(
        agent_id="claude", packet_rows=rows
    )
    assert sorted(delivery_pending) == ["rev_pkt_d1", "rev_pkt_d2"]
    assert sorted(executing) == ["rev_pkt_e1", "rev_pkt_e2"]
    # acknowledged shows up in legacy active_action_requests_to_me but not
    # in either typed split list — it's neither pending delivery nor
    # currently executing.


def test_attention_and_executing_both_empty_when_no_active_work() -> None:
    """Empty packet_rows or only terminal-lifecycle rows produce empty
    selections for both attention and executing."""
    rows = [
        _row(packet_id="rev_pkt_done", to_agent="claude",
             lifecycle="applied", latest_event_id="rev_evt_5000",
             execution_started_by="claude"),
    ]
    assert _select_attention_packet(agent_id="claude", packet_rows=rows) == ""
    assert _select_executing_packet_id(actor_id="claude", packet_rows=rows) == ""


def test_legacy_active_packet_id_aliases_attention_in_work_board() -> None:
    """Per Codex rev_pkt_2420: ``active_packet_id`` is kept for one release
    cycle as a deprecated alias of ``attention_packet_id``. The work-board
    selector still returns the same value as the attention selector."""
    rows = [
        _row(packet_id="rev_pkt_attention", to_agent="claude",
             lifecycle="delivery_pending", latest_event_id="rev_evt_5000"),
    ]
    assert _select_current_active_packet_id(actor_id="claude", packet_rows=rows) == "rev_pkt_attention"
    # Same selection as attention.
    assert _select_attention_packet(agent_id="claude", packet_rows=rows) == "rev_pkt_attention"


def test_scoped_packets_do_not_enter_ambiguous_agent_sync_attention() -> None:
    """Agent-level sync rows cannot prove which Claude session is reading."""
    rows = [
        _row(
            packet_id="rev_pkt_coder_only",
            to_agent="claude",
            lifecycle="delivery_pending",
            latest_event_id="rev_evt_5000",
            target_role="coder",
            target_session_id="session-coder",
        ),
    ]
    assert _select_attention_packet(agent_id="claude", packet_rows=rows) == ""


def test_work_board_attention_accepts_matching_scoped_session() -> None:
    """Per-session work-board rows may consume packets scoped to that session."""
    rows = [
        _row(
            packet_id="rev_pkt_coder_only",
            to_agent="claude",
            lifecycle="in_progress",
            latest_event_id="rev_evt_5000",
            execution_started_by="claude",
            target_role="coder",
            target_session_id="session-coder",
        ),
    ]
    assert (
        _select_current_active_packet_id(
            actor_id="claude",
            packet_rows=rows,
            target_role="implementer",
            target_session_id="session-coder",
        )
        == "rev_pkt_coder_only"
    )
    assert (
        _select_executing_packet_id(
            actor_id="claude",
            packet_rows=rows,
            target_role="implementer",
            target_session_id="session-coder",
        )
        == "rev_pkt_coder_only"
    )
    assert (
        _select_current_active_packet_id(
            actor_id="claude",
            packet_rows=rows,
            target_role="dashboard",
            target_session_id="session-coder",
        )
        == ""
    )
