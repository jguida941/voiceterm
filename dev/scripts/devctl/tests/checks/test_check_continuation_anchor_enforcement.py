"""Tests for ``check_continuation_anchor_enforcement`` (G27)."""

from __future__ import annotations

from datetime import datetime, timezone

from dev.scripts.checks import check_continuation_anchor_enforcement as guard


CURRENT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
OTHER_ROW_ID = "MP-OTHER-ROW"
NOW = datetime(2026, 5, 22, 22, 0, 0, tzinfo=timezone.utc)


def _anchor(
    *,
    packet_id: str,
    target_role: str = "reviewer",
    target_session_id: str = "session-codex-A",
    target_ref: str = f"plan:{CURRENT_ROW_ID}",
    plan_id: str = CURRENT_ROW_ID,
    scope: str = "",
    expires_at_utc: str = "",
    posted_at: str = "2026-05-22T20:00:00Z",
    kind: str = guard.ANCHOR_KIND_CONTINUATION,
    **extra: object,
) -> dict[str, object]:
    packet: dict[str, object] = {
        "packet_id": packet_id,
        "kind": kind,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "target_ref": target_ref,
        "plan_id": plan_id,
        "posted_at": posted_at,
        "status": "pending",
    }
    if scope:
        packet["scope"] = scope
    if expires_at_utc:
        packet["expires_at_utc"] = expires_at_utc
    packet.update(extra)
    return packet


def _stop_anchor(
    *,
    packet_id: str,
    releases_anchor_packet_id: str,
    plan_id: str = CURRENT_ROW_ID,
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": guard.ANCHOR_KIND_STOP,
        "releases_anchor_packet_id": releases_anchor_packet_id,
        "target_ref": f"plan:{plan_id}",
        "plan_id": plan_id,
    }


def _pending_packet(
    *,
    packet_id: str,
    target_role: str = "implementer",
    target_session_id: str = "session-claude-A",
    target_ref: str = f"plan:{CURRENT_ROW_ID}",
    plan_id: str = CURRENT_ROW_ID,
    kind: str = "finding",
    body_observed_at_utc: str = "",
    posted_at: str = "2026-05-22T20:30:00Z",
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": kind,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "target_ref": target_ref,
        "plan_id": plan_id,
        "status": "pending",
        "posted_at": posted_at,
        "body_observed_at_utc": body_observed_at_utc,
    }


def _reviewer_terminal_event(
    *,
    event_id: str,
    timestamp_utc: str = "2026-05-22T21:00:00Z",
    reviewer_state: str = "final_completion",
    event_type: str = "reviewer_final_completion",
    role: str = "reviewer",
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp_utc": timestamp_utc,
        "reviewer_state": reviewer_state,
        "role": role,
    }


def _peer_steady_state_event(
    *,
    event_id: str,
    peer_role: str = "implementer",
    timestamp_utc: str = "2026-05-22T21:00:00Z",
    event_type: str = "peer_steady_state",
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp_utc": timestamp_utc,
        "peer_role": peer_role,
    }


def _liveness_expired_event(
    *,
    event_id: str,
    session_name: str = "session-claude-A",
    role: str = "implementer",
    provider: str = "claude_code",
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "event_type": "participant_liveness_expired",
        "timestamp_utc": "2026-05-22T21:00:00Z",
        "session_name": session_name,
        "role": role,
        "provider": provider,
    }


def _lane_wake_event(
    *,
    event_id: str,
    session_name: str = "",
    role: str = "",
    event_type: str = "lane_wake",
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp_utc": "2026-05-22T21:01:00Z",
        "session_name": session_name,
        "role": role,
    }


# ---------------------------------------------------------------------------
# Rule 1 / 2: final completion or idle/ended while anchor is live.
# ---------------------------------------------------------------------------


def test_final_completion_with_live_anchor_fails():
    packets = [_anchor(packet_id="rev_pkt_anchor_1")]
    events = [_reviewer_terminal_event(event_id="rev_evt_final_1")]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_FINAL_COMPLETION_WITH_LIVE_ANCHOR in rules
    assert any(
        v["anchor_packet_id"] == "rev_pkt_anchor_1"
        for v in report["violations"]
    )
    assert report["live_anchor_count"] == 1


def test_reviewer_idle_with_live_anchor_fails():
    packets = [_anchor(packet_id="rev_pkt_anchor_2")]
    events = [
        _reviewer_terminal_event(
            event_id="rev_evt_idle_2",
            reviewer_state="idle",
            event_type="reviewer_idle",
        )
    ]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_REVIEWER_IDLE_WITH_LIVE_ANCHOR in rules


def test_stop_anchor_releases_live_anchor_passes():
    packets = [
        _anchor(packet_id="rev_pkt_anchor_3"),
        _stop_anchor(
            packet_id="rev_pkt_stop_3",
            releases_anchor_packet_id="rev_pkt_anchor_3",
        ),
    ]
    events = [_reviewer_terminal_event(event_id="rev_evt_final_3")]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_anchor_converted_to_typed_blocker_passes():
    packets = [
        _anchor(packet_id="rev_pkt_anchor_4"),
        {
            "packet_id": "rev_pkt_blocker_4",
            "kind": "task_blocked",
            "blocker_for_anchor_packet_id": "rev_pkt_anchor_4",
            "target_ref": f"plan:{CURRENT_ROW_ID}",
            "plan_id": CURRENT_ROW_ID,
            "reason": "current-row blocker for anchor",
        },
    ]
    events = [_reviewer_terminal_event(event_id="rev_evt_final_4")]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_no_terminal_event_with_live_anchor_passes():
    packets = [_anchor(packet_id="rev_pkt_anchor_5")]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["live_anchor_count"] == 1


# ---------------------------------------------------------------------------
# Rule 3: session-scoped anchor with stale session.
# ---------------------------------------------------------------------------


def test_session_scoped_anchor_stale_session_fails():
    packets = [
        _anchor(
            packet_id="rev_pkt_anchor_stale",
            target_session_id="session-codex-DEAD",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-LIVE",),
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SESSION_SCOPED_ANCHOR_STALE_SESSION in rules


def test_session_scoped_anchor_live_session_passes():
    packets = [
        _anchor(
            packet_id="rev_pkt_anchor_live",
            target_session_id="session-codex-LIVE",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-LIVE",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_plan_scoped_anchor_survives_session_replacement_passes():
    packets = [
        _anchor(
            packet_id="rev_pkt_anchor_plan",
            target_session_id="session-codex-DEAD",
            scope="plan",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-LIVE",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_refresh_anchor_to_live_session_passes():
    packets = [
        _anchor(
            packet_id="rev_pkt_anchor_dead",
            target_session_id="session-codex-DEAD",
        ),
        _anchor(
            packet_id="rev_pkt_anchor_refresh",
            target_session_id="session-codex-LIVE",
            refresh_of_packet_id="rev_pkt_anchor_dead",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-LIVE",),
        now=NOW,
    )
    # The refresh anchor itself is also session-scoped against the live
    # session, which is fine; the dead-session anchor must be considered
    # refreshed and not violate the stale-session rule.
    assert all(
        v["rule_id"] != guard.RULE_SESSION_SCOPED_ANCHOR_STALE_SESSION
        for v in report["violations"]
    )


# ---------------------------------------------------------------------------
# Rule 4: startup authority degraded while anchor pending.
# ---------------------------------------------------------------------------


def test_startup_authority_tools_only_with_anchor_fails():
    packets = [_anchor(packet_id="rev_pkt_anchor_degraded")]
    startup_authority = {
        "reviewer_mode": "tools_only",
        "observed_control_topology": "no_live_agents",
        "safe_to_continue": False,
    }
    report = guard.build_report(
        packets=packets,
        events=(),
        startup_authority=startup_authority,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_STARTUP_AUTHORITY_NOT_ENFORCED in rules
    assert sorted(report["startup_authority_degraded_reasons"]) == [
        "observed_control_topology=no_live_agents",
        "reviewer_mode=tools_only",
        "safe_to_continue=false",
    ]


def test_startup_authority_healthy_with_anchor_passes():
    packets = [_anchor(packet_id="rev_pkt_anchor_healthy")]
    startup_authority = {
        "reviewer_mode": "dual_agent",
        "observed_control_topology": "dual_agent",
        "safe_to_continue": True,
    }
    report = guard.build_report(
        packets=packets,
        events=(),
        startup_authority=startup_authority,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["startup_authority_degraded_reasons"] == []


def test_startup_authority_degraded_with_blocker_passes():
    packets = [
        _anchor(packet_id="rev_pkt_anchor_blocked"),
        {
            "packet_id": "rev_pkt_blocker_for_degraded",
            "kind": "task_blocked",
            "blocker_for_anchor_packet_id": "rev_pkt_anchor_blocked",
            "target_ref": f"plan:{CURRENT_ROW_ID}",
            "plan_id": CURRENT_ROW_ID,
            "reason": guard.RULE_STARTUP_AUTHORITY_NOT_ENFORCED,
        },
    ]
    startup_authority = {
        "reviewer_mode": "tools_only",
        "safe_to_continue": False,
    }
    report = guard.build_report(
        packets=packets,
        events=(),
        startup_authority=startup_authority,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


# ---------------------------------------------------------------------------
# Rule 5: peer steady-state while peer inbox has current-row pending packet.
# ---------------------------------------------------------------------------


def test_peer_steady_state_with_pending_packet_fails():
    packets = [
        _pending_packet(
            packet_id="rev_pkt_4821",
            target_role="implementer",
            target_session_id="session-claude-A",
        ),
    ]
    events = [
        _peer_steady_state_event(
            event_id="rev_evt_steady_1",
            peer_role="implementer",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_PEER_STEADY_STATE_WITH_PENDING_PACKET in rules
    matching = [
        v for v in report["violations"]
        if v["rule_id"] == guard.RULE_PEER_STEADY_STATE_WITH_PENDING_PACKET
    ]
    assert any(v["anchor_packet_id"] == "rev_pkt_4821" for v in matching)


def test_peer_steady_state_with_routed_lifecycle_passes():
    packets = [
        _pending_packet(
            packet_id="rev_pkt_4825",
            target_role="implementer",
        ),
    ]
    events = [
        {
            "event_id": "rev_evt_steady_routed",
            "event_type": "peer_steady_state",
            "timestamp_utc": "2026-05-22T21:00:00Z",
            "peer_role": "implementer",
            "steady_state_blocked_by_pending_packet": True,
            "routed_lifecycle_transition": "peer_steady_state_with_pending_current_row_packet",
        },
    ]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert all(
        v["rule_id"] != guard.RULE_PEER_STEADY_STATE_WITH_PENDING_PACKET
        for v in report["violations"]
    )


def test_peer_steady_state_no_pending_packet_passes():
    packets = [
        _pending_packet(
            packet_id="rev_pkt_observed",
            target_role="implementer",
            body_observed_at_utc="2026-05-22T20:45:00Z",
        ),
    ]
    events = [
        _peer_steady_state_event(
            event_id="rev_evt_steady_clean",
            peer_role="implementer",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["pending_peer_packet_count"] == 0


# ---------------------------------------------------------------------------
# Rule 6: trace-only liveness expiry.
# ---------------------------------------------------------------------------


def test_liveness_expired_with_no_wake_or_blocker_fails():
    events = [
        _liveness_expired_event(
            event_id="rev_evt_liveness_alone",
            session_name="session-codex-DEAD",
            role="reviewer",
        ),
    ]
    report = guard.build_report(
        packets=(),
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-LIVE",),
        now=NOW,
    )
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_TRACE_ONLY_LIVENESS_EXPIRY in rules
    assert report["liveness_expired_event_count"] == 1


def test_liveness_expired_with_lane_wake_passes():
    events = [
        _liveness_expired_event(
            event_id="rev_evt_liveness_woken",
            session_name="session-codex-DEAD",
            role="reviewer",
        ),
        _lane_wake_event(
            event_id="rev_evt_wake",
            session_name="session-codex-DEAD",
            role="reviewer",
        ),
    ]
    report = guard.build_report(
        packets=(),
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-LIVE",),
        now=NOW,
    )
    assert all(
        v["rule_id"] != guard.RULE_TRACE_ONLY_LIVENESS_EXPIRY
        for v in report["violations"]
    )


def test_liveness_expired_with_current_row_blocker_passes():
    packets = [
        {
            "packet_id": "rev_pkt_blocker_liveness",
            "kind": "task_blocked",
            "target_ref": f"plan:{CURRENT_ROW_ID}",
            "plan_id": CURRENT_ROW_ID,
            "triggering_event_id": "rev_evt_liveness_routed",
            "reason": "session expired; routed to current-row blocker",
        },
    ]
    events = [
        _liveness_expired_event(
            event_id="rev_evt_liveness_routed",
            session_name="session-codex-DEAD",
            role="reviewer",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-LIVE",),
        now=NOW,
    )
    assert all(
        v["rule_id"] != guard.RULE_TRACE_ONLY_LIVENESS_EXPIRY
        for v in report["violations"]
    )


# ---------------------------------------------------------------------------
# Anchor expiry / row-scope.
# ---------------------------------------------------------------------------


def test_expired_anchor_is_not_live():
    packets = [
        _anchor(
            packet_id="rev_pkt_anchor_expired",
            expires_at_utc="2026-05-22T21:00:00Z",
        ),
    ]
    events = [_reviewer_terminal_event(event_id="rev_evt_final_exp")]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["live_anchor_count"] == 0
    assert report["ok"] is True


def test_anchor_for_other_row_does_not_block_current_row_completion():
    packets = [
        _anchor(
            packet_id="rev_pkt_anchor_other_row",
            target_ref=f"plan:{OTHER_ROW_ID}",
            plan_id=OTHER_ROW_ID,
        ),
    ]
    events = [_reviewer_terminal_event(event_id="rev_evt_final_other")]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is True
    assert report["live_anchor_count"] == 0


def test_consumed_anchor_does_not_block_completion():
    packets = [
        _anchor(
            packet_id="rev_pkt_anchor_consumed",
            absorbed_at_utc="2026-05-22T20:30:00Z",
            disposition_state="absorbed",
        ),
    ]
    events = [_reviewer_terminal_event(event_id="rev_evt_final_consumed")]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    assert report["ok"] is True


# ---------------------------------------------------------------------------
# Markdown render covers violations and warnings paths.
# ---------------------------------------------------------------------------


def test_render_markdown_includes_violation_rows():
    packets = [_anchor(packet_id="rev_pkt_anchor_md")]
    events = [_reviewer_terminal_event(event_id="rev_evt_final_md")]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-A",),
        now=NOW,
    )
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert "rev_pkt_anchor_md" in md
    assert guard.RULE_FINAL_COMPLETION_WITH_LIVE_ANCHOR in md


# ---------------------------------------------------------------------------
# Multi-condition / dogfood proof of the spec's example surface.
# ---------------------------------------------------------------------------


def test_dogfood_rev_pkt_4821_full_scenario_fails_with_all_rules():
    """Mirrors the spec scenario: current-row anchor live, reviewer emits
    final completion, startup authority degraded, peer steady-state with
    pending `rev_pkt_4821`, and a trace-only liveness expiry."""

    packets = [
        _anchor(
            packet_id="rev_pkt_4803",
            target_role="reviewer",
            target_session_id="session-codex-DEAD",
        ),
        _pending_packet(
            packet_id="rev_pkt_4821",
            target_role="implementer",
            target_session_id="session-claude-A",
        ),
    ]
    events = [
        _reviewer_terminal_event(event_id="rev_evt_final_4821"),
        _peer_steady_state_event(
            event_id="rev_evt_steady_4821", peer_role="implementer"
        ),
        _liveness_expired_event(
            event_id="rev_evt_liveness_4821",
            session_name="session-codex-DEAD",
            role="reviewer",
        ),
    ]
    startup_authority = {
        "reviewer_mode": "tools_only",
        "observed_control_topology": "no_live_agents",
        "safe_to_continue": False,
    }
    report = guard.build_report(
        packets=packets,
        events=events,
        startup_authority=startup_authority,
        current_row_id=CURRENT_ROW_ID,
        live_reviewer_session_ids=("session-codex-LIVE",),
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    # Every rule lights up:
    assert guard.RULE_FINAL_COMPLETION_WITH_LIVE_ANCHOR in rules
    assert guard.RULE_SESSION_SCOPED_ANCHOR_STALE_SESSION in rules
    assert guard.RULE_STARTUP_AUTHORITY_NOT_ENFORCED in rules
    assert guard.RULE_PEER_STEADY_STATE_WITH_PENDING_PACKET in rules
    assert guard.RULE_TRACE_ONLY_LIVENESS_EXPIRY in rules
    # Dogfood proof fields are present on at least one violation each.
    peer_violation = next(
        v for v in report["violations"]
        if v["rule_id"] == guard.RULE_PEER_STEADY_STATE_WITH_PENDING_PACKET
    )
    assert peer_violation["anchor_packet_id"] == "rev_pkt_4821"
    assert peer_violation["target_role"] == "implementer"
    assert peer_violation["target_session_id"] == "session-claude-A"
