"""Focused tests for the bounded coordination/topology reducer."""

from __future__ import annotations

from dev.scripts.devctl.platform.coordination_topology import (
    build_coordination_topology_snapshot,
)
from dev.scripts.devctl.runtime.review_state_parser import review_state_from_payload
from dev.scripts.devctl.runtime.work_intake_models import (
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)


def _review_state(payload: dict[str, object]):
    state = review_state_from_payload(payload)
    assert state is not None
    return state


def test_coordination_topology_marks_bridge_runtime_participant_and_runtime_repair() -> None:
    state = _review_state(
        {
            "schema_version": 1,
            "command": "review-channel",
            "action": "status",
            "timestamp": "2026-04-08T00:00:00Z",
            "ok": True,
            "review_state": {
                "review": {"session_id": "session-1"},
                "queue": {"pending_total": 0},
                "current_session": {
                    "current_instruction_revision": "rev-1",
                    "implementer_ack_state": "current",
                    "implementer_session_state": "waiting_for_user_input",
                    "implementer_session_hint": "implementer is waiting for manual input",
                },
                "collaboration": {
                    "schema_version": 1,
                    "contract_id": "CollaborationSession",
                    "session_id": "session-1",
                    "status": "resumable",
                    "reviewer_mode": "single_agent",
                    "operator_mode": "manual",
                    "lead_agent": "codex",
                    "review_agent": "codex",
                    "coding_agent": "claude",
                    "current_slice": "continue",
                    "topology_mode": "single_agent",
                    "work_ownership_mode": "exclusive_slice",
                    "peer_review": {
                        "current_instruction": "continue",
                        "current_instruction_revision": "rev-1",
                        "open_findings": "none",
                        "implementer_status": "coding",
                        "implementer_ack": "ack",
                        "implementer_ack_state": "current",
                    },
                    "arbitration": {"status": "clear", "summary": "", "owner": "system"},
                    "restart": {
                        "status": "resumable",
                        "resumable": True,
                        "source": "session_metadata",
                    },
                    "ready_gates": [
                        {
                            "gate_id": "runtime_truth",
                            "status": "blocked",
                            "summary": "reviewer runtime is inactive",
                        }
                    ],
                    "role_assignments": [],
                    "participants": [
                        {
                            "agent_id": "claude",
                            "provider": "claude",
                            "role": "implementer",
                            "session_name": "claude-conductor",
                            "live": False,
                            "status": "configured",
                            "requested_worker_budget": 1,
                            "planned_lane_count": 2,
                        }
                    ],
                    "delegated_work": [],
                },
                "bridge": {
                    "reviewer_mode": "single_agent",
                    "effective_reviewer_mode": "single_agent",
                    "claude_conductor_active": True,
                },
                "attention": {
                    "status": "inactive",
                    "owner": "system",
                    "summary": "review loop is inactive",
                    "recommended_action": "resume reviewer runtime",
                    "recommended_command": "python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json",
                },
                "reviewer_runtime": {
                    "reviewer_mode": "single_agent",
                    "effective_reviewer_mode": "single_agent",
                    "reviewer_freshness": "overdue",
                    "stale_reason": "inactive",
                    "session_owner": {
                        "provider": "codex",
                        "session_name": "codex-conductor",
                    },
                },
            },
        }
    )

    snapshot = build_coordination_topology_snapshot(
        review_state=state,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="single_agent",
            authority_mode="self_directed",
            work_ownership_mode="exclusive_slice",
            sync_cadence_mode="continuous",
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
        ),
    )

    assert snapshot.active_participant_count == 1
    assert snapshot.active_participants[0].provider == "claude"
    assert snapshot.active_participants[0].live is True
    assert snapshot.active_participants[0].live_source == "bridge_runtime"
    assert snapshot.fanout_posture == "blocked_resync"
    assert snapshot.fanout_safe is False
    assert snapshot.resync_posture == "runtime_repair"


def test_coordination_topology_flags_duplicate_worktrees_as_conflict() -> None:
    state = _review_state(
        {
            "schema_version": 1,
            "command": "review-channel",
            "action": "status",
            "timestamp": "2026-04-08T00:00:00Z",
            "ok": True,
            "review_state": {
                "review": {"session_id": "session-1"},
                "queue": {"pending_total": 0},
                "current_session": {"implementer_ack_state": "current"},
                "collaboration": {
                    "schema_version": 1,
                    "contract_id": "CollaborationSession",
                    "session_id": "session-1",
                    "status": "live",
                    "reviewer_mode": "active_dual_agent",
                    "operator_mode": "manual",
                    "lead_agent": "codex",
                    "review_agent": "codex",
                    "coding_agent": "claude",
                    "current_slice": "continue",
                    "topology_mode": "multi_agent_orchestrated",
                    "work_ownership_mode": "concurrent_writer_conflict",
                    "peer_review": {
                        "current_instruction": "continue",
                        "current_instruction_revision": "rev-1",
                        "open_findings": "none",
                        "implementer_status": "coding",
                        "implementer_ack": "ack",
                        "implementer_ack_state": "current",
                    },
                    "arbitration": {"status": "clear", "summary": "", "owner": "system"},
                    "restart": {"status": "live", "resumable": True, "source": "session_metadata"},
                    "ready_gates": [],
                    "role_assignments": [],
                    "participants": [
                        {
                            "agent_id": "codex",
                            "provider": "codex",
                            "role": "reviewer",
                            "live": True,
                            "status": "live",
                            "requested_worker_budget": 1,
                            "planned_lane_count": 1,
                        },
                        {
                            "agent_id": "claude",
                            "provider": "claude",
                            "role": "implementer",
                            "live": True,
                            "status": "live",
                            "requested_worker_budget": 1,
                            "planned_lane_count": 1,
                        },
                    ],
                    "delegated_work": [
                        {
                            "receipt_id": "worker-1",
                            "agent_id": "codex-worker-1",
                            "provider": "codex",
                            "role": "implementer",
                            "owner_session": "codex",
                            "status": "live",
                            "live": True,
                            "lane": "AGENT-1",
                            "worktree": "../codex-voice-wt-a1",
                        },
                        {
                            "receipt_id": "worker-2",
                            "agent_id": "claude-worker-1",
                            "provider": "claude",
                            "role": "implementer",
                            "owner_session": "claude",
                            "status": "live",
                            "live": True,
                            "lane": "AGENT-2",
                            "worktree": "../codex-voice-wt-a1",
                        },
                    ],
                },
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                    "codex_conductor_active": True,
                    "claude_conductor_active": True,
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "healthy",
                    "recommended_action": "",
                    "recommended_command": "",
                },
                "reviewer_runtime": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                    "reviewer_freshness": "fresh",
                },
            },
        }
    )

    snapshot = build_coordination_topology_snapshot(
        review_state=state,
        ownership=WorkIntakeOwnershipState(
            status="concurrent_writer_activity",
            concurrent_writer_detected=True,
        ),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="multi_agent_orchestrated",
            authority_mode="reviewer_gated",
            work_ownership_mode="concurrent_writer_conflict",
            sync_cadence_mode="before_scope_change",
            duplicate_delegated_worktrees=("../codex-voice-wt-a1",),
            concurrent_writer_conflict_detected=True,
        ),
    )

    assert snapshot.fanout_posture == "blocked_conflict"
    assert snapshot.fanout_safe is False
    assert snapshot.recommended_topology == "role_authority_conflict"
    assert snapshot.duplicate_delegated_worktrees == ("../codex-voice-wt-a1",)
    assert snapshot.delegated_worktrees[0].duplicate_worktree is True


def test_coordination_topology_uses_generic_typed_role_occupancy_label() -> None:
    state = _review_state(
        {
            "schema_version": 1,
            "command": "review-channel",
            "action": "status",
            "timestamp": "2026-04-08T00:00:00Z",
            "ok": True,
            "review_state": {
                "review": {"session_id": "session-1"},
                "queue": {"pending_total": 0},
                "current_session": {"implementer_ack_state": "current"},
                "collaboration": {
                    "schema_version": 1,
                    "contract_id": "CollaborationSession",
                    "session_id": "session-1",
                    "status": "live",
                    "reviewer_mode": "active_dual_agent",
                    "operator_mode": "manual",
                    "lead_agent": "",
                    "review_agent": "",
                    "coding_agent": "",
                    "current_slice": "continue",
                    "peer_review": {
                        "current_instruction": "continue",
                        "current_instruction_revision": "rev-1",
                        "open_findings": "none",
                        "implementer_status": "coding",
                        "implementer_ack": "ack",
                        "implementer_ack_state": "current",
                    },
                    "arbitration": {"status": "clear", "summary": "", "owner": "system"},
                    "restart": {"status": "live", "resumable": True, "source": "session_metadata"},
                    "ready_gates": [],
                    "role_assignments": [
                        {
                            "agent_id": "codex",
                            "provider": "codex",
                            "role_id": "TDDFirstRole",
                            "live": True,
                        },
                        {
                            "agent_id": "claude",
                            "provider": "claude",
                            "role_id": "dogfooder",
                            "live": True,
                        },
                    ],
                    "participants": [],
                    "delegated_work": [],
                },
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                    "active_conductor_providers": ["codex", "claude"],
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "healthy",
                    "recommended_action": "",
                    "recommended_command": "",
                },
                "reviewer_runtime": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                    "reviewer_freshness": "fresh",
                },
            },
        }
    )

    snapshot = build_coordination_topology_snapshot(
        review_state=state,
        ownership=WorkIntakeOwnershipState(status="clear"),
        coordination=WorkIntakeCoordinationState(),
    )

    assert snapshot.collaboration_topology == (
        "typed_role_topology[dogfood_test:claude;tdd_first_role:codex]"
    )
    assert tuple(row.role for row in snapshot.active_participants) == (
        "dogfood_test",
        "tdd_first_role",
    )


def test_coordination_topology_marks_live_fanout_ready_when_workers_are_isolated() -> None:
    state = _review_state(
        {
            "schema_version": 1,
            "command": "review-channel",
            "action": "status",
            "timestamp": "2026-04-08T00:00:00Z",
            "ok": True,
            "review_state": {
                "review": {"session_id": "session-1"},
                "queue": {"pending_total": 0},
                "current_session": {"implementer_ack_state": "current"},
                "collaboration": {
                    "schema_version": 1,
                    "contract_id": "CollaborationSession",
                    "session_id": "session-1",
                    "status": "live",
                    "reviewer_mode": "active_dual_agent",
                    "operator_mode": "manual",
                    "lead_agent": "codex",
                    "review_agent": "codex",
                    "coding_agent": "claude",
                    "current_slice": "continue",
                    "topology_mode": "multi_agent_orchestrated",
                    "work_ownership_mode": "shared_slice",
                    "peer_review": {
                        "current_instruction": "continue",
                        "current_instruction_revision": "rev-1",
                        "open_findings": "none",
                        "implementer_status": "coding",
                        "implementer_ack": "ack",
                        "implementer_ack_state": "current",
                    },
                    "arbitration": {"status": "clear", "summary": "", "owner": "system"},
                    "restart": {"status": "live", "resumable": True, "source": "session_metadata"},
                    "ready_gates": [
                        {
                            "gate_id": "delegated_work",
                            "status": "ready",
                            "summary": "delegated lanes are isolated",
                        }
                    ],
                    "role_assignments": [],
                    "participants": [
                        {
                            "agent_id": "codex",
                            "provider": "codex",
                            "role": "reviewer",
                            "live": True,
                            "status": "live",
                            "requested_worker_budget": 1,
                            "planned_lane_count": 2,
                        },
                        {
                            "agent_id": "claude",
                            "provider": "claude",
                            "role": "implementer",
                            "live": True,
                            "status": "live",
                            "requested_worker_budget": 1,
                            "planned_lane_count": 2,
                        },
                    ],
                    "delegated_work": [
                        {
                            "receipt_id": "worker-1",
                            "agent_id": "codex-worker-1",
                            "provider": "codex",
                            "role": "implementer",
                            "owner_session": "codex",
                            "status": "live",
                            "live": True,
                            "lane": "AGENT-1",
                            "worktree": "../codex-voice-wt-a1",
                        }
                    ],
                },
                "bridge": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                    "codex_conductor_active": True,
                    "claude_conductor_active": True,
                },
                "attention": {
                    "status": "healthy",
                    "owner": "system",
                    "summary": "healthy",
                    "recommended_action": "",
                    "recommended_command": "",
                },
                "reviewer_runtime": {
                    "reviewer_mode": "active_dual_agent",
                    "effective_reviewer_mode": "active_dual_agent",
                    "reviewer_freshness": "fresh",
                },
            },
        }
    )

    snapshot = build_coordination_topology_snapshot(
        review_state=state,
        ownership=WorkIntakeOwnershipState(status="in_scope_dirty_paths"),
        coordination=WorkIntakeCoordinationState(
            collaboration_topology="multi_agent_orchestrated",
            authority_mode="reviewer_gated",
            work_ownership_mode="shared_slice",
            sync_cadence_mode="continuous",
        ),
    )

    assert snapshot.active_participant_count == 2
    assert snapshot.active_conductor_count == 2
    assert snapshot.planned_lane_count == 4
    assert snapshot.requested_worker_budget_total == 2
    assert snapshot.live_delegated_worker_count == 1
    assert snapshot.fanout_posture == "fanout_ready"
    assert snapshot.fanout_safe is True
    assert snapshot.recommended_topology == "multi_agent_orchestrated"
