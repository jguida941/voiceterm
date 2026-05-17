"""Regression tests for canonical active-packet predicate (rev_pkt_2396).

Per Codex rev_pkt_2412/2414: ``current_active_packet_for_agent`` MUST
prefer a freshly routed ``delivery_pending`` action_request over an
older ``in_progress`` one of the same actor. Lifecycle priority order:
``delivery_pending=4 > execution_pending/apply_pending_after_execution=3
> acknowledged/pending=2 > in_progress=1``. Same-priority ties resolve
by newest event_id rank.

Codex flagged that without these tests, the rev_pkt_2396 fix had no
typed coverage — a regression could silently flip the canonical
predicate back to the older in_progress packet without breaking any
guard.
"""

from __future__ import annotations

# Pre-load CLI so cross-package imports resolve in production order.
from dev.scripts.devctl import cli as _cli  # noqa: F401

from dev.scripts.devctl.review_channel.active_packet_authority import (
    current_active_packet_for_agent,
)


def _row(
    *,
    packet_id: str,
    to_agent: str,
    lifecycle: str,
    latest_event_id: str,
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
        "target_role": target_role,
        "target_session_id": target_session_id,
    }


def _state(packet_rows: list[dict]) -> dict:
    return {"packets": packet_rows, "agent_work_board": {}, "agent_sync": {}}


def test_delivery_pending_dominates_older_in_progress() -> None:
    """rev_pkt_2396 core invariant: a freshly routed delivery_pending packet
    outranks an older in_progress packet of the same agent."""
    rows = [
        _row(packet_id="rev_pkt_2288", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_45281"),
        _row(packet_id="rev_pkt_2394", to_agent="claude",
             lifecycle="delivery_pending", latest_event_id="rev_evt_45641"),
    ]
    assert current_active_packet_for_agent(_state(rows), "claude") == "rev_pkt_2394"


def test_delivery_pending_wins_even_when_older_than_in_progress() -> None:
    """delivery_pending priority dominates rank — a delivery_pending packet
    with an OLDER rank still wins over an in_progress one."""
    rows = [
        _row(packet_id="rev_pkt_old_delivery", to_agent="claude",
             lifecycle="delivery_pending", latest_event_id="rev_evt_1000"),
        _row(packet_id="rev_pkt_new_progress", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_1500"),
    ]
    assert current_active_packet_for_agent(_state(rows), "claude") == "rev_pkt_old_delivery"


def test_lifecycle_priority_full_ordering() -> None:
    """Cover the full priority table: delivery_pending=4 > execution_pending=3
    > acknowledged=2 > in_progress=1. Ranks kept within stale-gap window so
    the priority comparison is the discriminator, not staleness."""
    rows = [
        _row(packet_id="rev_pkt_progress", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_5000"),
        _row(packet_id="rev_pkt_acked", to_agent="claude",
             lifecycle="acknowledged", latest_event_id="rev_evt_4900"),
        _row(packet_id="rev_pkt_execpending", to_agent="claude",
             lifecycle="execution_pending", latest_event_id="rev_evt_4800"),
        _row(packet_id="rev_pkt_delivery", to_agent="claude",
             lifecycle="delivery_pending", latest_event_id="rev_evt_4700"),
    ]
    assert current_active_packet_for_agent(_state(rows), "claude") == "rev_pkt_delivery"


def test_terminal_lifecycle_excluded_regardless_of_freshness() -> None:
    """Applied/dismissed/failed/archived/expired never count as active even
    if their event-id rank is the newest. Ranks kept within stale-gap window."""
    rows = [
        _row(packet_id="rev_pkt_fresh_applied", to_agent="claude",
             lifecycle="applied", latest_event_id="rev_evt_5100"),
        _row(packet_id="rev_pkt_old_pending", to_agent="claude",
             lifecycle="delivery_pending", latest_event_id="rev_evt_5000"),
    ]
    assert current_active_packet_for_agent(_state(rows), "claude") == "rev_pkt_old_pending"


def test_stale_rank_gap_filters_historical_active() -> None:
    """Per rev_pkt_2386: historical action_requests whose latest_event_id
    is more than 1000 ranks behind the head are filtered as stale, even if
    their lifecycle is non-terminal."""
    rows = [
        _row(packet_id="rev_pkt_stale", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_171"),
        _row(packet_id="rev_pkt_recent", to_agent="claude",
             lifecycle="in_progress", latest_event_id="rev_evt_45641"),
    ]
    assert current_active_packet_for_agent(_state(rows), "claude") == "rev_pkt_recent"


def test_to_agent_filter_isolates_per_actor() -> None:
    """A delivery_pending packet to one agent must not appear as active for
    another agent."""
    rows = [
        _row(packet_id="rev_pkt_for_codex", to_agent="codex",
             lifecycle="delivery_pending", latest_event_id="rev_evt_45641"),
        _row(packet_id="rev_pkt_for_claude", to_agent="claude",
             lifecycle="acknowledged", latest_event_id="rev_evt_45000"),
    ]
    state = _state(rows)
    assert current_active_packet_for_agent(state, "claude") == "rev_pkt_for_claude"
    assert current_active_packet_for_agent(state, "codex") == "rev_pkt_for_codex"


def test_kind_filter_excludes_non_action_request_packets() -> None:
    """Findings, decisions, plan_gap_reviews are not action_requests; the
    canonical active-packet predicate must not pick them."""
    rows = [
        _row(packet_id="rev_pkt_finding", to_agent="claude",
             lifecycle="pending", latest_event_id="rev_evt_45641",
             kind="finding"),
        _row(packet_id="rev_pkt_request", to_agent="claude",
             lifecycle="acknowledged", latest_event_id="rev_evt_45000"),
    ]
    assert current_active_packet_for_agent(_state(rows), "claude") == "rev_pkt_request"


def test_empty_review_state_returns_empty_string() -> None:
    """Bare review_state with no packet rows must return empty, not raise."""
    assert current_active_packet_for_agent({}, "claude") == ""
    assert current_active_packet_for_agent({"packets": []}, "claude") == ""


def test_work_board_active_packet_takes_precedence_over_agent_sync() -> None:
    """Work-board first authority order: when work_board names an active
    packet for the actor, the predicate uses that, not packet_rows."""
    state = {
        "packets": [
            _row(packet_id="rev_pkt_packets", to_agent="claude",
                 lifecycle="delivery_pending",
                 latest_event_id="rev_evt_99999"),
        ],
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "active_packet_id": "rev_pkt_workboard",
                    "source_event_id": "rev_evt_50000",
                },
            ],
        },
    }
    assert current_active_packet_for_agent(state, "claude") == "rev_pkt_workboard"


def test_target_role_and_session_scope_disambiguates_same_agent_packets() -> None:
    """Targeted packets require a matching role/session-scoped reader."""
    rows = [
        _row(
            packet_id="rev_pkt_coder",
            to_agent="claude",
            lifecycle="delivery_pending",
            latest_event_id="rev_evt_5000",
            target_role="coder",
            target_session_id="session-coder",
        ),
        _row(
            packet_id="rev_pkt_dashboard",
            to_agent="claude",
            lifecycle="delivery_pending",
            latest_event_id="rev_evt_5001",
            target_role="dashboard",
            target_session_id="session-dashboard",
        ),
    ]
    state = _state(rows)
    assert current_active_packet_for_agent(state, "claude") == ""
    assert (
        current_active_packet_for_agent(
            state,
            "claude",
            target_role="implementer",
            target_session_id="session-coder",
        )
        == "rev_pkt_coder"
    )
    assert (
        current_active_packet_for_agent(
            state,
            "claude",
            target_role="dashboard",
            target_session_id="session-dashboard",
        )
        == "rev_pkt_dashboard"
    )
    assert (
        current_active_packet_for_agent(
            state,
            "claude",
            target_role="dashboard",
            target_session_id="session-coder",
        )
        == ""
    )


def test_work_board_scope_uses_role_and_session_before_legacy_precedence() -> None:
    """Work-board rows must not collapse coder-Claude and dashboard-Claude."""
    state = {
        "packets": [
            _row(
                packet_id="rev_pkt_coder",
                to_agent="claude",
                lifecycle="delivery_pending",
                latest_event_id="rev_evt_5000",
                target_role="coder",
                target_session_id="session-coder",
            ),
            _row(
                packet_id="rev_pkt_dashboard",
                to_agent="claude",
                lifecycle="delivery_pending",
                latest_event_id="rev_evt_5001",
                target_role="dashboard",
                target_session_id="session-dashboard",
            ),
        ],
        "agent_work_board": {
            "rows": [
                {
                    "actor_id": "claude",
                    "role": "implementer",
                    "session_id": "session-coder",
                    "active_packet_id": "rev_pkt_coder",
                    "source_event_id": "rev_evt_5000",
                },
                {
                    "actor_id": "claude",
                    "role": "dashboard",
                    "session_id": "session-dashboard",
                    "active_packet_id": "rev_pkt_dashboard",
                    "source_event_id": "rev_evt_5001",
                },
            ],
        },
        "agent_sync": {},
    }
    assert current_active_packet_for_agent(state, "claude") == ""
    assert (
        current_active_packet_for_agent(
            state,
            "claude",
            target_role="coder",
            target_session_id="session-coder",
        )
        == "rev_pkt_coder"
    )
    assert (
        current_active_packet_for_agent(
            state,
            "claude",
            target_role="dashboard",
            target_session_id="session-dashboard",
        )
        == "rev_pkt_dashboard"
    )
