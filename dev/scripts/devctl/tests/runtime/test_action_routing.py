"""Focused tests for typed startup action routing."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.runtime.action_routing import (
    build_agent_lane_decision,
    build_startup_action_routing,
)
from dev.scripts.devctl.runtime.action_routing_publication_defer import (
    DEFER_SAFE_CHECKPOINT_REASONS,
    PublicationDeferInput,
    publication_defer_decision,
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


def test_defer_publication_reallows_editing_when_publication_is_pending() -> None:
    payload = {
        "advisory_action": "push_allowed",
        "push_decision": {
            "action": "run_devctl_push",
            "next_step_command": "python3 dev/scripts/devctl.py push --execute",
        },
        "governance": {
            "push_enforcement": {
                "checkpoint_required": False,
                "safe_to_continue_editing": True,
                "ahead_of_upstream_commits": 3,
                "recommended_action": "use_devctl_push",
            }
        },
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
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py push --execute",
        defer_publication=True,
    )

    assert decision.publication_deferred_active is True
    assert decision.publication_deferred_reason == "publication_deferred_for_development"
    assert decision.implementation_admissibility == "allowed"
    assert "implementation.edit" in decision.allowed_actions
    assert "implementation.edit" not in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions
    assert (
        decision.deferred_publication_command
        == "python3 dev/scripts/devctl.py push --execute"
    )
    assert decision.to_dict()["deferred_publication_actions"] == [
        "vcs.stage",
        "vcs.commit",
        "vcs.push",
    ]


def test_defer_publication_reallows_editing_when_tools_only_loop_is_inactive() -> None:
    payload = {
        "observed_control_topology": "no_live_agents",
        "reviewer_mode": "tools_only",
        "effective_reviewer_mode": "tools_only",
        "advisory_action": "push_allowed",
        "push_decision": {
            "action": "run_devctl_push",
            "next_step_command": "python3 dev/scripts/devctl.py push --execute",
        },
        "governance": {
            "push_enforcement": {
                "checkpoint_required": False,
                "safe_to_continue_editing": True,
                "worktree_dirty": False,
                "dirty_path_count": 0,
                "untracked_path_count": 0,
                "ahead_of_upstream_commits": 22,
                "recommended_action": "use_devctl_push",
            }
        },
        "work_intake": {
            "coordination": {
                "authority_mode": "review_gated",
                "work_ownership_mode": "exclusive_slice",
                "sync_cadence_mode": "before_publish",
                "implementation_permission": "blocked",
                "resync_required": True,
            }
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py push --execute",
        caller_role="implementer",
        defer_publication=True,
    )

    assert decision.publication_deferred_active is True
    assert decision.implementation_admissibility == "allowed"
    assert "implementation.edit" in decision.allowed_actions
    assert "implementation.edit" not in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions


def test_defer_publication_does_not_override_stale_active_dual_agent_loop() -> None:
    payload = {
        "observed_control_topology": "no_live_agents",
        "reviewer_mode": "active_dual_agent",
        "effective_reviewer_mode": "active_dual_agent",
        "advisory_action": "push_allowed",
        "push_decision": {"action": "run_devctl_push"},
        "governance": {
            "push_enforcement": {
                "checkpoint_required": False,
                "safe_to_continue_editing": True,
                "ahead_of_upstream_commits": 3,
            }
        },
        "work_intake": {
            "coordination": {
                "implementation_permission": "blocked",
                "resync_required": True,
            }
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py push --execute",
        caller_role="implementer",
        defer_publication=True,
    )

    assert decision.publication_deferred_active is False
    assert "implementation.edit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions


def test_defer_publication_reallows_dirty_edit_only_implementer_lane() -> None:
    payload = {
        "observed_control_topology": "implementer_without_reviewer",
        "reviewer_mode": "tools_only",
        "effective_reviewer_mode": "tools_only",
        "advisory_action": "checkpoint_before_continue",
        "push_decision": {
            "action": "await_checkpoint",
            "reason": "worktree_dirty",
            "next_step_command": 'python3 dev/scripts/devctl.py commit -m "checkpoint"',
        },
        "governance": {
            "push_enforcement": {
                "checkpoint_required": False,
                "safe_to_continue_editing": True,
                "worktree_dirty": True,
                "dirty_path_count": 7,
                "unstaged_path_count": 7,
                "untracked_path_count": 0,
                "staged_path_count": 0,
                "pending_publication_commits": 22,
            }
        },
        "work_intake": {
            "coordination": {
                "authority_mode": "review_gated",
                "work_ownership_mode": "exclusive_slice",
                "sync_cadence_mode": "before_publish",
                "implementation_permission": "suspended",
                "resync_required": True,
            }
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command='python3 dev/scripts/devctl.py commit -m "checkpoint"',
        caller_role="implementer",
        defer_publication=True,
    )

    assert decision.publication_deferred_active is True
    assert decision.implementation_admissibility == "allowed"
    assert "implementation.edit" in decision.allowed_actions
    assert "implementation.edit" not in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions


def test_defer_publication_blocks_dirty_edit_when_index_is_staged() -> None:
    payload = {
        "observed_control_topology": "implementer_without_reviewer",
        "reviewer_mode": "tools_only",
        "effective_reviewer_mode": "tools_only",
        "push_decision": {
            "action": "await_checkpoint",
            "reason": "worktree_dirty",
        },
        "governance": {
            "push_enforcement": {
                "checkpoint_required": False,
                "safe_to_continue_editing": True,
                "worktree_dirty": True,
                "dirty_path_count": 1,
                "staged_path_count": 1,
                "pending_publication_commits": 1,
            }
        },
        "work_intake": {
            "coordination": {
                "implementation_permission": "suspended",
                "resync_required": True,
            }
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command='python3 dev/scripts/devctl.py commit -m "checkpoint"',
        caller_role="implementer",
        defer_publication=True,
    )

    assert decision.publication_deferred_active is False
    assert "implementation.edit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions


def test_defer_publication_does_not_override_checkpoint_gate() -> None:
    payload = {
        "implementation_permission": "active",
        "advisory_action": "push_allowed",
        "push_decision": {
            "action": "run_devctl_push",
            "next_step_command": "python3 dev/scripts/devctl.py push --execute",
        },
        "governance": {
            "push_enforcement": {
                "checkpoint_required": True,
                "safe_to_continue_editing": False,
                "checkpoint_reason": "review_loop_relaunch_required",
                "ahead_of_upstream_commits": 3,
            }
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py push --execute",
        defer_publication=True,
    )

    assert decision.publication_deferred_active is False
    assert decision.implementation_admissibility == "checkpoint_required"
    assert "implementation.edit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions


def test_defer_publication_reallows_editing_across_dirty_checkpoint_gate() -> None:
    payload = {
        "implementation_permission": "active",
        "advisory_action": "checkpoint_before_continue",
        "push_decision": {
            "action": "await_checkpoint",
            "next_step_command": 'python3 dev/scripts/devctl.py commit -m "checkpoint"',
        },
        "governance": {
            "push_enforcement": {
                "checkpoint_required": True,
                "safe_to_continue_editing": False,
                "checkpoint_reason": "dirty_path_budget_exceeded",
                "pending_publication_commits": 6,
            }
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command='python3 dev/scripts/devctl.py commit -m "checkpoint"',
        defer_publication=True,
    )

    assert decision.publication_deferred_active is True
    assert "implementation.edit" in decision.allowed_actions
    assert "implementation.edit" not in decision.blocked_actions
    assert "vcs.stage" in decision.blocked_actions
    assert "vcs.commit" in decision.blocked_actions
    assert "vcs.push" in decision.blocked_actions
    assert (
        decision.deferred_publication_command
        == 'python3 dev/scripts/devctl.py commit -m "checkpoint"'
    )


def test_defer_publication_does_not_override_read_only_lane() -> None:
    payload = {
        "implementation_permission": "active",
        "advisory_action": "push_allowed",
        "push_decision": {
            "action": "run_devctl_push",
            "next_step_command": "python3 dev/scripts/devctl.py push --execute",
        },
        "governance": {
            "push_enforcement": {
                "checkpoint_required": False,
                "safe_to_continue_editing": True,
                "ahead_of_upstream_commits": 3,
            }
        },
    }

    decision = build_startup_action_routing(
        payload,
        next_command="python3 dev/scripts/devctl.py push --execute",
        caller_role="observer",
        defer_publication=True,
    )

    assert decision.publication_deferred_active is False
    assert "implementation.edit" in decision.blocked_actions
    assert "implementation.edit" not in decision.allowed_actions


def test_publication_defer_requires_explicit_flag() -> None:
    decision = publication_defer_decision(_publication_defer_input(defer_publication=False))

    assert decision.active is False


def test_publication_defer_requires_lane_edit_allowed() -> None:
    decision = publication_defer_decision(_publication_defer_input(lane_edit_allowed=False))

    assert decision.active is False


def test_publication_defer_requires_implementation_edit_permission() -> None:
    decision = publication_defer_decision(_publication_defer_input(lane_permissions=()))

    assert decision.active is False


def test_publication_defer_requires_active_implementation_permission() -> None:
    decision = publication_defer_decision(_publication_defer_input(permission="blocked"))

    assert decision.active is False


def test_publication_defer_requires_typed_publication_or_checkpoint_pressure() -> None:
    decision = publication_defer_decision(
        _publication_defer_input(
            ctx_payload={},
            next_command="python3 dev/scripts/devctl.py push --execute",
            push={"checkpoint_required": False, "safe_to_continue_editing": True},
        )
    )

    assert decision.active is False


def test_publication_defer_checkpoint_reasons_are_positive_listed() -> None:
    assert "dirty_path_budget_exceeded" in DEFER_SAFE_CHECKPOINT_REASONS
    assert "staged_and_unstaged_worktree_present" in DEFER_SAFE_CHECKPOINT_REASONS

    decision = publication_defer_decision(
        _publication_defer_input(
            push={
                "checkpoint_required": True,
                "safe_to_continue_editing": False,
                "checkpoint_reason": "review_loop_relaunch_required",
                "pending_publication_commits": 1,
            }
        )
    )

    assert decision.active is False


def test_publication_deferral_field_is_render_only_outside_routing() -> None:
    allowed_consumers = {
        "dev/scripts/devctl/runtime/action_routing.py",
        "dev/scripts/devctl/commands/governance/startup_context.py",
        "dev/scripts/devctl/commands/governance/startup_context_render.py",
        "dev/scripts/devctl/commands/governance/startup_context_summary.py",
    }
    offenders: list[str] = []
    for path in Path("dev/scripts/devctl").rglob("*.py"):
        rel_path = path.as_posix()
        if "/tests/" in rel_path or rel_path in allowed_consumers:
            continue
        text = path.read_text(encoding="utf-8")
        if (
            "publication_deferred_active" in text
            or "publication_deferred_reason" in text
        ):
            offenders.append(rel_path)

    assert offenders == []


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


def _publication_defer_input(
    *,
    ctx_payload: dict[str, object] | None = None,
    next_command: str = "python3 dev/scripts/devctl.py review-channel --action status",
    lane_edit_allowed: bool = True,
    lane_permissions: tuple[str, ...] = ("implementation.edit",),
    push: dict[str, object] | None = None,
    permission: str = "active",
    defer_publication: bool = True,
) -> PublicationDeferInput:
    if ctx_payload is None:
        ctx_payload = {"push_decision": {"action": "run_devctl_push"}}
    if push is None:
        push = {"checkpoint_required": False, "safe_to_continue_editing": True}
    return PublicationDeferInput(
        ctx_payload=ctx_payload,
        next_command=next_command,
        lane_edit_allowed=lane_edit_allowed,
        lane_permissions=lane_permissions,
        push=push,
        permission=permission,
        defer_publication=defer_publication,
    )


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
