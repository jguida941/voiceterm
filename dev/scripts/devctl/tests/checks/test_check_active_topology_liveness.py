"""A16 RED slice: failing tests for the active-topology-liveness guard.

Per delete_after_ingest.md A16:
- G19 check_provider_pre_tool_hook_coverage
- G20 check_active_topology_liveness
- G21 check_reviewer_coding_route

The minimum RED scenario rev_pkt_4801 names is: Codex (reviewer) attempts
implementation mutation while Claude (implementer) has no current-row handoff
and Codex pre-tool hook coverage is unproven. This file pins that scenario as
a fixture and asserts the guard fires with the A16 machine-readable reasons.
"""

from __future__ import annotations

from typing import Any

import pytest

from dev.scripts.checks import check_active_topology_liveness as topo_guard
from dev.scripts.checks.check_active_topology_liveness import (
    ACTIVE_TOPOLOGY_NOT_LIVE_REASON,
    CHAT_VISIBILITY_WITHOUT_TYPED_PATH_REASON,
    COLLAPSED_REVIEWER_MODE_REASON,
    EXPIRED_SELECTED_ACTION_REQUEST_REASON,
    IMPLEMENTER_LANE_IDLE_REASON,
    MUTATION_OWNER_MISMATCH_REASON,
    PACKET_ATTENTION_BOOTSTRAP_LANE_MISSING_REASON,
    PACKET_BODY_OBSERVATION_ROUTE_MISSING_REASON,
    PROJECTION_DISAGREES_WITH_ROUTING_REASON,
    PROVIDER_HOOK_MISSING_REASON,
    PROVIDER_HOOK_UNPROVEN_REASON,
    REVIEWER_CODING_WITHOUT_HANDOFF_REASON,
    REVIEWER_ROUTE_LIFECYCLE_BLOCKED_REASON,
    REVIEWER_SPOOFED_BODY_OPEN_REASON,
    TYPED_HANDOFF_MISSING_REASON,
    build_report,
)
import pytest


CURRENT_ROW = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def _decision(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contract_id": "AgentLoopDecision",
        "actor_id": "codex",
        "actor_role": "reviewer",
        "session_id": "codex-session",
        "may_mutate": False,
        "can_run_next_command": False,
        "allowed_actions": [],
        "granted_capabilities": [],
        "source_latest_event_id": "rev_evt_85618",
    }
    payload.update(overrides)
    return payload


def _action(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action_kind": "implementation_edit",
        "command": "apply_patch dev/scripts/devctl/runtime/foo.py",
        "actor": "codex",
        "role": "reviewer",
        "session_id": "codex-session",
        "mutates": True,
        "writes_state": True,
    }
    payload.update(overrides)
    return payload


def _state(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "contract_id": "ReviewChannelState",
        "current_plan_row_id": CURRENT_ROW,
        "agent_loop_decision": _decision(),
        "attempted_action": _action(),
        "collaboration": {
            "mutation_owner": "claude",
            "reviewer_mode": "active_dual_agent",
        },
        "registry": {
            "providers": {
                "claude": {"pre_tool_hook_state": "hook_tested"},
                "codex": {"pre_tool_hook_state": "hook_missing"},
            }
        },
        "packets": [],
    }
    payload.update(overrides)
    return payload


def _reasons(report: dict[str, Any]) -> set[str]:
    return {str(v["reason"]) for v in report.get("violations", []) if isinstance(v, dict)}


def test_codex_reviewer_coding_without_claude_handoff_fails() -> None:
    """A16 minimum RED scenario named by rev_pkt_4801.

    Codex (reviewer) attempts mutation, Claude (implementer) has no current-row
    handoff in the packet queue, and Codex pre-tool hook coverage is unproven.
    """
    report = build_report(report_override=_state())

    assert report["ok"] is False
    reasons = _reasons(report)
    assert REVIEWER_CODING_WITHOUT_HANDOFF_REASON in reasons
    assert PROVIDER_HOOK_MISSING_REASON in reasons
    assert TYPED_HANDOFF_MISSING_REASON in reasons


def test_codex_hook_state_unproven_fails() -> None:
    """A16 G19: distinguish hook_missing from hook_unproven (config without test)."""
    state = _state(
        registry={
            "providers": {
                "claude": {"pre_tool_hook_state": "hook_tested"},
                "codex": {"pre_tool_hook_state": "hook_configured"},
            }
        },
        packets=[
            {
                "packet_id": "rev_pkt_4801",
                "to_agent": "claude",
                "target_role": "implementer",
                "kind": "action_request",
                "current_plan_row_id": CURRENT_ROW,
                "body_observed_at_utc": "2026-05-22T02:30:00Z",
                "acked_at_utc": "2026-05-22T02:30:05Z",
                "status": "applied",
            }
        ],
    )
    report = build_report(report_override=state)

    assert report["ok"] is False
    assert PROVIDER_HOOK_UNPROVEN_REASON in _reasons(report)


def test_implementer_lane_idle_when_no_implementer_role_present() -> None:
    """A16 G20: implementer_lane_idle_or_missing when topology lacks any implementer-role binding."""
    state = _state(
        collaboration={
            "mutation_owner": "",
            "reviewer_mode": "reviewer_only",
        },
        packets=[],
    )
    report = build_report(report_override=state)

    assert report["ok"] is False
    reasons = _reasons(report)
    assert IMPLEMENTER_LANE_IDLE_REASON in reasons


def test_mutation_owner_mismatch_fails() -> None:
    """A16 G20: mutation_owner=claude but reviewer (codex) attempts mutation."""
    report = build_report(report_override=_state())

    assert MUTATION_OWNER_MISMATCH_REASON in _reasons(report)


def test_topology_not_live_reason_summary_present() -> None:
    """Whenever any A16 sub-violation fires, an active_topology_not_live summary
    reason is also emitted so the gate has a single machine-readable handle.
    """
    report = build_report(report_override=_state())

    assert ACTIVE_TOPOLOGY_NOT_LIVE_REASON in _reasons(report)


def test_consumed_handoff_and_proven_hooks_pass() -> None:
    """Topology is live: Claude handoff body-opened+acked, both providers hook_tested."""
    state = _state(
        registry={
            "providers": {
                "claude": {"pre_tool_hook_state": "hook_tested"},
                "codex": {"pre_tool_hook_state": "hook_tested"},
            }
        },
        collaboration={
            "mutation_owner": "claude",
            "reviewer_mode": "active_dual_agent",
        },
        agent_loop_decision=_decision(
            actor_id="claude",
            actor_role="implementer",
            session_id="claude-session",
            may_mutate=True,
            allowed_actions=["implementation.edit"],
        ),
        attempted_action=_action(
            actor="claude",
            role="implementer",
            session_id="claude-session",
        ),
        packets=[
            {
                "packet_id": "rev_pkt_4801",
                "to_agent": "claude",
                "target_role": "implementer",
                "kind": "action_request",
                "current_plan_row_id": CURRENT_ROW,
                "body_observed_at_utc": "2026-05-22T02:30:00Z",
                "acked_at_utc": "2026-05-22T02:30:05Z",
                "status": "applied",
            }
        ],
    )
    report = build_report(report_override=state)

    assert report["ok"] is True, report


def test_handoff_pending_not_acked_still_fails() -> None:
    """Per A16: packet must be body_observed AND acked. Unconsumed = blocker."""
    state = _state(
        packets=[
            {
                "packet_id": "rev_pkt_4801",
                "to_agent": "claude",
                "target_role": "implementer",
                "kind": "action_request",
                "current_plan_row_id": CURRENT_ROW,
                "body_observed_at_utc": "",
                "acked_at_utc": "",
                "status": "pending",
            }
        ],
    )
    report = build_report(report_override=state)

    assert report["ok"] is False
    assert TYPED_HANDOFF_MISSING_REASON in _reasons(report)


def test_live_shape_with_packet_routing_and_registry_agents() -> None:
    """TDD-discovery binding: the guard must read the same defects from the live
    review-channel projection shape (registry.agents list, packets carrying
    plan_packet_routing.current_plan_row_id) that it reads from the fixture
    shape. Without this test the live dogfood would silently pass.
    """
    state = {
        "contract_id": "ReviewChannelState",
        "collaboration": {
            "mutation_owner": "claude",
            "reviewer_mode": "active_dual_agent",
        },
        "agent_loop_decision": _decision(
            actor_role="implementer",
            actor_id="claude",
            session_id="066d28ce-af03-4f1f-86ff-c285908c88a7",
        ),
        "registry": {
            "agents": [
                {"agent_id": "claude-impl", "provider": "claude"},
                {"agent_id": "codex-rev", "provider": "codex"},
            ]
        },
        "packets": [
            {
                "packet_id": "rev_pkt_9999",
                "to_agent": "claude",
                "target_role": "implementer",
                "kind": "action_request",
                "status": "pending",
                "packet_creation_binding": {
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            }
        ],
    }
    report = build_report(report_override=state)

    assert report["ok"] is False
    assert report["current_plan_row_id"] == CURRENT_ROW
    assert report["implementer_handoff_packet_id"] == "rev_pkt_9999"
    reasons = _reasons(report)
    assert PROVIDER_HOOK_MISSING_REASON in reasons
    assert ACTIVE_TOPOLOGY_NOT_LIVE_REASON in reasons


def _selected_handoff(reviewer="reviewer-actor", implementer="implementer-actor", **overrides):
    """Provider-neutral handoff fixture parameterized over (reviewer, implementer).

    Used by A17 tests so guard logic stays model-agnostic per the plan's
    A13 provider-neutral pivot.
    """
    packet = {
        "packet_id": "rev_pkt_a17_test",
        "from_agent": reviewer,
        "to_agent": implementer,
        "target_role": "implementer",
        "target_session_id": f"{implementer}-session",
        "kind": "action_request",
        "current_plan_row_id": CURRENT_ROW,
        "status": "pending",
        "delivery_emitted_at_utc": "2026-05-22T01:00:00Z",
        "body_observed_at_utc": "",
        "acked_at_utc": "",
        "expires_at_utc": "2026-05-29T00:00:00Z",
    }
    packet.update(overrides)
    return packet


def test_a17_delivery_emitted_without_body_open_fails() -> None:
    """A17 G23: packet delivered, target_session set, body_observed empty -> route missing."""
    state = _state(packets=[_selected_handoff()])
    report = build_report(report_override=state)
    assert report["ok"] is False
    assert PACKET_BODY_OBSERVATION_ROUTE_MISSING_REASON in _reasons(report)


def test_a17_reviewer_spoofed_body_open_fails() -> None:
    """A17 G23: body_observed_by is a reviewer role, not the target implementer."""
    state = _state(
        packets=[
            _selected_handoff(
                body_observed_at_utc="2026-05-22T01:30:00Z",
                body_observed_by="reviewer-actor",
                body_observed_role="reviewer",
                body_observed_session_id="reviewer-session",
                acked_at_utc="",
            )
        ]
    )
    report = build_report(report_override=state)
    assert report["ok"] is False
    assert REVIEWER_SPOOFED_BODY_OPEN_REASON in _reasons(report)


def test_a17_expired_action_request_without_refresh_fails() -> None:
    """A17 G24: expired action_request with no refresh packet referencing it."""
    state = _state(
        now_utc="2026-05-22T03:00:00Z",
        packets=[
            _selected_handoff(
                packet_id="rev_pkt_expired",
                expires_at_utc="2026-05-22T01:00:00Z",
                delivery_emitted_at_utc="2026-05-22T00:00:00Z",
            )
        ],
    )
    report = build_report(report_override=state)
    assert report["ok"] is False
    assert EXPIRED_SELECTED_ACTION_REQUEST_REASON in _reasons(report)


def test_a17_expired_action_request_with_typed_refresh_passes_g24() -> None:
    """A17 G24: a refresh packet that names the expired packet in evidence_refs absolves G24."""
    state = _state(
        now_utc="2026-05-22T03:00:00Z",
        registry={
            "providers": {
                "claude": {"pre_tool_hook_state": "hook_tested"},
                "codex": {"pre_tool_hook_state": "hook_tested"},
            }
        },
        agent_loop_decision=_decision(
            actor_id="implementer-actor",
            actor_role="implementer",
            session_id="implementer-actor-session",
            may_mutate=True,
            allowed_actions=["implementation.edit"],
        ),
        attempted_action=_action(
            actor="implementer-actor",
            role="implementer",
            session_id="implementer-actor-session",
        ),
        collaboration={
            "mutation_owner": "implementer-actor",
            "reviewer_mode": "active_dual_agent",
        },
        packets=[
            _selected_handoff(
                packet_id="rev_pkt_expired",
                expires_at_utc="2026-05-22T01:00:00Z",
            ),
            _selected_handoff(
                packet_id="rev_pkt_refresh",
                expires_at_utc="2026-05-29T00:00:00Z",
                body_observed_at_utc="2026-05-22T02:00:00Z",
                body_observed_by="implementer-actor",
                body_observed_role="implementer",
                body_observed_session_id="implementer-actor-session",
                acked_at_utc="2026-05-22T02:00:05Z",
                status="applied",
                evidence_refs=["packet:rev_pkt_expired"],
            ),
        ],
    )
    report = build_report(report_override=state)
    reasons = _reasons(report)
    assert EXPIRED_SELECTED_ACTION_REQUEST_REASON not in reasons


def test_a17_chat_visibility_without_typed_path_emits_blocker() -> None:
    """A17 G25: when chat reveals body but no typed lifecycle path exists, blocker fires."""
    state = _state(
        collaboration={
            "mutation_owner": "claude",
            "reviewer_mode": "active_dual_agent",
            "chat_body_visible_for_handoff": True,
        },
        packets=[_selected_handoff()],
    )
    report = build_report(report_override=state)
    assert report["ok"] is False
    assert CHAT_VISIBILITY_WITHOUT_TYPED_PATH_REASON in _reasons(report)


def test_a17_consumed_handoff_silences_a17_reasons() -> None:
    """When body-open + ack are recorded by the target session, no A17 violations fire."""
    state = _state(
        registry={
            "providers": {
                "claude": {"pre_tool_hook_state": "hook_tested"},
                "codex": {"pre_tool_hook_state": "hook_tested"},
            }
        },
        agent_loop_decision=_decision(
            actor_id="implementer-actor",
            actor_role="implementer",
            session_id="implementer-actor-session",
            may_mutate=True,
            allowed_actions=["implementation.edit"],
        ),
        attempted_action=_action(
            actor="implementer-actor",
            role="implementer",
            session_id="implementer-actor-session",
        ),
        collaboration={
            "mutation_owner": "implementer-actor",
            "reviewer_mode": "active_dual_agent",
        },
        packets=[
            _selected_handoff(
                body_observed_at_utc="2026-05-22T01:30:00Z",
                body_observed_by="implementer-actor",
                body_observed_role="implementer",
                body_observed_session_id="implementer-actor-session",
                acked_at_utc="2026-05-22T01:30:05Z",
                status="applied",
            )
        ],
    )
    report = build_report(report_override=state)
    a17_reasons = {
        PACKET_BODY_OBSERVATION_ROUTE_MISSING_REASON,
        REVIEWER_SPOOFED_BODY_OPEN_REASON,
        EXPIRED_SELECTED_ACTION_REQUEST_REASON,
        CHAT_VISIBILITY_WITHOUT_TYPED_PATH_REASON,
    }
    assert not (_reasons(report) & a17_reasons), _reasons(report)


def test_future_row_note_packet_not_selected_as_handoff() -> None:
    """rev_pkt_4808 finding #1: future_row_note packets must NOT be picked as the
    current-row implementer handoff even if they were created while this row was
    the system's current row. The discriminator is classification + target_plan_row_id.
    """
    state = _state(
        packets=[
            {
                "packet_id": "rev_pkt_future",
                "to_agent": "claude",
                "target_role": "implementer",
                "kind": "action_request",
                "status": "pending",
                "delivery_emitted_at_utc": "2026-05-22T01:00:00Z",
                "packet_creation_binding": {
                    "plan_packet_routing": {
                        "classification": "future_row_note",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": "MP-NEW-P204-S1",
                    }
                },
            }
        ],
    )
    report = build_report(report_override=state)

    assert report["implementer_handoff_packet_id"] == ""
    assert report["ok"] is False
    reasons = _reasons(report)
    assert TYPED_HANDOFF_MISSING_REASON in reasons
    assert PACKET_BODY_OBSERVATION_ROUTE_MISSING_REASON not in reasons


def test_pending_handoff_fires_typed_missing_without_attempted_action() -> None:
    """rev_pkt_4808 finding #2: pending unconsumed handoff must violate independent of
    an attempted_action. Otherwise a fixed hook registry would let the guard pass
    while the body-open lifecycle is still broken.
    """
    state = {
        "contract_id": "ReviewChannelState",
        "current_plan_row_id": CURRENT_ROW,
        "collaboration": {
            "mutation_owner": "implementer-actor",
            "reviewer_mode": "active_dual_agent",
        },
        "registry": {
            "providers": {
                "impl-provider": {"pre_tool_hook_state": "hook_tested"},
                "review-provider": {"pre_tool_hook_state": "hook_tested"},
            }
        },
        "agent_loop_decision": _decision(
            actor_id="implementer-actor",
            actor_role="implementer",
            session_id="implementer-actor-session",
        ),
        "packets": [
            _selected_handoff(
                packet_creation_binding={
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            )
        ],
    }
    report = build_report(report_override=state)

    assert report["ok"] is False
    reasons = _reasons(report)
    assert TYPED_HANDOFF_MISSING_REASON in reasons


def test_a17_archived_packet_not_selected_as_handoff() -> None:
    """rev_pkt_4810 review finding: archived/expired packets must NOT be picked
    as the active handoff, even when they're same_row_blocker for this row.
    """
    state = _state(
        now_utc="2026-05-22T03:00:00Z",
        packets=[
            _selected_handoff(
                packet_id="rev_pkt_archived",
                status="archived",
                lifecycle_current_state="archived",
                disposition={
                    "sink": "archived",
                    "status": "archived",
                },
                expires_at_utc="2026-05-21T22:30:17Z",
                packet_creation_binding={
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            )
        ],
    )
    report = build_report(report_override=state)
    assert report["implementer_handoff_packet_id"] == ""
    assert TYPED_HANDOFF_MISSING_REASON in _reasons(report)


def test_a17_expired_at_utc_excludes_from_handoff() -> None:
    """rev_pkt_4810: expired_at_utc in the past must exclude packet from handoff
    selection even if status is still pending (clock drift / unreaped packets).
    """
    state = _state(
        now_utc="2026-05-22T03:00:00Z",
        packets=[
            _selected_handoff(
                packet_id="rev_pkt_clock_drift",
                status="pending",
                expires_at_utc="2026-05-22T01:00:00Z",
                packet_creation_binding={
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            )
        ],
    )
    report = build_report(report_override=state)
    assert report["implementer_handoff_packet_id"] == ""


def test_a17_session_mismatch_excludes_from_handoff() -> None:
    """rev_pkt_4810: packet whose target_session_id names a DIFFERENT session
    than the active implementer must NOT be selected — that's a historical packet.
    """
    state = {
        "contract_id": "ReviewChannelState",
        "current_plan_row_id": CURRENT_ROW,
        "collaboration": {
            "mutation_owner": "implementer-actor",
            "reviewer_mode": "active_dual_agent",
        },
        "registry": {"agents": [{"agent_id": "impl", "provider": "impl-provider"}]},
        "agent_loop_decisions": [
            _decision(
                actor_id="implementer-actor",
                actor_role="implementer",
                session_id="active-session-NEW",
            )
        ],
        "packets": [
            _selected_handoff(
                packet_id="rev_pkt_historical_session",
                target_session_id="historical-session-OLD",
                packet_creation_binding={
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            )
        ],
    }
    report = build_report(report_override=state)
    assert report["implementer_handoff_packet_id"] == ""


def test_a17_g24_live_shape_no_now_utc_still_filters_expired() -> None:
    """rev_pkt_4811 finding: live latest.json has no ``now_utc`` field, but the
    guard must still exclude expired packets and emit G24 violations. The guard
    owns its own clock when state doesn't supply one.
    """
    state = {
        "contract_id": "ReviewChannelState",
        # NOTE: deliberately omit "now_utc" to mimic live latest.json
        "current_plan_row_id": CURRENT_ROW,
        "collaboration": {
            "mutation_owner": "implementer-actor",
            "reviewer_mode": "active_dual_agent",
        },
        "registry": {
            "agents": [{"agent_id": "impl", "provider": "impl-provider"}]
        },
        "agent_loop_decisions": [
            _decision(
                actor_id="implementer-actor",
                actor_role="implementer",
                session_id="implementer-actor-session",
            )
        ],
        "packets": [
            _selected_handoff(
                packet_id="rev_pkt_live_expired",
                status="pending",
                # expires_at_utc in 2024 — definitely before "now" whatever the clock
                expires_at_utc="2024-01-01T00:00:00Z",
                packet_creation_binding={
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            )
        ],
    }
    report = build_report(report_override=state)

    # Two invariants must both hold without an explicit now_utc:
    # 1. Expired packet is NOT selected as handoff.
    # 2. G24 expired_selected_action_request fires.
    assert report["implementer_handoff_packet_id"] == ""
    assert EXPIRED_SELECTED_ACTION_REQUEST_REASON in _reasons(report)


def test_a17_projection_disagrees_with_routing_emits_blocker() -> None:
    """rev_pkt_4813 finding: a projection that names a packet as 'canonical
    active' must agree with that packet's plan_packet_routing classification.
    Otherwise emit a typed blocker pointing at the source projection path.
    Aligning the source projection is owner-row work, NOT this slice.
    """
    state = _state(
        reviewer_runtime={
            "session_posture": {
                "actors": [
                    {"current_target": "rev_pkt_future_active"},
                ]
            }
        },
        agent_work_board={
            "rows": [
                {"active_packet_id": "rev_pkt_future_active"},
                {"active_packet_id": "rev_pkt_future_active"},
            ]
        },
        packets=[
            {
                "packet_id": "rev_pkt_future_active",
                "to_agent": "claude",
                "target_role": "implementer",
                "kind": "action_request",
                "status": "pending",
                "packet_creation_binding": {
                    "plan_packet_routing": {
                        "classification": "future_row_note",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": "MP-NEW-OTHER-S1",
                    }
                },
            }
        ],
    )
    report = build_report(report_override=state)

    assert report["ok"] is False
    reasons = _reasons(report)
    assert PROJECTION_DISAGREES_WITH_ROUTING_REASON in reasons
    detail = next(
        v["detail"]
        for v in report["violations"]
        if v["reason"] == PROJECTION_DISAGREES_WITH_ROUTING_REASON
    )
    # Must include the source projection path so the operator/reviewer can
    # locate the misaligned renderer.
    assert "reviewer_runtime.session_posture.actors[0].current_target" in detail \
        or "agent_work_board.rows[0].active_packet_id" in detail


def test_a17_projection_agrees_with_routing_does_not_emit() -> None:
    """When projections name a same_row_blocker packet for the current row,
    no projection-disagreement blocker fires.
    """
    state = _state(
        reviewer_runtime={
            "session_posture": {
                "actors": [{"current_target": "rev_pkt_aligned"}]
            }
        },
        packets=[
            _selected_handoff(
                packet_id="rev_pkt_aligned",
                packet_creation_binding={
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            )
        ],
    )
    report = build_report(report_override=state)
    assert PROJECTION_DISAGREES_WITH_ROUTING_REASON not in _reasons(report)


@pytest.mark.parametrize(
    "collapsed_mode",
    ["single_agent", "reviewer_only", "tools_only", "observer_dashboard_lane_read_only"],
)
def test_a16_g20_collapsed_reviewer_mode_fails_during_implementation_slice(
    collapsed_mode: str,
) -> None:
    """rev_pkt_4815: each collapsed reviewer_mode must fail when an
    implementation slice is active (handoff exists OR mutation attempted),
    even with mutation_owner set, proven hooks, and consumed handoff.
    """
    state = _state(
        registry={
            "providers": {
                "impl-provider": {"pre_tool_hook_state": "hook_tested"},
                "review-provider": {"pre_tool_hook_state": "hook_tested"},
            }
        },
        collaboration={
            "mutation_owner": "implementer-actor",
            "reviewer_mode": collapsed_mode,
        },
        agent_loop_decision=_decision(
            actor_id="implementer-actor",
            actor_role="implementer",
            session_id="implementer-actor-session",
            may_mutate=True,
            allowed_actions=["implementation.edit"],
        ),
        attempted_action=_action(
            actor="implementer-actor",
            role="implementer",
            session_id="implementer-actor-session",
        ),
        packets=[
            _selected_handoff(
                body_observed_at_utc="2026-05-22T03:00:00Z",
                body_observed_by="implementer-actor",
                body_observed_role="implementer",
                body_observed_session_id="implementer-actor-session",
                acked_at_utc="2026-05-22T03:00:05Z",
                status="applied",
                packet_creation_binding={
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            )
        ],
    )
    report = build_report(report_override=state)
    assert report["ok"] is False
    reasons = _reasons(report)
    assert COLLAPSED_REVIEWER_MODE_REASON in reasons
    # The detail must name the specific collapsed mode for debuggability.
    detail = next(
        v["detail"] for v in report["violations"]
        if v["reason"] == COLLAPSED_REVIEWER_MODE_REASON
    )
    assert collapsed_mode in detail


def test_a16_g20_collapsed_mode_with_typed_blocker_passes() -> None:
    """A typed blocker on collaboration.collapse_blockers for the named mode
    silences the violation (operator acknowledged the collapse).
    """
    state = _state(
        registry={
            "providers": {
                "impl-provider": {"pre_tool_hook_state": "hook_tested"},
                "review-provider": {"pre_tool_hook_state": "hook_tested"},
            }
        },
        collaboration={
            "mutation_owner": "implementer-actor",
            "reviewer_mode": "tools_only",
            "collapse_blockers": [
                {
                    "mode": "tools_only",
                    "blocker_ref": "packet:rev_pkt_collapse_ack_42",
                    "reason": "operator-approved temporary reviewer offline",
                }
            ],
        },
        agent_loop_decision=_decision(
            actor_id="implementer-actor",
            actor_role="implementer",
            session_id="implementer-actor-session",
            may_mutate=True,
            allowed_actions=["implementation.edit"],
        ),
        attempted_action=_action(
            actor="implementer-actor",
            role="implementer",
            session_id="implementer-actor-session",
        ),
        packets=[
            _selected_handoff(
                body_observed_at_utc="2026-05-22T03:00:00Z",
                body_observed_by="implementer-actor",
                body_observed_role="implementer",
                body_observed_session_id="implementer-actor-session",
                acked_at_utc="2026-05-22T03:00:05Z",
                status="applied",
                packet_creation_binding={
                    "plan_packet_routing": {
                        "classification": "same_row_blocker",
                        "current_plan_row_id": CURRENT_ROW,
                        "target_plan_row_id": CURRENT_ROW,
                    }
                },
            )
        ],
    )
    report = build_report(report_override=state)
    assert COLLAPSED_REVIEWER_MODE_REASON not in _reasons(report), report


def test_a16_g20_consumes_g19_inline_provider_hook_states() -> None:
    """rev_pkt_4820: when state.g19_provider_hook_states declares hook_configured
    for both providers, G20 must surface provider_pre_tool_hook_unproven (NOT
    missing), proving the topology guard composes G19's effective states.
    """
    state = _state(
        g19_provider_hook_states={
            "claude": "hook_configured",
            "codex": "hook_configured",
        },
        registry={"agents": [{"provider": "claude"}, {"provider": "codex"}]},
    )
    report = build_report(report_override=state)
    reasons = _reasons(report)
    assert PROVIDER_HOOK_UNPROVEN_REASON in reasons
    assert PROVIDER_HOOK_MISSING_REASON not in reasons


def test_a16_g20_g19_tested_states_silence_provider_hook_violations() -> None:
    """When G19 derivation says all providers are hook_tested, the topology
    guard must emit NO provider hook violations.
    """
    state = _state(
        g19_provider_hook_states={
            "claude": "hook_tested",
            "codex": "hook_tested",
        },
        registry={"providers": {}},
    )
    report = build_report(report_override=state)
    reasons = _reasons(report)
    assert PROVIDER_HOOK_UNPROVEN_REASON not in reasons
    assert PROVIDER_HOOK_MISSING_REASON not in reasons


def test_a16_g20_g19_stronger_state_overrides_weaker_registry_state() -> None:
    """rev_pkt_4821: when the registry projection declares hook_configured for
    a provider but G19 has stronger hook_tested evidence, G20 must adopt the
    stronger state. Fixing only blanks (the previous bug) would keep the
    weaker hook_configured and emit a spurious unproven violation.
    """
    state = _state(
        g19_provider_hook_states={"codex": "hook_tested"},
        registry={
            "providers": {
                "claude": {"pre_tool_hook_state": "hook_tested"},
                "codex": {"pre_tool_hook_state": "hook_configured"},
            }
        },
    )
    report = build_report(report_override=state)
    states_map = {
        s["actor"]: s["detail"]
        for s in report.get("violations", [])
        if isinstance(s, dict) and s.get("actor")
    }
    # No unproven violation for codex — the stronger hook_tested wins.
    codex_unproven = [
        v for v in report["violations"]
        if v["reason"] == PROVIDER_HOOK_UNPROVEN_REASON
        and v.get("actor") == "codex"
    ]
    assert codex_unproven == [], report["violations"]
    assert report["provider_hook_states"]["codex"] == "hook_tested"


def test_a16_g20_g19_weaker_state_does_not_demote_stronger_registry_state() -> None:
    """Symmetric: registry hook_tested + G19 hook_configured must keep hook_tested.
    Precedence is one-directional — never demote a stronger registry value.
    """
    state = _state(
        g19_provider_hook_states={"codex": "hook_configured"},
        registry={
            "providers": {
                "codex": {"pre_tool_hook_state": "hook_tested"},
            }
        },
    )
    report = build_report(report_override=state)
    assert report["provider_hook_states"]["codex"] == "hook_tested"


def test_a17_g26_reviewer_review_accepted_blocked_by_body_open_required() -> None:
    """rev_pkt_4821 followup / A17 G26: a reviewer-session post of
    review_accepted with valid control-decision input, rejected by
    body_open_required, must surface as reviewer_route_lifecycle_blocked.
    """
    state = _state(
        attempted_action_receipts=[
            {
                "receipt_id": "attempted_action:review-channel.post:9d5a89b4110bd915",
                "action_kind": "review-channel.post",
                "actor": "codex",
                "role": "reviewer",
                "packet_kind": "review_accepted",
                "rejection_reason": "body_open_required",
                "source_decision_id": "agent-runtime-clock:rev_evt_99999",
            }
        ],
    )
    report = build_report(report_override=state)
    assert report["ok"] is False
    reasons = _reasons(report)
    assert REVIEWER_ROUTE_LIFECYCLE_BLOCKED_REASON in reasons
    detail = next(
        v["detail"] for v in report["violations"]
        if v["reason"] == REVIEWER_ROUTE_LIFECYCLE_BLOCKED_REASON
    )
    # Detail must name the supported next transition so the reviewer route
    # is observable, not silent.
    assert "task_blocked" in detail.lower() or "next transition" in detail.lower()


def test_a17_g26_implementer_post_does_not_trigger_reviewer_route_blocker() -> None:
    """An implementer-role attempted_action must NOT trigger the reviewer-route
    blocker even when rejected by body_open_required.
    """
    state = _state(
        attempted_action_receipts=[
            {
                "receipt_id": "attempted_action:review-channel.post:implementer-foo",
                "action_kind": "review-channel.post",
                "actor": "claude",
                "role": "implementer",
                "packet_kind": "task_progress",
                "rejection_reason": "body_open_required",
                "source_decision_id": "agent-runtime-clock:rev_evt_99999",
            }
        ],
    )
    report = build_report(report_override=state)
    assert REVIEWER_ROUTE_LIFECYCLE_BLOCKED_REASON not in _reasons(report)


def test_a17_g26_reviewer_without_control_decision_input_does_not_trigger() -> None:
    """Without valid control-decision input the rejection is the prior G7
    blocker (no_control_decision_input), not the body-open route blocker.
    G26 specifically targets the route gap where the input IS valid.
    """
    state = _state(
        attempted_action_receipts=[
            {
                "receipt_id": "attempted_action:review-channel.post:no-cdi",
                "action_kind": "review-channel.post",
                "actor": "codex",
                "role": "reviewer",
                "packet_kind": "review_accepted",
                "rejection_reason": "body_open_required",
                # no source_decision_id / control-decision-input on this receipt
            }
        ],
    )
    report = build_report(report_override=state)
    assert REVIEWER_ROUTE_LIFECYCLE_BLOCKED_REASON not in _reasons(report)


def test_a17_g26_argv_form_with_kind_and_control_decision_flag() -> None:
    """The detector must also recognize argv-form receipts where ``--kind`` and
    ``--control-decision-input`` are tokens rather than top-level fields.
    """
    state = _state(
        attempted_action_receipts=[
            {
                "receipt_id": "attempted_action:review-channel.post:argv-form",
                "action_kind": "review-channel.post",
                "actor": "codex",
                "role": "reviewer",
                "argv": [
                    "review-channel",
                    "--action",
                    "post",
                    "--kind",
                    "review_accepted",
                    "--control-decision-input",
                    "/tmp/codex_decision.json",
                ],
                "rejection_reason": "non_body_open_action_after_body_open_required",
            }
        ],
    )
    report = build_report(report_override=state)
    reasons = _reasons(report)
    assert REVIEWER_ROUTE_LIFECYCLE_BLOCKED_REASON in reasons


def test_a17_g29_body_open_required_with_empty_lane_emits_blocker() -> None:
    """rev_pkt_4822 / G29 RED: claude implementer decision with
    packet_body_open_required + concrete next_command + lane=None +
    allowed_actions=[] must surface as packet_attention_bootstrap_lane_missing.
    Reproduces the exact live shape codex named: rev_pkt_4821 / rev_evt_85697.
    """
    state = _state(
        agent_loop_decisions=[
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "claude",
                "actor_role": "implementer",
                "session_id": "066d28ce-af03-4f1f-86ff-c285908c88a7",
                "loop_state": "blocked",
                "lifecycle_state": "needs_attention",
                "decision": "run_next_command",
                "reason_code": "packet_body_open_required",
                "next_command": (
                    "review-channel --action show --packet-id rev_pkt_4821 "
                    "--actor claude --actor-role implementer "
                    "--session-id 066d28ce-af03-4f1f-86ff-c285908c88a7"
                ),
                "lane": None,
                "agent_lane": None,
                "allowed_actions": [],
                "may_mutate": False,
                "advance_allowed": True,
            }
        ],
    )
    report = build_report(report_override=state)
    assert report["ok"] is False
    reasons = _reasons(report)
    assert PACKET_ATTENTION_BOOTSTRAP_LANE_MISSING_REASON in reasons


def test_a17_g29_semantic_ingestion_required_with_empty_lane_emits_blocker() -> None:
    """G29: same shape but post-body-open the gate becomes semantic_ingestion."""
    state = _state(
        agent_loop_decisions=[
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "claude",
                "actor_role": "implementer",
                "session_id": "066d28ce-af03-4f1f-86ff-c285908c88a7",
                "reason_code": "packet_semantic_ingestion_required",
                "next_command": (
                    "review-channel --action ingest --packet-id rev_pkt_4821 "
                    "--actor claude --actor-role implementer"
                ),
                "lane": None,
                "agent_lane": None,
                "allowed_actions": [],
            }
        ],
    )
    report = build_report(report_override=state)
    assert PACKET_ATTENTION_BOOTSTRAP_LANE_MISSING_REASON in _reasons(report)


def test_a17_g29_non_packet_attention_reason_does_not_trigger() -> None:
    """G29 must only fire for packet-attention reason_codes. Other reasons
    (e.g. mutation_owner_mismatch) with empty lanes are different defects.
    """
    state = _state(
        agent_loop_decisions=[
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "claude",
                "actor_role": "implementer",
                "reason_code": "operator_resync_required",
                "next_command": "devctl session --role implementer",
                "lane": None,
                "allowed_actions": [],
            }
        ],
    )
    report = build_report(report_override=state)
    assert PACKET_ATTENTION_BOOTSTRAP_LANE_MISSING_REASON not in _reasons(report)


def test_a17_g29_grant_for_command_clears_blocker() -> None:
    """G29 GREEN shape: when allowed_actions includes a sanctioned packet-
    attention action, the bootstrap blocker does NOT fire. Proves the guard
    silences correctly when the reducer is patched.
    """
    state = _state(
        agent_loop_decisions=[
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "claude",
                "actor_role": "implementer",
                "reason_code": "packet_body_open_required",
                "next_command": "review-channel --action show --packet-id rev_pkt_4821",
                "lane": "implementer",
                "allowed_actions": ["review-channel.show_packet"],
            }
        ],
    )
    report = build_report(report_override=state)
    assert PACKET_ATTENTION_BOOTSTRAP_LANE_MISSING_REASON not in _reasons(report)


def test_machine_readable_reasons_are_stable() -> None:
    """Pin the public reason strings so router/policy can reference them."""
    assert ACTIVE_TOPOLOGY_NOT_LIVE_REASON == "active_topology_not_live"
    assert IMPLEMENTER_LANE_IDLE_REASON == "implementer_lane_idle_or_missing"
    assert MUTATION_OWNER_MISMATCH_REASON == "mutation_owner_mismatch"
    assert PROVIDER_HOOK_MISSING_REASON == "provider_pre_tool_hook_missing"
    assert PROVIDER_HOOK_UNPROVEN_REASON == "provider_pre_tool_hook_unproven"
    assert REVIEWER_CODING_WITHOUT_HANDOFF_REASON == "reviewer_coding_instead_of_implementer_handoff"
    assert TYPED_HANDOFF_MISSING_REASON == "typed_collaboration_handoff_missing"
    assert (
        PACKET_BODY_OBSERVATION_ROUTE_MISSING_REASON == "packet_body_observation_route_missing"
    )
    assert REVIEWER_SPOOFED_BODY_OPEN_REASON == "reviewer_spoofs_implementer_body_open"
    assert EXPIRED_SELECTED_ACTION_REQUEST_REASON == "expired_selected_action_request"
    assert (
        CHAT_VISIBILITY_WITHOUT_TYPED_PATH_REASON == "chat_visibility_without_typed_lifecycle_path"
    )
