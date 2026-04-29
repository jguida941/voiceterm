"""Focused tests for typed startup action routing."""

from __future__ import annotations

from dev.scripts.devctl.runtime.action_routing import (
    build_agent_lane_decision,
    build_startup_action_routing,
)
from dev.scripts.devctl.runtime.advisory_next_action_role_filter import (
    READ_ONLY_NEXT_COMMAND,
)


def test_build_startup_action_routing_prefers_work_intake_coordination_owner() -> None:
    payload = {
        "work_intake": {
            "coordination": {
                "authority_mode": "reviewer_gated",
                "work_ownership_mode": "shared_slice",
                "sync_cadence_mode": "before_scope_change",
                "implementation_permission": "active",
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


def test_build_startup_action_routing_filters_mutating_observer_command() -> None:
    decision = build_startup_action_routing(
        {
            "implementation_permission": "active",
            "coordination": {"resync_required": False},
        },
        next_command="python3 dev/scripts/devctl.py push --execute",
        caller_role="observer",
    )

    assert decision.next_command == READ_ONLY_NEXT_COMMAND
    assert "vcs.push" in decision.blocked_actions


def test_build_startup_action_routing_filters_runtime_control_observer_command() -> None:
    decision = build_startup_action_routing(
        {
            "implementation_permission": "blocked",
            "coordination": {"resync_required": True},
        },
        next_command=(
            "python3 dev/scripts/devctl.py review-channel --action ensure "
            "--follow --terminal none --format json --execution-mode markdown-bridge "
            "--follow-inactivity-timeout-seconds 0"
        ),
        caller_role="observer",
    )

    assert decision.next_command == READ_ONLY_NEXT_COMMAND


def test_agent_lane_separates_occupied_lane_from_granted_capabilities() -> None:
    decision = build_agent_lane_decision(
        caller_role="dashboard",
        occupied_lane="observer",
        granted_capabilities=("repo.commit", "approval.commit"),
    )

    payload = decision.to_dict()
    assert decision.lane == "dashboard"
    assert decision.occupied_lane == "observer"
    assert "repo.commit" in decision.granted_capabilities
    assert "vcs.commit" not in decision.permissions
    assert payload["lane"] == "dashboard"
    assert payload["occupied_lane"] == "observer"
    assert payload["granted_capabilities"] == ["repo.commit", "approval.commit"]


def test_build_startup_action_routing_blocks_when_work_intake_requires_resync() -> None:
    payload = {
        "work_intake": {
            "coordination": {
                "authority_mode": "reviewer_gated",
                "work_ownership_mode": "shared_slice",
                "sync_cadence_mode": "before_scope_change",
                "implementation_permission": "active",
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
    assert "implementation.edit" not in decision.allowed_actions
    assert "implementation.edit" in decision.intrinsic_allowed_actions
    assert decision.recovery_action == "coordination_resync"
    assert decision.escalation_action == "operator_resume_review_loop"
    assert decision.implementation_admissibility == "blocked"


def test_build_startup_action_routing_uses_work_intake_permission_not_top_level() -> None:
    payload = {
        "implementation_permission": "active",
        "work_intake": {
            "coordination": {
                "authority_mode": "reviewer_gated",
                "work_ownership_mode": "exclusive_slice",
                "sync_cadence_mode": "continuous",
                "implementation_permission": "blocked",
                "active_participants": ["codex:implementer"],
                "active_implementation_owner": "codex",
            }
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py startup-context --format summary",
    )

    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert decision.agent_lane.edit_gate.active_implementation_owner == "codex"


def test_build_startup_action_routing_uses_top_level_coordination_fallbacks() -> None:
    payload = {
        "implementation_permission": "blocked",
        "coordination": {
            "actors": [
                {
                    "actor_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "presence": "live",
                }
            ],
            "resync_required": True,
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py startup-context --format summary",
    )

    assert decision.agent_lane.edit_gate.active_implementation_owner == ""
    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions
    assert decision.recovery_action == "coordination_resync"
    assert decision.escalation_action == "operator_resume_review_loop"
    assert decision.implementation_admissibility == "blocked"


def test_build_startup_action_routing_blocks_when_coordination_permission_missing() -> None:
    payload = {
        "coordination": {
            "actors": [
                {
                    "actor_id": "claude",
                    "provider": "claude",
                    "role": "implementer",
                    "presence": "live",
                }
            ],
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py startup-context --format summary",
    )

    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions
    assert decision.recovery_action == "refresh_startup_or_review_status"
    assert decision.escalation_action == "operator_resync_required"
    assert decision.implementation_admissibility == "blocked"


def test_build_startup_action_routing_blocks_when_owner_present_but_permission_missing() -> None:
    payload = {
        "work_intake": {
            "coordination": {
                "authority_mode": "reviewer_gated",
                "work_ownership_mode": "shared_slice",
                "sync_cadence_mode": "before_scope_change",
                "active_implementation_owner": "codex",
                "active_participants": ["codex:implementer"],
            }
        }
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py review-channel --action status",
    )

    assert decision.agent_lane.edit_gate.active_implementation_owner == "codex"
    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions
    assert decision.recovery_action == "refresh_startup_or_review_status"
    assert decision.escalation_action == "operator_resync_required"
    assert decision.implementation_admissibility == "blocked"


def test_build_startup_action_routing_blocks_on_checkpoint_gate() -> None:
    payload = {
        "implementation_permission": "active",
        "governance": {
            "push_enforcement": {
                "checkpoint_required": True,
                "safe_to_continue_editing": False,
            }
        }
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py startup-context --format summary",
    )

    assert decision.implementation_admissibility == "checkpoint_required"
    assert "implementation.edit" in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions
    assert decision.recovery_action == ""


def test_build_startup_action_routing_allows_checkpoint_commit_via_status_payload() -> None:
    payload = {
        "implementation_permission": "blocked",
        "observed_control_topology": "no_live_agents",
        "bridge_liveness": {
            "push_enforcement": {
                "checkpoint_required": True,
                "safe_to_continue_editing": False,
            }
        },
        "push_decision": {
            "action": "await_checkpoint",
        },
        "doctor": {
            "implementation_blocked": True,
            "implementation_block_reason": "review_loop_relaunch_required",
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command='python3 dev/scripts/devctl.py commit -m "checkpoint"',
    )

    assert "implementation.edit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions
    assert "vcs.stage" not in decision.blocked_actions
    assert "vcs.commit" not in decision.blocked_actions
    assert "vcs.stage" in decision.allowed_actions
    assert "vcs.commit" in decision.allowed_actions
