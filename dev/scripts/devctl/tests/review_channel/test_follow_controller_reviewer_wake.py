from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.review_channel.core import LaneAssignment
from dev.scripts.devctl.review_channel.follow_controller import (
    ReviewerWakeDeps,
    maybe_wake_waiting_reviewer_conductor,
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


def test_maybe_wake_waiting_reviewer_conductor_skips_non_remote_control() -> None:
    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(
            execution_mode="markdown-bridge",
            rollover_threshold_pct=20,
            await_ack_seconds=180,
        ),
        repo_root=Path("/tmp/repo"),
        paths={},
        report=_base_report(),
        operator_interaction_mode="local_terminal",
    )

    assert result is None


def test_maybe_wake_waiting_reviewer_conductor_relaunches_unobserved_action_request(
) -> None:
    cleanup_calls: list[str] = []
    observed_calls: list[str] = []

    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=lambda **_kw: (
            "",
            [
                LaneAssignment(
                    agent_id="AGENT-1",
                    provider="codex",
                    role="reviewer",
                    lane="Codex reviewer",
                    docs="review",
                    mp_scope="MP-355",
                    worktree="../codex-voice-wt-a1",
                    branch="feature/a1",
                )
            ],
        ),
        build_launch_sessions_fn=lambda **_kw: [{"session_name": "codex-conductor"}],
        launch_sessions_headless_fn=lambda _sessions, _warnings: True,
        load_conductor_sessions_fn=lambda **_kw: (
            SimpleNamespace(provider="codex", live=True, session_name="codex-conductor"),
        ),
        cleanup_terminal_session_fn=lambda session: cleanup_calls.append(session.session_name)
        or [],
        mark_action_request_packets_observed_fn=lambda **_kw: observed_calls.append(
            "pkt-1"
        )
        or True,
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(
            execution_mode="markdown-bridge",
            rollover_threshold_pct=20,
            await_ack_seconds=180,
            approval_mode="balanced",
            dangerous=False,
        ),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
            "promotion_plan_path": Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            "artifact_paths": SimpleNamespace(
                artifact_root=Path("/tmp/repo/dev/reports/review_channel")
            ),
        },
        report=_base_report(),
        operator_interaction_mode="remote_control",
        deps=deps,
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-1",
        "requested_action": "restore_reviewer_turn",
    }
    assert cleanup_calls == ["codex-conductor"]
    assert observed_calls == ["pkt-1"]


def test_maybe_wake_waiting_reviewer_conductor_skips_observed_action_request() -> None:
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

    deps = ReviewerWakeDeps(
        load_conductor_sessions_fn=lambda **_kw: (
            SimpleNamespace(provider="codex", live=True, session_name="codex-conductor"),
        ),
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge"),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
        },
        report=report,
        operator_interaction_mode="remote_control",
        deps=deps,
    )

    assert result is None


def test_maybe_wake_waiting_reviewer_conductor_relaunches_unseen_finding() -> None:
    cleanup_calls: list[str] = []
    observed_calls: list[str] = []
    report = {
        "bridge_liveness": {
            "session_state_hints": {
                "codex": {"state": "waiting_for_user_input"},
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
                "from_agent": "claude",
                "kind": "finding",
                "status": "pending",
                "summary": "Review the latest Claude finding.",
            }
        ],
    }

    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=lambda **_kw: (
            "",
            [
                LaneAssignment(
                    agent_id="AGENT-1",
                    provider="codex",
                    role="reviewer",
                    lane="Codex reviewer",
                    docs="review",
                    mp_scope="MP-355",
                    worktree="../codex-voice-wt-a1",
                    branch="feature/a1",
                )
            ],
        ),
        build_launch_sessions_fn=lambda **_kw: [{"session_name": "codex-conductor"}],
        launch_sessions_headless_fn=lambda _sessions, _warnings: True,
        load_conductor_sessions_fn=lambda **_kw: (
            SimpleNamespace(provider="codex", live=True, session_name="codex-conductor"),
        ),
        cleanup_terminal_session_fn=lambda session: cleanup_calls.append(session.session_name)
        or [],
        mark_action_request_packets_observed_fn=lambda **_kw: observed_calls.append(
            "unexpected"
        )
        or True,
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(
            execution_mode="markdown-bridge",
            rollover_threshold_pct=20,
            await_ack_seconds=180,
            approval_mode="balanced",
            dangerous=False,
        ),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
            "promotion_plan_path": Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            "artifact_paths": SimpleNamespace(
                artifact_root=Path("/tmp/repo/dev/reports/review_channel")
            ),
        },
        report=report,
        operator_interaction_mode="remote_control",
        deps=deps,
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-find-1",
        "requested_action": "",
    }
    assert cleanup_calls == ["codex-conductor"]
    assert observed_calls == []


def test_maybe_wake_waiting_reviewer_conductor_allows_typed_claude_lane_when_mode_is_local_terminal(
) -> None:
    cleanup_calls: list[str] = []
    report = _base_report()
    report["packet_inbox"]["agents"][0]["attention_status"] = "review_needed"
    report["packet_inbox"]["agents"][0]["wake_reason"] = "finding_pending"
    report["packet_inbox"]["agents"][0]["latest_finding_packet_id"] = "pkt-find-2"
    report["packets"] = [
        {
            "packet_id": "pkt-find-2",
            "to_agent": "codex",
            "kind": "finding",
            "status": "pending",
            "requested_action": "",
        }
    ]
    report["authority_snapshot"] = {
        "mutation_owner": "claude",
        "verification_owner": "codex",
        "verification_status": "configured",
        "watcher_owner": "claude",
        "watcher_status": "live",
    }

    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=lambda **_kw: (
            "",
            [
                LaneAssignment(
                    agent_id="AGENT-1",
                    provider="codex",
                    role="reviewer",
                    lane="Codex reviewer",
                    docs="review",
                    mp_scope="MP-355",
                    worktree="../codex-voice-wt-a1",
                    branch="feature/a1",
                )
            ],
        ),
        build_launch_sessions_fn=lambda **_kw: [{"session_name": "codex-conductor"}],
        launch_sessions_headless_fn=lambda _sessions, _warnings: True,
        load_conductor_sessions_fn=lambda **_kw: (
            SimpleNamespace(provider="codex", live=True, session_name="codex-conductor"),
        ),
        cleanup_terminal_session_fn=lambda session: cleanup_calls.append(session.session_name)
        or [],
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(
            execution_mode="markdown-bridge",
            rollover_threshold_pct=20,
            await_ack_seconds=180,
            approval_mode="balanced",
            dangerous=False,
        ),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
            "promotion_plan_path": Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            "artifact_paths": SimpleNamespace(
                artifact_root=Path("/tmp/repo/dev/reports/review_channel")
            ),
        },
        report=report,
        operator_interaction_mode="local_terminal",
        deps=deps,
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-find-2",
        "requested_action": "",
    }
    assert cleanup_calls == ["codex-conductor"]


def test_maybe_wake_waiting_reviewer_conductor_allows_typed_finding_without_waiting_hint(
) -> None:
    cleanup_calls: list[str] = []
    report = _base_report()
    report["bridge_liveness"]["session_state_hints"]["codex"]["state"] = "running"
    report["packet_inbox"]["agents"][0]["attention_status"] = "review_needed"
    report["packet_inbox"]["agents"][0]["wake_reason"] = "finding_pending"
    report["packet_inbox"]["agents"][0]["latest_finding_packet_id"] = "pkt-find-typed"
    report["packet_inbox"]["agents"][0].pop("current_instruction_packet_id", None)
    report["packets"] = [
        {
            "packet_id": "pkt-find-typed",
            "to_agent": "codex",
            "kind": "finding",
            "status": "pending",
            "requested_action": "",
        }
    ]
    report["authority_snapshot"] = {
        "mutation_owner": "claude",
        "verification_owner": "codex",
        "verification_status": "live",
        "watcher_owner": "claude",
        "watcher_status": "live",
    }

    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=lambda **_kw: (
            "",
            [
                LaneAssignment(
                    agent_id="AGENT-1",
                    provider="codex",
                    role="reviewer",
                    lane="Codex reviewer",
                    docs="review",
                    mp_scope="MP-355",
                    worktree="../codex-voice-wt-a1",
                    branch="feature/a1",
                )
            ],
        ),
        build_launch_sessions_fn=lambda **_kw: [{"session_name": "codex-conductor"}],
        launch_sessions_headless_fn=lambda _sessions, _warnings: True,
        load_conductor_sessions_fn=lambda **_kw: (
            SimpleNamespace(provider="codex", live=True, session_name="codex-conductor"),
        ),
        cleanup_terminal_session_fn=lambda session: cleanup_calls.append(session.session_name)
        or [],
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(
            execution_mode="markdown-bridge",
            rollover_threshold_pct=20,
            await_ack_seconds=180,
            approval_mode="balanced",
            dangerous=False,
        ),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
            "promotion_plan_path": Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            "artifact_paths": SimpleNamespace(
                artifact_root=Path("/tmp/repo/dev/reports/review_channel")
            ),
        },
        report=report,
        operator_interaction_mode="local_terminal",
        deps=deps,
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-find-typed",
        "requested_action": "",
    }
    assert cleanup_calls == ["codex-conductor"]


def test_maybe_wake_waiting_reviewer_conductor_launches_when_no_live_codex_session(
) -> None:
    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=lambda **_kw: (
            "",
            [
                LaneAssignment(
                    agent_id="AGENT-1",
                    provider="codex",
                    role="reviewer",
                    lane="Codex reviewer",
                    docs="review",
                    mp_scope="MP-355",
                    worktree="../codex-voice-wt-a1",
                    branch="feature/a1",
                )
            ],
        ),
        build_launch_sessions_fn=lambda **_kw: [{"session_name": "codex-conductor"}],
        launch_sessions_headless_fn=lambda _sessions, _warnings: True,
        load_conductor_sessions_fn=lambda **_kw: (),
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(
            execution_mode="markdown-bridge",
            rollover_threshold_pct=20,
            await_ack_seconds=180,
            approval_mode="balanced",
            dangerous=False,
        ),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
            "promotion_plan_path": Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            "artifact_paths": SimpleNamespace(
                artifact_root=Path("/tmp/repo/dev/reports/review_channel")
            ),
        },
        report=_base_report(),
        operator_interaction_mode="remote_control",
        deps=deps,
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-1",
        "requested_action": "restore_reviewer_turn",
    }


def test_maybe_wake_waiting_reviewer_conductor_allows_finding_wake_during_resync() -> None:
    cleanup_calls: list[str] = []
    report = {
        "bridge_liveness": {
            "session_state_hints": {
                "codex": {"state": "waiting_for_user_input"},
            }
        },
        "coordination": {
            "resync_required": True,
        },
        "packet_inbox": {
            "agents": [
                {
                    "agent": "codex",
                    "attention_status": "review_needed",
                    "wake_reason": "finding_pending",
                    "latest_finding_packet_id": "pkt-find-resync",
                }
            ]
        },
        "packets": [
            {
                "packet_id": "pkt-find-resync",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "requested_action": "",
            }
        ],
    }

    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=lambda **_kw: (
            "",
            [
                LaneAssignment(
                    agent_id="AGENT-1",
                    provider="codex",
                    role="reviewer",
                    lane="Codex reviewer",
                    docs="review",
                    mp_scope="MP-355",
                    worktree="../codex-voice-wt-a1",
                    branch="feature/a1",
                )
            ],
        ),
        build_launch_sessions_fn=lambda **_kw: [{"session_name": "codex-conductor"}],
        launch_sessions_headless_fn=lambda _sessions, _warnings: True,
        load_conductor_sessions_fn=lambda **_kw: (
            SimpleNamespace(provider="codex", live=True, session_name="codex-conductor"),
        ),
        cleanup_terminal_session_fn=lambda session: cleanup_calls.append(session.session_name)
        or [],
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(
            execution_mode="markdown-bridge",
            rollover_threshold_pct=20,
            await_ack_seconds=180,
            approval_mode="balanced",
            dangerous=False,
        ),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
            "promotion_plan_path": Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            "artifact_paths": SimpleNamespace(
                artifact_root=Path("/tmp/repo/dev/reports/review_channel")
            ),
        },
        report=report,
        operator_interaction_mode="remote_control",
        deps=deps,
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-find-resync",
        "requested_action": "",
    }
    assert cleanup_calls == ["codex-conductor"]


def test_maybe_wake_waiting_reviewer_conductor_blocks_action_request_during_resync() -> None:
    report = _base_report()
    report["coordination"] = {"resync_required": True}

    deps = ReviewerWakeDeps(
        load_conductor_sessions_fn=lambda **_kw: (
            SimpleNamespace(provider="codex", live=True, session_name="codex-conductor"),
        ),
    )

    result = maybe_wake_waiting_reviewer_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge"),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
        },
        report=report,
        operator_interaction_mode="remote_control",
        deps=deps,
    )

    assert result is None
