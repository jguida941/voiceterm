"""Focused tests for typed startup action routing."""

from __future__ import annotations

from dev.scripts.devctl.runtime.action_routing import build_startup_action_routing


def test_build_startup_action_routing_prefers_work_intake_coordination_owner() -> None:
    payload = {
        "work_intake": {
            "coordination": {
                "authority_mode": "reviewer_gated",
                "work_ownership_mode": "shared_slice",
                "sync_cadence_mode": "before_scope_change",
                "active_implementation_owner": "codex",
                "active_participants": ["codex:implementer"],
            }
        },
        "coordination": {
            "actors": [
                {
                    "actor_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "presence": "live",
                }
            ]
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py review-channel --action status",
        caller_role="dashboard",
    )

    assert decision.agent_lane.edit_gate.active_implementation_owner == "codex"
    assert decision.agent_lane.edit_gate.reason == (
        "active_implementation_lane_owned_by_other_agent"
    )


def test_build_startup_action_routing_blocks_when_work_intake_requires_resync() -> None:
    payload = {
        "work_intake": {
            "coordination": {
                "authority_mode": "reviewer_gated",
                "work_ownership_mode": "shared_slice",
                "sync_cadence_mode": "before_scope_change",
                "active_participants": ["codex:implementer"],
                "active_implementation_owner": "codex",
                "resync_required": True,
            }
        }
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py review-channel --action status",
    )

    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "review-channel.status" in decision.allowed_actions
    assert decision.recovery_action == "coordination_resync"
    assert decision.escalation_action == "operator_resume_review_loop"
