from __future__ import annotations

from dev.scripts.devctl.commands.review_channel.status_readiness import (
    attach_runtime_readiness,
)


def test_runtime_readiness_marks_blocked_status_without_losing_command_ok() -> None:
    report: dict[str, object] = {
        "action": "status",
        "exit_ok": True,
        "errors": [],
        "recommended_command": "python3 dev/scripts/devctl.py commit -m x",
        "recommended_command_source": "attention",
        "attention": {"status": "checkpoint_required"},
        "authority_snapshot": {
            "safe_to_continue": False,
            "required_action": "cut_checkpoint",
            "blocked_actions": ["vcs.commit", "vcs.push"],
        },
        "coordination_state": {
            "coordination_topology": "multi_agent_active",
            "legacy_reviewer_mode": "single_agent",
            "observed_runtime": {
                "active_runtime_providers": ["codex", "claude"],
                "work_board_row_counts": {"total": 2},
            },
        },
    }

    attach_runtime_readiness(report)

    readiness = report["runtime_readiness"]
    assert report["command_ok"] is True
    assert report["ok"] is True
    assert readiness["system_ok"] is False
    assert readiness["status"] == "blocked"
    assert readiness["safe_to_continue"] is False
    assert readiness["recommended_command_allowed"] is False
    assert readiness["recommended_command_blockers"] == ["vcs.commit"]
    assert readiness["coordination_topology"] == "multi_agent_active"
    assert readiness["legacy_reviewer_mode"] == "single_agent"
    assert readiness["active_runtime_providers"] == ["codex", "claude"]
    assert readiness["work_board_row_counts"] == {"total": 2}


def test_runtime_readiness_preserves_ok_when_runtime_is_ready() -> None:
    report: dict[str, object] = {
        "action": "status",
        "exit_ok": True,
        "errors": [],
        "attention": {"status": "healthy"},
        "authority_snapshot": {
            "safe_to_continue": True,
            "blocked_actions": [],
        },
    }

    attach_runtime_readiness(report)

    assert report["command_ok"] is True
    assert report["ok"] is True
    assert report["runtime_readiness"]["status"] == "ready"


def test_runtime_readiness_allows_healthy_read_only_observer_status() -> None:
    report: dict[str, object] = {
        "action": "status",
        "exit_ok": True,
        "errors": [],
        "attention": {"status": "healthy"},
        "doctor": {
            "status": "healthy",
            "decision_action_id": "continue_scoped_loop",
        },
        "authority_snapshot": {
            "safe_to_continue": False,
            "coordination_state": "single_agent",
            "required_action": "continue_scoped_loop",
            "implementation_permission": "active",
            "current_instruction_revision": "",
            "implementer_ack_state": "missing",
            "allowed_actions": [
                "startup-context.summary",
                "review-channel.status",
                "context-graph.bootstrap",
            ],
            "blocked_actions": [
                "implementation.edit",
                "vcs.stage",
                "vcs.commit",
                "vcs.push",
            ],
        },
    }

    attach_runtime_readiness(report)

    readiness = report["runtime_readiness"]
    assert report["command_ok"] is True
    assert report["ok"] is True
    assert readiness["system_ok"] is True
    assert readiness["status"] == "ready"
    assert readiness["safe_to_continue"] is True
