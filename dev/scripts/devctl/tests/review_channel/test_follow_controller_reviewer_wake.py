"""Regressions for follow-loop packet attention.

The follow loop may identify packets needing attention, but packet delivery is
not a conductor launch primitive.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.review_channel.follow_controller import (
    ReviewerWakeDeps,
    maybe_wake_waiting_agent_conductor,
    maybe_wake_waiting_reviewer_conductor,
)
from dev.scripts.devctl.review_channel.follow_controller_wake_target import (
    resolve_reviewer_wake_target,
)


def _base_report() -> dict[str, object]:
    return {
        "bridge_liveness": {
            "session_state_hints": {
                "codex": {"state": "waiting_for_user_input"},
            }
        },
        "packet_inbox": {
            "agents": [
                {
                    "agent": "codex",
                    "attention_status": "wake_required",
                    "current_instruction_packet_id": "pkt-1",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "pkt-1",
                "to_agent": "codex",
                "kind": "action_request",
                "status": "pending",
                "requested_action": "restore_reviewer_turn",
            }
        ],
    }


def _fail_launch_dependency(**_kwargs):
    raise AssertionError("packet attention must not invoke launch dependencies")


def test_maybe_wake_waiting_reviewer_conductor_skips_non_remote_without_authority() -> None:
    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge"),
        repo_root=Path("/tmp/repo"),
        paths={},
        report=_base_report(),
        operator_interaction_mode="local_terminal",
    )

    assert result is None


def test_reviewer_wake_target_uses_agent_loop_decision_when_packet_inbox_is_stale() -> None:
    report = {
        "bridge_liveness": {
            "session_state_hints": {
                "codex": {"state": "waiting_for_user_input"},
            }
        },
        "packet_inbox": {"agents": []},
        "agent_loop_decisions": [
            {
                "actor_id": "codex",
                "actor_role": "reviewer",
                "loop_mode": "continue_to_goal",
                "user_action": "Continue to goal",
                "continuation_goal": "pkt-loop",
                "wake_required": True,
                "attention_packet_id": "pkt-loop",
            }
        ],
        "packets": [
            {
                "packet_id": "pkt-loop",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
            }
        ],
    }

    packet, command = resolve_reviewer_wake_target(
        report=report,
        operator_interaction_mode="remote_control",
    )

    assert command is None
    assert packet is not None
    assert packet["packet_id"] == "pkt-loop"


def test_reviewer_wake_target_skips_stopped_agent_loop_decision() -> None:
    report = {
        "bridge_liveness": {
            "session_state_hints": {
                "codex": {"state": "waiting_for_user_input"},
            }
        },
        "packet_inbox": {"agents": []},
        "agent_loop_decisions": [
            {
                "actor_id": "codex",
                "actor_role": "reviewer",
                "loop_mode": "stopped",
                "wake_required": True,
                "attention_packet_id": "pkt-loop",
            }
        ],
        "packets": [
            {
                "packet_id": "pkt-loop",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
            }
        ],
    }

    packet, command = resolve_reviewer_wake_target(
        report=report,
        operator_interaction_mode="remote_control",
    )

    assert packet is None
    assert command is None


def test_maybe_wake_waiting_reviewer_conductor_records_attention_only() -> None:
    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=_fail_launch_dependency,
        build_launch_sessions_fn=_fail_launch_dependency,
        launch_sessions_headless_fn=lambda _sessions, _warnings: False,
        load_conductor_sessions_fn=lambda **_kwargs: (),
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge"),
        repo_root=Path("/tmp/repo"),
        paths={},
        report=_base_report(),
        operator_interaction_mode="remote_control",
        deps=deps,
    )

    assert result["attempted"] is False
    assert result["woke"] is False
    assert result["reason"] == "packet_delivery_records_typed_attention_only"
    assert result["packet_id"] == "pkt-1"
    assert result["requested_action"] == "restore_reviewer_turn"
    assert result["target_agent"] == "codex"
    assert result["wake_method"] == "none"


def test_maybe_wake_waiting_reviewer_conductor_skips_observed_packet() -> None:
    report = _base_report()
    report["packets"] = [
        {
            "packet_id": "pkt-1",
            "to_agent": "codex",
            "kind": "action_request",
            "status": "pending",
            "requested_action": "restore_reviewer_turn",
            "delivery_observed_at_utc": "2026-04-14T18:00:00Z",
        }
    ]

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge"),
        repo_root=Path("/tmp/repo"),
        paths={},
        report=report,
        operator_interaction_mode="remote_control",
        deps=ReviewerWakeDeps(
            ensure_launcher_prereqs_fn=_fail_launch_dependency,
        ),
    )

    assert result is None


def test_maybe_wake_waiting_reviewer_conductor_finding_records_attention_only() -> None:
    report = {
        "bridge_liveness": {
            "session_state_hints": {
                "codex": {"state": "running"},
            }
        },
        "packet_inbox": {
            "agents": [
                {
                    "agent": "codex",
                    "attention_status": "review_needed",
                    "wake_reason": "finding_pending",
                    "latest_finding_packet_id": "pkt-find-1",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "pkt-find-1",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
            }
        ],
        "authority_snapshot": {
            "mutation_owner": "claude",
            "verification_owner": "codex",
            "verification_status": "live",
            "watcher_owner": "claude",
            "watcher_status": "live",
        },
    }

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge"),
        repo_root=Path("/tmp/repo"),
        paths={},
        report=report,
        operator_interaction_mode="local_terminal",
        deps=ReviewerWakeDeps(
            ensure_launcher_prereqs_fn=_fail_launch_dependency,
        ),
    )

    assert result["attempted"] is False
    assert result["woke"] is False
    assert result["reason"] == "packet_delivery_records_typed_attention_only"
    assert result["packet_id"] == "pkt-find-1"
    assert result["target_agent"] == "codex"
    assert result["wake_method"] == "none"


def test_maybe_wake_waiting_agent_conductor_records_target_session_attention_only() -> None:
    result = maybe_wake_waiting_agent_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge"),
        repo_root=Path("/tmp/repo"),
        paths={},
        report=_base_report(),
        operator_interaction_mode="remote_control",
        target_agent="claude",
        packet={
            "packet_id": "pkt-claude",
            "to_agent": "claude",
            "kind": "action_request",
            "status": "pending",
            "requested_action": "stage_commit_pipeline",
            "target_role": "dashboard",
            "target_session_id": "session-visible",
        },
        deps=ReviewerWakeDeps(
            ensure_launcher_prereqs_fn=_fail_launch_dependency,
            build_launch_sessions_fn=_fail_launch_dependency,
        ),
    )

    assert result["attempted"] is False
    assert result["woke"] is False
    assert result["reason"] == "packet_delivery_records_typed_attention_only"
    assert result["packet_id"] == "pkt-claude"
    assert result["requested_action"] == "stage_commit_pipeline"
    assert result["target_agent"] == "claude"
    assert result["target_role"] == "dashboard"
    assert result["target_session_id"] == "session-visible"
    assert result["wake_method"] == "none"


def test_maybe_wake_waiting_agent_conductor_records_unscoped_codex_attention_only() -> None:
    result = maybe_wake_waiting_agent_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge", terminal="none"),
        repo_root=Path("/tmp/repo"),
        paths={},
        report=_base_report(),
        operator_interaction_mode="remote_control",
        target_agent="codex",
        packet={
            "packet_id": "pkt-codex-unscoped",
            "to_agent": "codex",
            "kind": "finding",
            "status": "pending",
        },
        deps=ReviewerWakeDeps(
            ensure_launcher_prereqs_fn=_fail_launch_dependency,
            build_launch_sessions_fn=_fail_launch_dependency,
        ),
    )

    assert result["attempted"] is False
    assert result["woke"] is False
    assert result["reason"] == "packet_delivery_records_typed_attention_only"
    assert result["wake_method"] == "none"
    assert result["target_agent"] == "codex"
