"""Tests for `check_action_request_expiry_refresh` (G24)."""

from __future__ import annotations

from datetime import datetime, timezone

from dev.scripts.checks import check_action_request_expiry_refresh as guard


CURRENT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
NOW = datetime(2026, 5, 22, 20, 0, 0, tzinfo=timezone.utc)


def _action_request(
    *,
    packet_id: str,
    expires_at_utc: str = "2026-05-22T19:00:00Z",
    posted_at: str = "2026-05-22T18:00:00Z",
    target_role: str = "implementer",
    target_session_id: str = "session-codex-A",
    target_ref: str = f"plan:{CURRENT_ROW_ID}",
    plan_id: str = CURRENT_ROW_ID,
    selector_state: str = "selected_only_active",
    kind: str = "action_request",
    **extra: object,
) -> dict[str, object]:
    packet: dict[str, object] = {
        "packet_id": packet_id,
        "kind": kind,
        "selector_state": selector_state,
        "expires_at_utc": expires_at_utc,
        "posted_at": posted_at,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "target_ref": target_ref,
        "plan_id": plan_id,
        "status": "pending",
    }
    packet.update(extra)
    return packet


def _body_observed_event(packet_id: str) -> dict[str, object]:
    return {
        "event_type": "packet_body_observed",
        "event_id": f"evt-observed-{packet_id}",
        "packet_id": packet_id,
        "body_observed_role": "implementer",
        "body_observed_session_id": "session-codex-A",
        "body_observed_at_utc": "2026-05-22T18:30:00Z",
    }


def test_selected_action_request_expired_without_refresh_or_blocker_fails():
    packets = [_action_request(packet_id="pkt_expired_1")]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_SELECTED_EXPIRED_NO_REPLACEMENT in rules
    assert report["checked_packet_count"] == 1
    assert report["selected_action_request_count"] == 1


def test_unexpired_selected_action_request_passes():
    packets = [
        _action_request(
            packet_id="pkt_unexpired",
            expires_at_utc="2026-05-22T22:00:00Z",
        )
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_expired_packet_with_body_observed_event_does_not_fail():
    packets = [_action_request(packet_id="pkt_body_open")]
    events = [_body_observed_event("pkt_body_open")]
    report = guard.build_report(
        packets=packets,
        events=events,
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_expired_packet_with_fresh_refresh_packet_passes():
    packets = [
        _action_request(packet_id="pkt_expired_2"),
        _action_request(
            packet_id="pkt_refresh_2",
            kind="action_request_refresh",
            selector_state="pending",
            expires_at_utc="2026-05-22T23:00:00Z",
            posted_at="2026-05-22T19:30:00Z",
            refresh_of_packet_id="pkt_expired_2",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_expired_packet_with_typed_blocker_packet_passes():
    packets = [
        _action_request(packet_id="pkt_expired_3"),
        {
            "packet_id": "pkt_blocker_3",
            "kind": "task_blocked",
            "selector_state": "pending",
            "refresh_of_packet_id": "pkt_expired_3",
            "target_ref": f"plan:{CURRENT_ROW_ID}",
            "plan_id": CURRENT_ROW_ID,
            "status": "pending",
        },
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_refresh_packet_missing_expired_ref_fails():
    packets = [
        _action_request(packet_id="pkt_expired_4"),
        _action_request(
            packet_id="pkt_refresh_4",
            kind="action_request_refresh",
            selector_state="pending",
            expires_at_utc="2026-05-22T23:00:00Z",
            posted_at="2026-05-22T19:30:00Z",
            # Intentionally no refresh_of_packet_id linking the expired packet.
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    # Without an expired-ref linkage, no refresh is detected, so the underlying
    # rule is the "no refresh/blocker" violation on the expired packet.
    assert guard.RULE_SELECTED_EXPIRED_NO_REPLACEMENT in rules


def test_refresh_packet_missing_plan_row_ref_fails():
    packets = [
        _action_request(packet_id="pkt_expired_5"),
        _action_request(
            packet_id="pkt_refresh_5",
            kind="action_request_refresh",
            selector_state="pending",
            expires_at_utc="2026-05-22T23:00:00Z",
            posted_at="2026-05-22T19:30:00Z",
            target_ref="plan:OTHER-ROW",
            plan_id="OTHER-ROW",
            refresh_of_packet_id="pkt_expired_5",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_REFRESH_MISSING_PLAN_ROW in rules


def test_refresh_packet_mismatched_role_session_target_fails():
    packets = [
        _action_request(packet_id="pkt_expired_6"),
        _action_request(
            packet_id="pkt_refresh_6",
            kind="action_request_refresh",
            selector_state="pending",
            expires_at_utc="2026-05-22T23:00:00Z",
            posted_at="2026-05-22T19:30:00Z",
            target_role="reviewer",  # mismatched
            target_session_id="session-claude-Z",  # mismatched
            refresh_of_packet_id="pkt_expired_6",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_REFRESH_MISMATCHED_TARGET in rules


def test_stale_selected_blocks_newer_finding_fails():
    packets = [
        _action_request(packet_id="pkt_expired_7"),
        {
            "packet_id": "pkt_newer_finding_7",
            "kind": "finding",
            "selector_state": "pending",
            "posted_at": "2026-05-22T19:30:00Z",
            "target_ref": f"plan:{CURRENT_ROW_ID}",
            "plan_id": CURRENT_ROW_ID,
            "status": "pending",
        },
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is False
    rules = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_STALE_BLOCKS_NEWER_FINDING in rules


def test_packet_id_filter_limits_check_scope():
    packets = [
        _action_request(packet_id="pkt_active"),
        _action_request(packet_id="pkt_stale_other"),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        packet_ids=("pkt_active",),
        now=NOW,
    )
    assert report["packet_ids"] == ["pkt_active"]
    assert report["checked_packet_ids"] == ["pkt_active"]
    assert report["checked_packet_count"] == 1
    violation_packets = {v["packet_id"] for v in report["violations"]}
    assert violation_packets == {"pkt_active"}


def test_non_action_request_kind_is_ignored():
    packets = [
        _action_request(
            packet_id="pkt_decision",
            kind="decision",
        )
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is True
    assert report["selected_action_request_count"] == 0


def test_unselected_action_request_is_ignored():
    packets = [
        _action_request(
            packet_id="pkt_pending",
            selector_state="pending",
        )
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is True
    assert report["selected_action_request_count"] == 0


def test_render_markdown_includes_violations():
    packets = [_action_request(packet_id="pkt_md_1")]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        packet_ids=("pkt_md_1",),
        now=NOW,
    )
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert "pkt_md_1" in md
    assert guard.RULE_SELECTED_EXPIRED_NO_REPLACEMENT in md
    assert "packet_ids: `pkt_md_1`" in md


def test_render_markdown_clean_report_omits_violations_section():
    packets = [
        _action_request(
            packet_id="pkt_clean",
            expires_at_utc="2026-05-22T22:00:00Z",
        )
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    md = guard.render_markdown(report)
    assert "## Violations" not in md
    assert "ok: True" in md


def test_refresh_via_supersedes_packet_id_satisfies_link():
    packets = [
        _action_request(packet_id="pkt_expired_8"),
        _action_request(
            packet_id="pkt_refresh_8",
            kind="action_request",
            selector_state="pending",
            expires_at_utc="2026-05-22T23:00:00Z",
            posted_at="2026-05-22T19:30:00Z",
            supersedes_packet_id="pkt_expired_8",
        ),
    ]
    report = guard.build_report(
        packets=packets,
        events=(),
        current_row_id=CURRENT_ROW_ID,
        now=NOW,
    )
    assert report["ok"] is True
    assert report["violation_count"] == 0
