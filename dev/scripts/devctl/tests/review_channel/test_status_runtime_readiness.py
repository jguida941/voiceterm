from __future__ import annotations

from dev.scripts.devctl.commands.review_channel.status_action_support import (
    normalize_read_only_status_ok,
)
from dev.scripts.devctl.commands.review_channel.status_readiness import (
    append_runtime_readiness_markdown,
    attach_runtime_readiness,
)
from dev.scripts.devctl.commands.review_channel_bridge_render import render_bridge_md
from dev.scripts.devctl.review_channel.event_render import render_event_md


def _blocked_read_only_status_report() -> dict[str, object]:
    report: dict[str, object] = {
        "action": "status",
        "exit_ok": True,
        "errors": [],
        "recommended_command": "python3 dev/scripts/devctl.py commit -m x",
        "attention": {"status": "checkpoint_required"},
        "authority_snapshot": {
            "safe_to_continue": False,
            "blocked_actions": ["vcs.commit"],
        },
    }
    attach_runtime_readiness(report)
    return report


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


def test_normalize_read_only_status_keeps_advisory_runtime_block_green() -> None:
    report: dict[str, object] = {
        "action": "status",
        "exit_ok": True,
        "errors": [],
        "recommended_command": "python3 dev/scripts/devctl.py commit -m x",
        "attention": {"status": "healthy"},
        "authority_snapshot": {
            "safe_to_continue": False,
            "blocked_actions": ["vcs.commit"],
        },
    }

    normalize_read_only_status_ok(report)

    assert report["ok"] is True
    assert report["command_ok"] is True
    assert report["runtime_readiness"]["system_ok"] is False
    assert report["runtime_readiness"]["recommended_command_allowed"] is False


def test_runtime_readiness_markdown_separates_command_and_system_status() -> None:
    report = _blocked_read_only_status_report()
    lines: list[str] = []

    append_runtime_readiness_markdown(lines, report)
    rendered = "\n".join(lines)

    assert "## Runtime Readiness" in rendered
    assert "- command_ok: True" in rendered
    assert "- system_ok: False" in rendered
    assert "- recommended_command_allowed: False" in rendered
    assert "- recommended_command_blockers: vcs.commit" in rendered


def test_event_markdown_renders_runtime_readiness_section() -> None:
    report = _blocked_read_only_status_report()
    report.update(
        {
            "execution_mode": "event-backed",
            "queue": {},
            "packet": None,
            "packets": [],
            "history": [],
        }
    )

    rendered = render_event_md(report)

    assert "- ok: True" in rendered
    assert "## Runtime Readiness" in rendered
    assert "- system_ok: False" in rendered


def test_bridge_markdown_renders_runtime_readiness_section() -> None:
    report = _blocked_read_only_status_report()
    report.update(
        {
            "execution_mode": "markdown-bridge",
            "terminal": "none",
            "terminal_profile_requested": None,
            "terminal_profile_applied": None,
            "approval_mode": "balanced",
            "dangerous": False,
            "rollover_threshold_pct": None,
            "rollover_trigger": None,
            "await_ack_seconds": 0,
            "bridge_active": False,
            "launched": False,
            "typed_state_written": False,
            "process_alive": False,
            "bridge_attached": False,
            "handoff_ack_required": False,
            "codex_requested_worker_budget": 0,
            "claude_requested_worker_budget": 0,
            "retirement_note": None,
            "bridge_liveness": {},
        }
    )

    rendered = render_bridge_md(report, bridge_liveness_keys=())

    assert "- ok: True" in rendered
    assert "## Runtime Readiness" in rendered
    assert "- system_ok: False" in rendered
