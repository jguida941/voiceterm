from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.review_channel.core import LaneAssignment
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


def test_reviewer_wake_uses_agent_loop_decision_when_packet_inbox_is_stale() -> None:
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
                "loop_mode": "pivot_to_packet",
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


def test_reviewer_wake_skips_stopped_agent_loop_decision() -> None:
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
            terminal="none",
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
        "wake_method": "replace",
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
            terminal="none",
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
        "wake_method": "replace",
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
            terminal="none",
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
        "wake_method": "replace",
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
        "wake_method": "replace",
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
        "wake_method": "spawn_fresh",
    }


def test_maybe_wake_waiting_agent_conductor_does_not_spawn_mutating_target_session() -> None:
    def fail_launch(**_kwargs):
        raise AssertionError("target-session wake must not spawn a replacement")

    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=fail_launch,
        build_launch_sessions_fn=fail_launch,
        launch_sessions_headless_fn=lambda _sessions, _warnings: False,
        load_conductor_sessions_fn=lambda **_kwargs: (),
    )

    result = maybe_wake_waiting_agent_conductor(
        args=SimpleNamespace(execution_mode="markdown-bridge"),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
        },
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
        deps=deps,
    )

    assert result == {
        "attempted": True,
        "woke": False,
        "reason": "target_session_unreachable_without_registry",
        "packet_id": "pkt-claude",
        "requested_action": "stage_commit_pipeline",
        "target_agent": "claude",
        "target_role": "dashboard",
        "target_session_id": "session-visible",
        "wake_method": "unreachable_until_operator_prompt",
    }


def test_maybe_wake_waiting_agent_conductor_delegates_read_only_dashboard_packet_headless() -> None:
    launch_calls: list[list[dict[str, object]]] = []
    build_requests: list[object] = []

    def fake_build_launch_sessions(**kwargs):
        build_requests.append(kwargs["request"])
        return [{"session_name": "claude-headless-delegate"}]

    def fake_launch_sessions_headless(sessions, _warnings):
        sessions[0]["headless_launch_pid"] = 4242
        launch_calls.append(sessions)
        return True

    deps = ReviewerWakeDeps(
        ensure_launcher_prereqs_fn=lambda **_kw: (
            "",
            [
                LaneAssignment(
                    agent_id="AGENT-2",
                    provider="claude",
                    role="implementer",
                    lane="Claude coding",
                    docs="review",
                    mp_scope="MP-377",
                    worktree="../codex-voice-wt-a2",
                    branch="feature/a2",
                )
            ],
        ),
        build_launch_sessions_fn=fake_build_launch_sessions,
        launch_sessions_headless_fn=fake_launch_sessions_headless,
        load_conductor_sessions_fn=lambda **_kwargs: (),
        cleanup_terminal_session_fn=lambda _session: [
            "unexpected cleanup for dashboard delegate"
        ],
    )

    result = maybe_wake_waiting_agent_conductor(
        args=SimpleNamespace(
            execution_mode="markdown-bridge",
            terminal="none",
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
        },
        report=_base_report(),
        operator_interaction_mode="single_agent",
        target_agent="claude",
        packet={
            "packet_id": "pkt-dashboard",
            "to_agent": "claude",
            "kind": "system_notice",
            "status": "pending",
            "requested_action": "review_only",
            "target_role": "dashboard",
            "target_session_id": "session-visible",
        },
        deps=deps,
    )

    assert result == {
        "attempted": True,
        "woke": False,
        "reason": "headless_delegate_launched",
        "packet_id": "pkt-dashboard",
        "requested_action": "review_only",
        "target_agent": "claude",
        "target_role": "dashboard",
        "target_session_id": "session-visible",
        "dashboard_session_id": "session-visible",
        "wake_method": "headless_delegate",
        "delegated": True,
        "visible_session_woke": False,
        "spawned_pids": [4242],
        "delivered_to_pids": [4242],
    }
    assert launch_calls == [
        [{"session_name": "claude-headless-delegate", "headless_launch_pid": 4242}]
    ]
    assert build_requests[0].headless is True
    assert build_requests[0].requested_worker_budgets == {"claude": 0}


def test_maybe_wake_waiting_reviewer_conductor_cleans_stale_running_codex_session() -> None:
    cleanup_calls: list[str] = []

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
            SimpleNamespace(
                provider="codex",
                live=False,
                session_name="codex-conductor",
                session_pid=4242,
                script_probe_state="running",
            ),
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
        "wake_method": "replace",
        "replaced_pids": [4242],
    }
    assert cleanup_calls == ["codex-conductor"]


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
        "wake_method": "replace",
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
