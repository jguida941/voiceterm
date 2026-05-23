"""Tests for `check_packet_hygiene_enforcement` (A19 G40)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dev.scripts.checks import check_packet_hygiene_enforcement as guard


_NOW = datetime(2026, 5, 22, 20, 0, 0, tzinfo=timezone.utc)


def _utc(seconds_ago: int) -> str:
    return (_NOW - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def _packet(
    *,
    packet_id: str,
    status: str = "pending",
    posted_seconds_ago: int = 60,
    expires_seconds_ago: int | None = None,
    delivery_emitted_at_utc: str = "",
    target_ref: str = "plan:MP-ROW-A",
    plan_id: str = "MP-ROW-A",
    kind: str = "task_progress",
    disposition_state: str = "",
    packet_creation_binding: dict | None = None,
) -> dict[str, object]:
    p: dict[str, object] = {
        "packet_id": packet_id,
        "status": status,
        "kind": kind,
        "posted_at": _utc(posted_seconds_ago),
        "delivery_emitted_at_utc": delivery_emitted_at_utc,
        "target_ref": target_ref,
        "plan_id": plan_id,
        "disposition_state": disposition_state,
    }
    if expires_seconds_ago is not None:
        p["expires_at_utc"] = _utc(expires_seconds_ago)
    if packet_creation_binding is not None:
        p["packet_creation_binding"] = packet_creation_binding
    return p


def _materialization_event(seconds_ago: int) -> dict[str, object]:
    return {
        "event_type": guard.PACKET_EXPIRED_EVENT_TYPE,
        "timestamp_utc": _utc(seconds_ago),
    }


def test_green_no_violations():
    packets = [
        _packet(packet_id="rev_pkt_fresh", posted_seconds_ago=60),
    ]
    report = guard.build_report(packets=packets, events=[], now=_NOW)
    assert report["ok"] is True
    assert report["live_pending_total"] == 1
    assert report["failures"] == []


def test_rule_1_stale_in_default_view_fails():
    packets = [
        _packet(
            packet_id="rev_pkt_old",
            posted_seconds_ago=guard.DEFAULT_HYGIENE_WINDOW_SECONDS + 1,
        ),
    ]
    report = guard.build_report(packets=packets, events=[], now=_NOW)
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_STALE_IN_DEFAULT_VIEW in rule_ids
    assert report["stale_within_hygiene_window_count"] == 1


def test_rule_1_hidden_by_include_stale_flag():
    packets = [
        _packet(
            packet_id="rev_pkt_old",
            posted_seconds_ago=guard.DEFAULT_HYGIENE_WINDOW_SECONDS + 1,
        ),
    ]
    report = guard.build_report(
        packets=packets, events=[], now=_NOW, include_stale=True
    )
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_STALE_IN_DEFAULT_VIEW not in rule_ids


def test_rule_2_stale_count_without_recent_materialization_fails():
    packets = [
        _packet(packet_id="rev_pkt_expired", expires_seconds_ago=10),
    ]
    report = guard.build_report(packets=packets, events=[], now=_NOW)
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_NO_RECENT_MATERIALIZATION in rule_ids
    assert report["past_expires_count"] == 1


def test_rule_2_passes_with_recent_materialization():
    packets = [
        _packet(packet_id="rev_pkt_expired", expires_seconds_ago=10),
    ]
    events = [_materialization_event(seconds_ago=60)]
    report = guard.build_report(packets=packets, events=events, now=_NOW)
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_NO_RECENT_MATERIALIZATION not in rule_ids


def test_rule_3_delivery_pending_fails():
    packets = [
        _packet(
            packet_id="rev_pkt_undelivered",
            posted_seconds_ago=guard.DEFAULT_DELIVERY_PENDING_SECONDS + 1,
            delivery_emitted_at_utc="",
        ),
    ]
    report = guard.build_report(packets=packets, events=[], now=_NOW)
    assert report["ok"] is False
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_DELIVERY_PENDING in rule_ids


def test_evaluate_delivery_stall_returns_packet_level_rows():
    packets = [
        _packet(
            packet_id="rev_pkt_undelivered",
            posted_seconds_ago=guard.DEFAULT_DELIVERY_PENDING_SECONDS + 1,
            delivery_emitted_at_utc="",
            kind="action_request",
        ),
    ]
    report = guard.evaluate_delivery_stall(
        packets=packets,
        now=_NOW,
        stall_threshold_seconds=guard.DEFAULT_DELIVERY_PENDING_SECONDS,
    )
    assert report["ok"] is False
    assert report["delivery_stall_count"] == 1
    assert report["violations"][0]["packet_id"] == "rev_pkt_undelivered"
    assert report["violations"][0]["reason"] == guard.RULE_DELIVERY_PENDING


def test_rule_3_passes_when_delivery_emitted():
    packets = [
        _packet(
            packet_id="rev_pkt_delivered",
            posted_seconds_ago=guard.DEFAULT_DELIVERY_PENDING_SECONDS + 1,
            delivery_emitted_at_utc=_utc(10),
        ),
    ]
    report = guard.build_report(packets=packets, events=[], now=_NOW)
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_DELIVERY_PENDING not in rule_ids


def test_rule_4_durable_binding_missing_fails():
    packets = [
        _packet(
            packet_id="rev_pkt_unbound",
            posted_seconds_ago=guard.DEFAULT_HYGIENE_WINDOW_SECONDS + 1,
            target_ref="",
            plan_id="",
        ),
    ]
    report = guard.build_report(
        packets=packets, events=[], now=_NOW, include_stale=True
    )
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_DURABLE_BINDING_MISSING in rule_ids
    assert report["durable_binding_missing_count"] == 1


def test_rule_4_passes_with_target_ref():
    packets = [
        _packet(
            packet_id="rev_pkt_bound",
            posted_seconds_ago=guard.DEFAULT_HYGIENE_WINDOW_SECONDS + 1,
            target_ref="plan:MP-ROW-X",
            plan_id="",
        ),
    ]
    report = guard.build_report(
        packets=packets, events=[], now=_NOW, include_stale=True
    )
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_DURABLE_BINDING_MISSING not in rule_ids


def test_rule_5_sweep_cannot_drain_fails():
    packets = [
        _packet(packet_id=f"rev_pkt_e{i}", expires_seconds_ago=10)
        for i in range(25)
    ]
    report = guard.build_report(
        packets=packets,
        events=[],
        now=_NOW,
        expire_packets_limit_default=20,
    )
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_SWEEP_CANNOT_DRAIN in rule_ids


def test_rule_5_passes_with_adequate_default():
    packets = [
        _packet(packet_id=f"rev_pkt_e{i}", expires_seconds_ago=10)
        for i in range(5)
    ]
    report = guard.build_report(
        packets=packets,
        events=[],
        now=_NOW,
        expire_packets_limit_default=20,
    )
    rule_ids = {f["rule_id"] for f in report["failures"]}
    assert guard.RULE_SWEEP_CANNOT_DRAIN not in rule_ids


def test_terminal_state_packets_excluded():
    packets = [
        _packet(
            packet_id="rev_pkt_absorbed",
            posted_seconds_ago=guard.DEFAULT_HYGIENE_WINDOW_SECONDS + 1,
            disposition_state="absorbed",
        ),
    ]
    report = guard.build_report(packets=packets, events=[], now=_NOW)
    assert report["live_pending_total"] == 0


def test_output_schema_matches_plan_spec():
    report = guard.build_report(packets=[], events=[], now=_NOW)
    for field in (
        "ok",
        "current_plan_row_id",
        "live_pending_total",
        "stale_within_hygiene_window_count",
        "past_expires_count",
        "delivery_pending_count",
        "durable_binding_missing_count",
        "last_expire_packets_at_utc",
        "hygiene_window_seconds",
        "checked_surfaces",
        "failures",
    ):
        assert field in report, f"missing required field {field!r}"


def test_render_markdown_includes_failures():
    packets = [
        _packet(
            packet_id="rev_pkt_old",
            posted_seconds_ago=guard.DEFAULT_HYGIENE_WINDOW_SECONDS + 1,
        ),
    ]
    report = guard.build_report(packets=packets, events=[], now=_NOW)
    md = guard.render_markdown(report)
    assert "## Failures" in md
    assert guard.RULE_STALE_IN_DEFAULT_VIEW in md
