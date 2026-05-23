"""Tests for `check_packet_body_observation_route`."""

from __future__ import annotations

from dev.scripts.checks import check_packet_body_observation_route as guard


def _packet_posted_event(
    *,
    packet_id: str,
    body: str = "hello",
    target_role: str = "implementer",
    target_session_id: str = "session-claude-A",
    target_ref: str = "plan:MP-ROW-A",
    plan_id: str = "MP-ROW-A",
) -> dict[str, object]:
    return {
        "event_type": guard.PACKET_POSTED_EVENT_TYPE,
        "event_id": f"evt-posted-{packet_id}",
        "packet_id": packet_id,
        "body": body,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "target_ref": target_ref,
        "plan_id": plan_id,
    }


def _body_observed_event(
    *,
    packet_id: str,
    role: str = "implementer",
    session: str = "session-claude-A",
    event_suffix: str = "1",
) -> dict[str, object]:
    return {
        "event_type": guard.PACKET_BODY_OBSERVED_EVENT_TYPE,
        "event_id": f"evt-observed-{packet_id}-{event_suffix}",
        "packet_id": packet_id,
        "body_observed_role": role,
        "body_observed_session_id": session,
        "body_observed_at_utc": "2026-05-22T18:00:00Z",
        "body_digest": "abc123",
    }


def test_route_matched_passes():
    events = [
        _packet_posted_event(packet_id="rev_pkt_A"),
        _body_observed_event(packet_id="rev_pkt_A"),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is True
    assert report["violation_count"] == 0
    assert report["checked_packet_count"] == 1
    assert report["observation_event_count"] == 1


def test_route_missing_fails():
    events = [_packet_posted_event(packet_id="rev_pkt_B")]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    assert report["violation_count"] == 1
    violation = report["violations"][0]
    assert violation["reason"] == guard.REASON_ROUTE_MISSING
    assert violation["packet_id"] == "rev_pkt_B"


def test_cross_role_spoofing_fails():
    events = [
        _packet_posted_event(packet_id="rev_pkt_C", target_role="implementer"),
        _body_observed_event(packet_id="rev_pkt_C", role="reviewer"),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_CROSS_ROLE_SPOOF in reasons
    assert guard.REASON_ROUTE_MISSING in reasons


def test_cross_session_spoofing_fails():
    events = [
        _packet_posted_event(
            packet_id="rev_pkt_D",
            target_session_id="session-claude-A",
        ),
        _body_observed_event(
            packet_id="rev_pkt_D",
            session="session-claude-B",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_CROSS_SESSION_SPOOF in reasons


def test_empty_body_skipped():
    events = [
        _packet_posted_event(packet_id="rev_pkt_E", body=""),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is True
    assert report["checked_packet_count"] == 1
    assert report["violation_count"] == 0


def test_packet_without_target_role_or_session_skipped():
    events = [
        _packet_posted_event(
            packet_id="rev_pkt_F",
            target_role="",
            target_session_id="",
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is True
    assert report["checked_packet_count"] == 1
    assert report["violation_count"] == 0


def test_row_id_filter_includes_matching_target_ref():
    events = [
        _packet_posted_event(
            packet_id="rev_pkt_G",
            target_ref="plan:MP-ROW-FILTERED",
            plan_id="MP-ROW-FILTERED",
        ),
    ]
    report = guard.build_report(events=events, row_id_filter="MP-ROW-FILTERED")
    assert report["ok"] is False
    assert report["checked_packet_count"] == 1


def test_row_id_filter_excludes_other_rows():
    events = [
        _packet_posted_event(
            packet_id="rev_pkt_H",
            target_ref="plan:OTHER-ROW",
            plan_id="OTHER-ROW",
        ),
    ]
    report = guard.build_report(events=events, row_id_filter="MP-ROW-FILTERED")
    assert report["ok"] is True
    assert report["checked_packet_count"] == 0


def test_packet_id_filter_limits_current_proof_scope():
    events = [
        _packet_posted_event(packet_id="rev_pkt_active"),
        _packet_posted_event(packet_id="rev_pkt_stale"),
    ]
    report = guard.build_report(events=events, packet_ids=("rev_pkt_active",))
    assert report["ok"] is False
    assert report["checked_packet_ids"] == ["rev_pkt_active"]
    assert report["checked_packet_count"] == 1
    assert [v["packet_id"] for v in report["violations"]] == ["rev_pkt_active"]


def test_packet_id_filter_deduplicates_empty_values():
    events = [_packet_posted_event(packet_id="rev_pkt_active")]
    report = guard.build_report(
        events=events,
        packet_ids=("", "rev_pkt_active", "rev_pkt_active"),
    )
    assert report["packet_ids"] == ["rev_pkt_active"]
    assert report["checked_packet_count"] == 1


def test_multiple_observations_all_matching_pass():
    events = [
        _packet_posted_event(packet_id="rev_pkt_I"),
        _body_observed_event(packet_id="rev_pkt_I", event_suffix="1"),
        _body_observed_event(packet_id="rev_pkt_I", event_suffix="2"),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is True
    assert report["observation_event_count"] == 2


def test_render_markdown_includes_violations():
    events = [_packet_posted_event(packet_id="rev_pkt_J")]
    report = guard.build_report(events=events, packet_ids=("rev_pkt_J",))
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert "rev_pkt_J" in md
    assert "packet_ids: `rev_pkt_J`" in md
    assert guard.REASON_ROUTE_MISSING in md
