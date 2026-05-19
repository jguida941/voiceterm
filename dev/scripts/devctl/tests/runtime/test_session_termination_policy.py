"""Tests for typed task-complete continuation policy."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from dev.scripts.devctl.review_channel.packet_contract import (
    VALID_PACKET_KINDS,
)
from dev.scripts.devctl.runtime.packet_transport_expiry import (
    TRANSPORT_EXPIRY_EXPLICIT_METADATA_KEY,
)
from dev.scripts.devctl.runtime.review_packet_inbox_actionable import is_actionable
from dev.scripts.devctl.runtime.session_termination_policy import (
    CONTINUATION_ANCHOR_MISSING_ERROR,
    CONTINUATION_ANCHOR_PACKET_KIND,
    PACKET_ATTENTION_PENDING_ERROR,
    PENDING_REVIEW_PACKET_ERROR,
    PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR,
    SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE,
    SESSION_TERMINATION_MODE_KEEP_AWAKE_VIA_PACKETS,
    STOP_ANCHOR_PACKET_KIND,
    STOP_ANCHOR_BODY_UNOBSERVED_ERROR,
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
        "metadata": {TRANSPORT_EXPIRY_EXPLICIT_METADATA_KEY: True},
    }
    packet.update(overrides)
    return packet


def test_anchor_packet_kinds_are_valid_but_not_actionable() -> None:
    assert CONTINUATION_ANCHOR_PACKET_KIND in VALID_PACKET_KINDS
    assert STOP_ANCHOR_PACKET_KIND in VALID_PACKET_KINDS
    assert is_actionable(_anchor()) is False
    assert is_actionable({"kind": STOP_ANCHOR_PACKET_KIND, "status": "pending"}) is False


def test_default_policy_terminates_task_complete_when_no_anchor() -> None:
    # MP377-CONTINUATION-ANCHOR-CONSOLIDATION-S1 (smell #058):
    # default policy still terminates TASK_COMPLETE, but ONLY when there is
    # no live continuation_anchor in the packet set. With no anchor present,
    # the legacy end_on_task_complete behavior is preserved.
    decision = task_complete_decision(
        session_id="session-1",
        packets=(),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )
    assert decision.terminate is True
    assert decision.reason == "policy_default"
    assert decision.policy_mode == SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE
    assert decision.next_command == ""


def test_default_policy_rejects_task_complete_when_continuation_anchor_live() -> None:
    # MP377-CONTINUATION-ANCHOR-CONSOLIDATION-S1 (smell #058 regression test):
    # operator-mandated. When a live continuation_anchor exists in the packet
    # set, TaskCompleteDecision must REJECT termination regardless of policy
    # mode. Previously the end_on_task_complete default mode skipped anchor
    # consultation entirely, letting codex sessions die mid-arc. The fix
    # consults `_active_continuation_anchor()` BEFORE the policy.mode gate.
    decision = task_complete_decision(
        session_id="session-1",
        packets=(_anchor(),),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )
    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"
    assert decision.policy_mode == SESSION_TERMINATION_MODE_END_ON_TASK_COMPLETE
    assert decision.anchor_packet_id == "rev_pkt_anchor"
    assert decision.correlation_id.startswith("corr-")


def test_role_scoped_anchor_survives_session_replacement() -> None:
    decision = task_complete_decision(
        session_id="session-new",
        packets=(
            _anchor(
                target_role="implementer",
                target_session_id="session-dead",
                anchor_scope="role",
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        actor_role="implementer",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"


def test_role_scoped_anchor_requires_successor_body_observation() -> None:
    decision = task_complete_decision(
        session_id="session-new",
        packets=(
            _anchor(
                target_role="implementer",
                target_session_id="session-dead",
                anchor_scope="role",
                body="Read this goal before continuing.",
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        actor_role="implementer",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_body_unobserved"
    assert decision.error_kind == "continuation_anchor_body_unobserved"
    assert decision.blocking_packet_id == "rev_pkt_anchor"
    assert "review-channel --action show --packet-id rev_pkt_anchor" in (
        decision.next_command
    )


def test_role_scoped_anchor_continues_after_successor_body_observation() -> None:
    body = "Read this goal before continuing."
    decision = task_complete_decision(
        session_id="session-new",
        packets=(
            _anchor(
                target_role="implementer",
                target_session_id="session-dead",
                anchor_scope="role",
                body=body,
                body_observation_events=[
                    {
                        "body_observed_by": "codex",
                        "body_observed_role": "implementer",
                        "body_observed_session_id": "session-new",
                        "body_digest": hashlib.sha256(
                            body.encode("utf-8")
                        ).hexdigest(),
                    }
                ],
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        actor_role="implementer",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"


def test_session_scoped_anchor_does_not_survive_session_replacement() -> None:
    decision = task_complete_decision(
        session_id="session-new",
        packets=(
            _anchor(
                target_session_id="session-dead",
                anchor_scope="session",
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        actor_role="implementer",
    )

    assert decision.terminate is True
    assert decision.reason == "policy_default"


def test_plan_scoped_anchor_blocks_matching_plan() -> None:
    decision = task_complete_decision(
        session_id="session-new",
        packets=(
            _anchor(
                target_kind="plan",
                target_ref="MP-377",
                anchor_scope="plan",
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        target_ref="plan:MP-377",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"


def test_plan_scoped_anchor_fails_closed_without_matching_plan() -> None:
    decision = task_complete_decision(
        session_id="session-new",
        packets=(
            _anchor(
                target_kind="plan",
                target_ref="MP-377",
                anchor_scope="plan",
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        target_ref="plan:MP-999",
    )

    assert decision.terminate is True
    assert decision.reason == "policy_default"


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


def test_task_complete_decision_preserves_explicit_lineage_fields() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(_anchor(correlation_id="corr-packet", causation_id="cause-packet"),),
        policy=SessionTerminationPolicy(),
        actor="codex",
        run_id="run-session",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"
    assert decision.correlation_id == "corr-packet"
    assert decision.causation_id == "cause-packet"
    assert decision.run_id == "run-session"


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


def test_stop_anchor_requires_body_observation_before_terminating() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(
            _anchor(
                packet_id="rev_pkt_stop",
                kind=STOP_ANCHOR_PACKET_KIND,
                lifecycle_current_state="pending",
                to_agent="codex",
                body="Stop after reading this anchor.",
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )

    assert decision.terminate is False
    assert decision.reason == STOP_ANCHOR_BODY_UNOBSERVED_ERROR
    assert decision.error_kind == STOP_ANCHOR_BODY_UNOBSERVED_ERROR
    assert decision.blocking_packet_id == "rev_pkt_stop"
    assert "review-channel --action show --packet-id rev_pkt_stop" in (
        decision.next_command
    )


def test_stop_anchor_terminates_after_body_observation() -> None:
    body = "Stop after reading this anchor."
    decision = task_complete_decision(
        session_id="session-1",
        packets=(
            _anchor(
                packet_id="rev_pkt_stop",
                kind=STOP_ANCHOR_PACKET_KIND,
                lifecycle_current_state="pending",
                to_agent="codex",
                body=body,
                body_observation_events=[
                    {
                        "body_observed_by": "codex",
                        "body_observed_session_id": "session-1",
                        "body_digest": hashlib.sha256(
                            body.encode("utf-8")
                        ).hexdigest(),
                    }
                ],
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )

    assert decision.terminate is True
    assert decision.reason == "operator_stop_anchor"
    assert decision.error_kind == ""


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


def test_pending_review_packet_requires_body_observation() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(
            _anchor(
                packet_id="rev_pkt_review",
                kind="review_started",
                lifecycle_current_state="review_in_progress",
                to_agent="codex",
                target_role="reviewer",
                target_session_id="session-1",
                body="Review this before claiming completion.",
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        actor_role="reviewer",
    )

    assert decision.terminate is False
    assert decision.reason == PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR
    assert decision.error_kind == PENDING_REVIEW_PACKET_BODY_UNOBSERVED_ERROR
    assert decision.blocking_packet_id == "rev_pkt_review"
    assert "review-channel --action show --packet-id rev_pkt_review" in (
        decision.next_command
    )


def test_pending_review_packet_blocks_normally_after_body_observation() -> None:
    body = "Review this before claiming completion."
    decision = task_complete_decision(
        session_id="session-1",
        packets=(
            _anchor(
                packet_id="rev_pkt_review",
                kind="review_started",
                lifecycle_current_state="review_in_progress",
                to_agent="codex",
                target_role="reviewer",
                target_session_id="session-1",
                body=body,
                body_observation_events=[
                    {
                        "body_observed_by": "codex",
                        "body_observed_role": "reviewer",
                        "body_observed_session_id": "session-1",
                        "body_digest": hashlib.sha256(
                            body.encode("utf-8")
                        ).hexdigest(),
                    }
                ],
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        actor_role="reviewer",
    )

    assert decision.terminate is False
    assert decision.reason == PENDING_REVIEW_PACKET_ERROR
    assert decision.error_kind == PENDING_REVIEW_PACKET_ERROR
    assert decision.blocking_packet_id == "rev_pkt_review"


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


def test_legacy_auto_ttl_continuation_anchor_remains_live_without_explicit_expiry() -> None:
    decision = task_complete_decision(
        session_id="session-1",
        packets=(
            _anchor(
                expires_at_utc=_stamp(timedelta(minutes=-30)),
                metadata={},
            ),
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"
    assert decision.anchor_packet_id == "rev_pkt_anchor"


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


def test_unstructured_stop_anchor_does_not_override_continuation_anchor() -> None:
    stop_anchor = {
        "packet_id": "rev_pkt_stop",
        "kind": STOP_ANCHOR_PACKET_KIND,
        "status": "pending",
        "lifecycle_current_state": "pending",
        "body": "Target session: dead-session",
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

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"


def test_plan_scoped_stop_anchor_only_overrides_matching_plan() -> None:
    stop_anchor = {
        "packet_id": "rev_pkt_stop",
        "kind": STOP_ANCHOR_PACKET_KIND,
        "status": "pending",
        "lifecycle_current_state": "pending",
        "target_kind": "plan",
        "target_ref": "MP-999",
        "anchor_scope": "plan",
        "posted_at": "2026-05-08T12:01:00+00:00",
        "expires_at_utc": _stamp(timedelta(minutes=30)),
    }
    decision = task_complete_decision(
        session_id="session-1",
        packets=(
            _anchor(target_kind="plan", target_ref="MP-377", anchor_scope="plan"),
            stop_anchor,
        ),
        policy=SessionTerminationPolicy(),
        actor="codex",
        target_ref="plan:MP-377",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"


# ---------------------------------------------------------------------------
# SLICE-Z (rev_pkt_4517 bug #9): slice-counted continuation_anchor auto-release
# ---------------------------------------------------------------------------


def _commit_evidence_packet(
    *,
    posted_at: str,
    sha: str,
    packet_id: str = "rev_pkt_commit",
) -> dict[str, object]:
    """Synthetic packet carrying typed commit evidence in target_revision."""
    return {
        "packet_id": packet_id,
        "kind": "finding",
        "status": "pending",
        "to_agent": "codex",
        "posted_at": posted_at,
        "target_revision": sha,
        "evidence_ref": f"commit:{sha}:claude-slice-evidence",
    }


def test_slice_counted_anchor_blocks_task_complete_with_zero_commits() -> None:
    """SLICE-Z: continuation_anchor release_mode=commit_count + 0 commits since posted_at -> typed pending blocker."""
    anchor = _anchor(
        packet_id="rev_pkt_slice_z",
        posted_at="2026-05-19T16:50:00+00:00",
        release_mode="commit_count",
        release_commit_count=2,
    )

    decision = task_complete_decision(
        session_id="session-1",
        packets=(anchor,),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_slice_counted_pending"


def test_slice_counted_anchor_blocks_task_complete_below_threshold() -> None:
    """SLICE-Z: 1 of 2 commits typed-after-anchor still blocks task_complete."""
    anchor = _anchor(
        packet_id="rev_pkt_slice_z",
        posted_at="2026-05-19T16:50:00+00:00",
        release_mode="commit_count",
        release_commit_count=2,
    )
    commit_a = _commit_evidence_packet(
        posted_at="2026-05-19T17:00:00+00:00",
        sha="abc1234",
        packet_id="rev_pkt_commit_a",
    )

    decision = task_complete_decision(
        session_id="session-1",
        packets=(anchor, commit_a),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_slice_counted_pending"


def test_slice_counted_anchor_fails_closed_when_release_metadata_invalid() -> None:
    """SLICE-Z: missing/invalid release_commit_count fails closed (continue, not terminate)."""
    anchor = _anchor(
        packet_id="rev_pkt_slice_z_invalid",
        posted_at="2026-05-19T16:50:00+00:00",
        release_mode="commit_count",
    )

    decision = task_complete_decision(
        session_id="session-1",
        packets=(anchor,),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_slice_counted_invalid"


def test_slice_counted_anchor_passthrough_when_release_mode_absent() -> None:
    """SLICE-Z: anchor without release_mode is unaffected (preserves cycle 1 regression test)."""
    anchor = _anchor(
        packet_id="rev_pkt_legacy",
        posted_at="2026-05-19T16:50:00+00:00",
    )

    decision = task_complete_decision(
        session_id="session-1",
        packets=(anchor,),
        policy=SessionTerminationPolicy(),
        actor="codex",
    )

    assert decision.terminate is False
    assert decision.reason == "continuation_anchor_active"
