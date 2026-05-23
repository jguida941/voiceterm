"""Tests for ``check_loose_chat_to_typed_lane`` (G25)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dev.scripts.checks import check_loose_chat_to_typed_lane as guard


_NOW = datetime(2026, 5, 22, 20, 0, 0, tzinfo=timezone.utc)
_ROW = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def _utc(seconds_ago: int) -> str:
    return (_NOW - timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")


def _packet(
    *,
    packet_id: str,
    kind: str = "task_progress",
    body: str = "typed body present",
    target_role: str = "implementer",
    target_session_id: str = "session-claude-A",
    target_ref: str = f"plan:{_ROW}",
    plan_id: str = _ROW,
    chat_only_source: bool = False,
    lifecycle_previous_state: str = "acknowledged",
    lifecycle_current_state: str = "task_progress",
    actor: str = "claude",
    posted_seconds_ago: int = 60,
    selector_active: bool = False,
) -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "kind": kind,
        "body": body,
        "target_role": target_role,
        "target_session_id": target_session_id,
        "target_ref": target_ref,
        "plan_id": plan_id,
        "chat_only_source": chat_only_source,
        "lifecycle_previous_state": lifecycle_previous_state,
        "lifecycle_current_state": lifecycle_current_state,
        "actor": actor,
        "posted_at": _utc(posted_seconds_ago),
        "selector_active": selector_active,
    }


# -- Acceptance 1: loose chat alone is insufficient collaboration proof --


def test_red_loose_chat_promoted_to_implementer_lane_fails():
    packets = [
        _packet(
            packet_id="rev_pkt_chat",
            kind="task_progress",
            body="",
            chat_only_source=True,
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_LOOSE_CHAT_AUTHORITY in rule_ids
    assert report["checked_packet_count"] == 1


def test_green_loose_chat_outside_implementer_lane_passes():
    # chat_only_source on a non-implementer kind is allowed (e.g. continuation_anchor).
    packets = [
        _packet(
            packet_id="rev_pkt_chat_anchor",
            kind="continuation_anchor",
            body="",
            chat_only_source=True,
            lifecycle_previous_state="",
            lifecycle_current_state="posted",
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_LOOSE_CHAT_AUTHORITY not in rule_ids


# -- Acceptance 2: typed body + target-provider session + transition path --


def test_red_typed_body_without_target_session_fails():
    packets = [
        _packet(
            packet_id="rev_pkt_no_session",
            kind="task_progress",
            target_session_id="",
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_MISSING_TARGET_SESSION_EVIDENCE in rule_ids


def test_red_unsupported_lifecycle_transition_fails():
    # task_produced -> task_progress is not in SUPPORTED_LIFECYCLE_TRANSITIONS.
    packets = [
        _packet(
            packet_id="rev_pkt_bad_transition",
            kind="task_progress",
            lifecycle_previous_state="task_produced",
            lifecycle_current_state="task_progress",
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_LIFECYCLE_TRANSITION_MISSING in rule_ids


def test_green_typed_body_with_session_and_supported_transition_passes():
    packets = [
        _packet(
            packet_id="rev_pkt_clean",
            kind="task_progress",
            lifecycle_previous_state="acknowledged",
            lifecycle_current_state="task_progress",
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    assert report["ok"] is True
    assert report["violations"] == []
    assert report["checked_packet_count"] == 1


# -- Acceptance 3: missing path requires typed blocker, not Codex implementer --


def test_red_codex_takes_implementer_lane_on_missing_path_fails():
    packets = [
        _packet(
            packet_id="rev_pkt_codex_lane_grab",
            kind="task_progress",
            actor="codex",
            lifecycle_previous_state="task_produced",  # unsupported -> implementer lane
            lifecycle_current_state="task_progress",
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    assert report["ok"] is False
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CODEX_TAKES_IMPLEMENTER_LANE in rule_ids
    assert guard.RULE_LIFECYCLE_TRANSITION_MISSING in rule_ids


def test_green_codex_emits_typed_blocker_instead_passes():
    # When the path is missing, the required output is a typed blocker, which
    # is not an implementer-lane kind and therefore is allowed for codex.
    packets = [
        _packet(
            packet_id="rev_pkt_codex_blocker",
            kind="task_blocked",
            actor="codex",
            lifecycle_previous_state="acknowledged",
            lifecycle_current_state="task_blocked",
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_CODEX_TAKES_IMPLEMENTER_LANE not in rule_ids
    assert guard.RULE_LIFECYCLE_TRANSITION_MISSING not in rule_ids
    assert report["ok"] is True


# -- Acceptance 4 & 5: stale action_request must not hide newer blockers --


def test_red_stale_action_request_hides_newer_blocker_fails():
    # rev_pkt_4804 (stale action_request, selector_active=True) vs
    # rev_pkt_4821 (newer task_blocked from same row).
    packets = [
        _packet(
            packet_id="rev_pkt_4804",
            kind="action_request",
            posted_seconds_ago=86400 * 3,  # 3 days ago
            selector_active=True,
            lifecycle_previous_state="posted",
            lifecycle_current_state="acknowledged",
        ),
        _packet(
            packet_id="rev_pkt_4821",
            kind="task_blocked",
            posted_seconds_ago=300,  # 5 minutes ago
            selector_active=False,
            lifecycle_previous_state="acknowledged",
            lifecycle_current_state="task_blocked",
        ),
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    assert report["ok"] is False
    offenders = [
        v
        for v in report["violations"]
        if v["rule_id"] == guard.RULE_STALE_PACKET_HIDES_NEWER_BLOCKER
    ]
    assert offenders, "expected a stale-selector violation row"
    offender = offenders[0]
    assert offender["packet_id"] == "rev_pkt_4804"
    assert "rev_pkt_4821" in offender["evidence_packet_ids"]


def test_green_newer_blocker_already_active_passes():
    packets = [
        _packet(
            packet_id="rev_pkt_4804",
            kind="action_request",
            posted_seconds_ago=86400 * 3,
            selector_active=False,
            lifecycle_previous_state="posted",
            lifecycle_current_state="acknowledged",
        ),
        _packet(
            packet_id="rev_pkt_4821",
            kind="task_blocked",
            posted_seconds_ago=300,
            selector_active=True,
            lifecycle_previous_state="acknowledged",
            lifecycle_current_state="task_blocked",
        ),
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_STALE_PACKET_HIDES_NEWER_BLOCKER not in rule_ids


def test_green_no_blocker_for_row_does_not_flag_action_request():
    # When the row has no blocker, an action_request being selector_active is fine.
    packets = [
        _packet(
            packet_id="rev_pkt_solo_action",
            kind="action_request",
            posted_seconds_ago=600,
            selector_active=True,
            lifecycle_previous_state="posted",
            lifecycle_current_state="acknowledged",
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_STALE_PACKET_HIDES_NEWER_BLOCKER not in rule_ids


def test_red_stale_selector_cross_row_does_not_leak():
    # Action request and blocker on different rows must not cross-flag.
    other_row = "MP-OTHER-ROW-S1"
    packets = [
        _packet(
            packet_id="rev_pkt_other_action",
            kind="action_request",
            target_ref=f"plan:{other_row}",
            plan_id=other_row,
            posted_seconds_ago=86400 * 3,
            selector_active=True,
            lifecycle_previous_state="posted",
            lifecycle_current_state="acknowledged",
        ),
        _packet(
            packet_id="rev_pkt_main_blocker",
            kind="task_blocked",
            posted_seconds_ago=300,
            selector_active=False,
            lifecycle_previous_state="acknowledged",
            lifecycle_current_state="task_blocked",
        ),
    ]
    # Scope to the main row only -- the other-row action_request should not be checked.
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    rule_ids = {v["rule_id"] for v in report["violations"]}
    assert guard.RULE_STALE_PACKET_HIDES_NEWER_BLOCKER not in rule_ids


# -- Markdown rendering smoke --


def test_render_markdown_includes_violations():
    packets = [
        _packet(
            packet_id="rev_pkt_md_render",
            kind="task_progress",
            body="",
            chat_only_source=True,
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert "rev_pkt_md_render" in md
    assert guard.RULE_LOOSE_CHAT_AUTHORITY in md
    assert guard.DISPLAY_TEXT in md


def test_row_id_filter_skips_other_rows():
    packets = [
        _packet(
            packet_id="rev_pkt_other",
            kind="task_progress",
            target_ref="plan:MP-DIFFERENT-ROW",
            plan_id="MP-DIFFERENT-ROW",
            body="",
            chat_only_source=True,
        )
    ]
    report = guard.build_report(packets=packets, current_row_id=_ROW)
    assert report["ok"] is True
    assert report["checked_packet_count"] == 0


def test_unknown_review_state_path_emits_warning():
    from pathlib import Path

    missing = Path("/tmp/nonexistent-loose-chat-test-state.json")
    report = guard.build_report(review_state_path=missing, current_row_id=_ROW)
    assert report["ok"] is True
    assert any(
        "review state missing" in str(w).lower() for w in report["warnings"]
    )
