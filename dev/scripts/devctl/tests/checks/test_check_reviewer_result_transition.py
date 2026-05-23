"""Tests for `check_reviewer_result_transition` (G26)."""

from __future__ import annotations

from dev.scripts.checks import check_reviewer_result_transition as guard


# ----- factory helpers -----------------------------------------------------


def _row_verified(
    *,
    session_id: str = "session-reviewer-A",
    actor_role: str = "reviewer",
    target_ref: str = "plan:MP-G26-ROW",
    plan_id: str = "MP-G26-ROW",
    event_id: str = "evt-verified-1",
) -> dict[str, object]:
    return {
        "event_type": guard.ROW_VERIFIED_EVENT_TYPE,
        "event_id": event_id,
        "session_id": session_id,
        "actor_role": actor_role,
        "target_ref": target_ref,
        "plan_id": plan_id,
    }


def _review_result_posted(
    *,
    packet_id: str,
    kind: str = "review_accepted",
    session_id: str = "session-reviewer-A",
    target_ref: str = "plan:MP-G26-ROW",
    plan_id: str = "MP-G26-ROW",
    acceptance_evidence: object = (),
    event_id: str | None = None,
) -> dict[str, object]:
    return {
        "event_type": guard.REVIEW_RESULT_POSTED_EVENT_TYPE,
        "event_id": event_id or f"evt-posted-{packet_id}",
        "packet_id": packet_id,
        "kind": kind,
        "session_id": session_id,
        "target_ref": target_ref,
        "plan_id": plan_id,
        "acceptance_evidence": acceptance_evidence,
    }


def _review_result_attempt(
    *,
    attempt_id: str,
    blocker_reason: str = "",
    packet_id: str = "rev_pkt_attempt",
    session_id: str = "session-reviewer-A",
    target_ref: str = "plan:MP-G26-ROW",
    plan_id: str = "MP-G26-ROW",
) -> dict[str, object]:
    return {
        "event_type": guard.REVIEW_RESULT_ATTEMPT_EVENT_TYPE,
        "event_id": f"evt-attempt-{attempt_id}",
        "attempt_id": attempt_id,
        "packet_id": packet_id,
        "session_id": session_id,
        "blocker_reason": blocker_reason,
        "target_ref": target_ref,
        "plan_id": plan_id,
    }


def _attempted_action_receipt(
    *,
    attempt_id: str,
    next_transition: str = "body_open",
    event_id: str | None = None,
) -> dict[str, object]:
    return {
        "event_type": guard.ATTEMPTED_ACTION_RECEIPT_EVENT_TYPE,
        "event_id": event_id or f"evt-receipt-{attempt_id}",
        "attempt_id": attempt_id,
        "next_transition": next_transition,
    }


def _blocker_recorded(
    *, attempt_id: str, event_id: str | None = None
) -> dict[str, object]:
    return {
        "event_type": guard.BLOCKER_EVIDENCE_RECORDED_EVENT_TYPE,
        "event_id": event_id or f"evt-blocker-{attempt_id}",
        "attempt_id": attempt_id,
        "blocker_kind": "route_lifecycle",
    }


def _control_decision_evaluated(
    *,
    event_id: str = "evt-ctrl-1",
    control_decision_input: str = "/tmp/decision.json",
    control_decision_input_readable: bool = True,
    control_decision_summary: str = "decision_applied",
    session_id: str = "session-reviewer-A",
    packet_id: str = "rev_pkt_ctrl",
) -> dict[str, object]:
    return {
        "event_type": guard.CONTROL_DECISION_EVALUATED_EVENT_TYPE,
        "event_id": event_id,
        "control_decision_input": control_decision_input,
        "control_decision_input_readable": control_decision_input_readable,
        "control_decision_summary": control_decision_summary,
        "session_id": session_id,
        "packet_id": packet_id,
    }


def _implementer_lane_claim(
    *,
    session_id: str = "session-reviewer-A",
    actor_role: str = "reviewer",
    event_id: str = "evt-lane-1",
) -> dict[str, object]:
    return {
        "event_type": guard.IMPLEMENTER_LANE_CLAIM_EVENT_TYPE,
        "event_id": event_id,
        "session_id": session_id,
        "actor_role": actor_role,
    }


# ----- A1: typed reviewer-result path after verification -------------------


def test_verified_reviewer_with_review_accepted_posting_passes():
    events = [
        _row_verified(),
        _review_result_posted(packet_id="rev_pkt_A", kind="review_accepted"),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is True, report["violations"]
    assert report["verified_session_count"] == 1
    assert report["review_result_posted_count"] == 1


def test_verified_reviewer_without_review_result_fails():
    events = [_row_verified()]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_NO_TYPED_PATH in reasons


def test_verified_reviewer_with_review_failed_posting_passes():
    events = [
        _row_verified(),
        _review_result_posted(packet_id="rev_pkt_FAIL", kind="review_failed"),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is True, report["violations"]


# ----- A2: ControlDecisionObeyedGuard preserves --control-decision-input ---


def test_control_decision_input_readable_summarized_as_no_input_fails():
    events = [
        _row_verified(),
        _review_result_posted(packet_id="rev_pkt_C"),
        _control_decision_evaluated(
            control_decision_input="/tmp/decision.json",
            control_decision_input_readable=True,
            control_decision_summary="no_control_decision_input",
        ),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_CONTROL_DECISION_INPUT_DISCARDED in reasons


def test_control_decision_input_evaluated_correctly_passes():
    events = [
        _row_verified(),
        _review_result_posted(packet_id="rev_pkt_D"),
        _control_decision_evaluated(
            control_decision_input="/tmp/decision.json",
            control_decision_input_readable=True,
            control_decision_summary="decision_applied",
        ),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is True, report["violations"]


def test_control_decision_no_input_supplied_does_not_trigger_violation():
    events = [
        _row_verified(),
        _review_result_posted(packet_id="rev_pkt_E"),
        _control_decision_evaluated(
            control_decision_input="",
            control_decision_input_readable=False,
            control_decision_summary="no_control_decision_input",
        ),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is True, report["violations"]


# ----- A3: blocked attempts must promote attempted-action receipt ----------


def test_blocked_attempt_without_receipt_fails():
    events = [
        _row_verified(),
        _review_result_attempt(
            attempt_id="att-1", blocker_reason="checkpoint_gate"
        ),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_BLOCKED_NO_RECEIPT in reasons


def test_blocked_attempt_receipt_without_next_transition_fails():
    events = [
        _row_verified(),
        _review_result_attempt(
            attempt_id="att-2", blocker_reason="checkpoint_gate"
        ),
        _attempted_action_receipt(attempt_id="att-2", next_transition=""),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_BLOCKED_NO_NEXT_TRANSITION in reasons


def test_blocked_checkpoint_with_full_receipt_passes():
    events = [
        _row_verified(),
        _review_result_attempt(
            attempt_id="att-3", blocker_reason="checkpoint_gate"
        ),
        _attempted_action_receipt(
            attempt_id="att-3", next_transition="checkpoint_complete"
        ),
        _blocker_recorded(attempt_id="att-3"),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is True, report["violations"]


# ----- A4: body_open_required must be promoted to route lifecycle blocker --


def test_body_open_required_without_blocker_recorded_fails():
    events = [
        _row_verified(),
        _review_result_attempt(
            attempt_id="att-4", blocker_reason="body_open_required"
        ),
        _attempted_action_receipt(
            attempt_id="att-4", next_transition="body_open"
        ),
        # No `_blocker_recorded` event -> must fail with REASON_BLOCKER_NOT_PROMOTED.
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_BLOCKER_NOT_PROMOTED in reasons


def test_body_open_required_with_blocker_recorded_passes():
    events = [
        _row_verified(),
        _review_result_attempt(
            attempt_id="att-5", blocker_reason="body_open_required"
        ),
        _attempted_action_receipt(
            attempt_id="att-5", next_transition="body_open"
        ),
        _blocker_recorded(attempt_id="att-5"),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is True, report["violations"]


def test_reviewer_session_taking_implementer_lane_fails():
    events = [
        _row_verified(),
        _review_result_posted(packet_id="rev_pkt_lane"),
        _implementer_lane_claim(actor_role="reviewer"),
    ]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_IMPLEMENTER_LANE_TAKEN in reasons


# ----- A5: rev_pkt_4821 requires three named evidence tags -----------------


def test_rev_pkt_4821_missing_evidence_fails():
    events = [
        _row_verified(),
        _review_result_posted(
            packet_id="rev_pkt_4821",
            acceptance_evidence=("command_output:test-python:744231b533e97e1c",),
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is False
    reasons = {v["reason"] for v in report["violations"]}
    assert guard.REASON_REV_PKT_4821_MISSING_EVIDENCE in reasons


def test_rev_pkt_4821_with_all_required_evidence_passes():
    events = [
        _row_verified(),
        _review_result_posted(
            packet_id="rev_pkt_4821",
            acceptance_evidence=(
                "command_output:test-python:744231b533e97e1c",
                "check_active_topology_liveness.py",
                "conftest.py:untouched",
            ),
        ),
    ]
    report = guard.build_report(events=events)
    assert report["ok"] is True, report["violations"]


# ----- ancillary: row filter + markdown render -----------------------------


def test_row_id_filter_excludes_unrelated_events():
    events = [
        _row_verified(target_ref="plan:OTHER", plan_id="OTHER"),
        _review_result_posted(
            packet_id="rev_pkt_other",
            target_ref="plan:OTHER",
            plan_id="OTHER",
        ),
    ]
    report = guard.build_report(
        events=events,
        row_id_filter="MP-G26-ROW",
        require_rev_pkt_4821_evidence=False,
    )
    assert report["ok"] is True, report["violations"]
    assert report["checked_event_count"] == 0


def test_render_markdown_includes_violations():
    events = [_row_verified()]
    report = guard.build_report(events=events, require_rev_pkt_4821_evidence=False)
    md = guard.render_markdown(report)
    assert "## Violations" in md
    assert guard.REASON_NO_TYPED_PATH in md
    assert "verified_session_count: 1" in md
