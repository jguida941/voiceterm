"""Focused regressions for event-backed post-triggered reviewer wake."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.event_handler import _run_event_action
from dev.scripts.devctl.commands.review_channel.event_post_wake import (
    EventPostWakeDeps,
    maybe_wake_posted_reviewer_packet,
)
from dev.scripts.devctl.commands.review_channel_command.models import RuntimePaths


def test_maybe_wake_posted_reviewer_packet_uses_typed_status_refresh() -> None:
    observed: dict[str, object] = {}

    def fake_refresh_status_snapshot(**kwargs):
        observed["refresh_kwargs"] = kwargs
        return SimpleNamespace(
            bridge_liveness={
                "reviewer_mode": "active_dual_agent",
                "session_state_hints": {
                    "codex": {"state": "waiting_for_user_input"},
                },
            },
            review_state=SimpleNamespace(
                to_dict=lambda: {
                    "packet_inbox": {
                        "attention_revision": "rev-1",
                        "agents": [
                            {
                                "agent": "codex",
                                "attention_status": "review_needed",
                                "wake_reason": "finding_pending",
                                "latest_finding_packet_id": "pkt-find-1",
                            }
                        ],
                    },
                    "packets": [
                        {
                            "packet_id": "pkt-find-1",
                            "to_agent": "codex",
                            "kind": "finding",
                            "requested_action": "",
                        }
                    ],
                    "coordination": {"resync_required": False},
                    "authority_snapshot": {
                        "mutation_owner": "claude",
                        "verification_owner": "codex",
                        "verification_status": "configured",
                        "watcher_owner": "claude",
                        "watcher_status": "live",
                    },
                }
            ),
        )

    def fake_maybe_wake(**kwargs):
        observed["wake_kwargs"] = kwargs
        return {
            "attempted": True,
            "woke": True,
            "reason": "launched",
            "packet_id": "pkt-find-1",
            "requested_action": "",
        }

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
            "promotion_plan_path": Path("/tmp/repo/dev/active/ai_governance_platform.md"),
        },
        packet={"packet_id": "pkt-find-1", "to_agent": "codex", "kind": "finding"},
        posted_review_state_payload={
            "packet_inbox": {
                "attention_revision": "rev-1",
                "agents": [
                    {
                        "agent": "codex",
                        "attention_status": "review_needed",
                        "wake_reason": "finding_pending",
                        "latest_finding_packet_id": "pkt-find-1",
                    }
                ],
            },
            "packets": [
                {
                    "packet_id": "pkt-find-1",
                    "to_agent": "codex",
                    "kind": "finding",
                    "requested_action": "",
                }
            ],
            "coordination": {"resync_required": False},
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fake_refresh_status_snapshot,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=lambda **_kwargs: "remote_control",
            maybe_wake_waiting_reviewer_conductor_fn=fake_maybe_wake,
            load_or_refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(
                review_state={}
            ),
        ),
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-find-1",
        "requested_action": "",
    }
    assert observed["refresh_kwargs"]["repo_root"] == Path("/tmp/repo")
    assert observed["wake_kwargs"]["operator_interaction_mode"] == "remote_control"
    assert observed["wake_kwargs"]["report"]["packet_inbox"]["attention_revision"] == "rev-1"
    assert observed["wake_kwargs"]["report"]["coordination"] == {
        "resync_required": False
    }
    assert observed["wake_kwargs"]["report"]["authority_snapshot"] == {
        "mutation_owner": "claude",
        "verification_owner": "codex",
        "verification_status": "configured",
        "watcher_owner": "claude",
        "watcher_status": "live",
    }


def test_maybe_wake_posted_reviewer_packet_routes_non_codex_adapter() -> None:
    observed: dict[str, object] = {}

    def fake_refresh_status_snapshot(**_kwargs):
        return SimpleNamespace(
            bridge_liveness={"reviewer_mode": "single_agent"},
            review_state=SimpleNamespace(
                to_dict=lambda: {
                    "packet_inbox": {"agents": []},
                    "packets": [],
                    "coordination": {"resync_required": False},
                }
            ),
        )

    def fake_agent_wake(**kwargs):
        observed.update(kwargs)
        return {
            "attempted": True,
            "woke": True,
            "reason": "launched",
            "packet_id": "pkt-claude",
            "requested_action": "probe",
            "target_agent": "claude",
        }

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
        },
        packet={
            "packet_id": "pkt-claude",
            "to_agent": "claude",
            "kind": "finding",
            "requested_action": "probe",
            "target_role": "dashboard",
            "target_session_id": "session-visible",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fake_refresh_status_snapshot,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=lambda **_kwargs: "remote_control",
            maybe_wake_waiting_reviewer_conductor_fn=lambda **_kwargs: None,
            maybe_wake_waiting_agent_conductor_fn=fake_agent_wake,
            load_or_refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(
                review_state={}
            ),
        ),
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-claude",
        "requested_action": "probe",
        "target_agent": "claude",
    }
    assert observed["target_agent"] == "claude"
    assert observed["packet"]["packet_id"] == "pkt-claude"
    assert observed["operator_interaction_mode"] == "remote_control"


def test_maybe_wake_posted_reviewer_packet_wakes_system_notice_to_provider() -> None:
    observed: dict[str, object] = {}

    def fake_refresh_status_snapshot(**_kwargs):
        return SimpleNamespace(
            bridge_liveness={"reviewer_mode": "active_dual_agent"},
            review_state=SimpleNamespace(
                to_dict=lambda: {
                    "packet_inbox": {"agents": []},
                    "packets": [],
                }
            ),
        )

    def fake_agent_wake(**kwargs):
        observed["called"] = True
        return {
            "attempted": True,
            "woke": True,
            "reason": "launched",
            "packet_id": "pkt-status",
            "requested_action": "",
            "target_agent": "claude",
        }

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={
            "bridge_path": Path("/tmp/repo/bridge.md"),
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
        },
        packet={
            "packet_id": "pkt-status",
            "to_agent": "claude",
            "kind": "system_notice",
            "requested_action": "",
            "status": "pending",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fake_refresh_status_snapshot,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=lambda **_kwargs: "remote_control",
            maybe_wake_waiting_reviewer_conductor_fn=lambda **_kwargs: None,
            maybe_wake_waiting_agent_conductor_fn=fake_agent_wake,
            load_or_refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(
                review_state={}
            ),
        ),
    )

    assert result == {
        "attempted": True,
        "woke": False,
        "reason": "target_session_binding_required",
        "packet_id": "pkt-status",
        "requested_action": "",
        "target_agent": "claude",
        "wake_method": "typed_attention_event",
        "target_role": "",
        "target_session_id": "",
        "visible_session_woke": False,
        "attention_decision_shape": "packet_arrival",
        "next_pivot_event": "packet_wake_attempted",
        "warnings": [
            "Provider wake suppressed: packet lacks actor role/session routing, "
            "so launching a fresh session would not prove the intended actor "
            "consumed it."
        ],
    }
    assert observed == {}


def test_maybe_wake_posted_reviewer_packet_records_wake_receipt(tmp_path: Path) -> None:
    recorded: dict[str, object] = {}

    def fake_refresh_status_snapshot(**_kwargs):
        return SimpleNamespace(
            bridge_liveness={"reviewer_mode": "single_agent"},
            review_state=SimpleNamespace(
                to_dict=lambda: {
                    "packet_inbox": {"agents": []},
                    "packets": [],
                }
            ),
        )

    def fake_agent_wake(**_kwargs):
        return {
            "attempted": True,
            "woke": False,
            "visible_session_woke": False,
            "delegated": True,
            "reason": "headless_delegate_launched",
            "wake_method": "headless_delegate",
            "packet_id": "pkt-dashboard",
            "requested_action": "review_only",
            "target_agent": "claude",
            "target_role": "dashboard",
            "target_session_id": "session-visible",
            "dashboard_session_id": "session-visible",
            "spawned_pids": [4242],
            "delivered_to_pids": [4242],
        }

    def fake_append_event(events_path, event, *, existing_events):
        recorded["events_path"] = events_path
        recorded["event"] = event
        recorded["existing_events"] = existing_events
        return event

    artifact_paths = SimpleNamespace(
        event_log_path=str(tmp_path / "events/trace.ndjson"),
        state_path=str(tmp_path / "state/latest.json"),
        projections_root=str(tmp_path / "projections/latest"),
    )

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed", terminal="none"),
        repo_root=tmp_path,
        paths={
            "bridge_path": tmp_path / "bridge.md",
            "review_channel_path": tmp_path / "dev/active/review_channel.md",
            "status_dir": tmp_path / "dev/reports/review_channel/latest",
            "artifact_paths": artifact_paths,
        },
        packet={
            "packet_id": "pkt-dashboard",
            "trace_id": "trace-1",
            "from_agent": "codex",
            "to_agent": "claude",
            "kind": "system_notice",
            "requested_action": "review_only",
            "target_role": "dashboard",
            "target_session_id": "session-visible",
            "status": "pending",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fake_refresh_status_snapshot,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=lambda **_kwargs: "single_agent",
            maybe_wake_waiting_reviewer_conductor_fn=lambda **_kwargs: None,
            maybe_wake_waiting_agent_conductor_fn=fake_agent_wake,
            load_or_refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(
                review_state={}
            ),
            load_events_fn=lambda _path: [],
            append_event_fn=fake_append_event,
            refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(),
        ),
    )

    assert result["wake_method"] == "headless_delegate"
    assert result["visible_session_woke"] is False
    event = recorded["event"]
    assert event["event_type"] == "packet_wake_attempted"
    assert event["packet_id"] == "pkt-dashboard"
    assert event["wake_method"] == "headless_delegate"
    assert event["delegated"] is True
    assert event["visible_session_woke"] is False
    assert event["wake_receipt"]["contract_id"] == "PacketWakeReceipt"
    assert event["wake_receipt"]["attention_decision_shape"] == "packet_arrival"
    assert event["wake_receipt"]["next_pivot_event"] == "packet_wake_attempted"
    assert event["wake_receipt"]["spawned_pids"] == [4242]
    assert event["wake_receipt"]["delivered_to_pids"] == [4242]


def test_maybe_wake_posted_reviewer_packet_records_attention_without_wake_report(
    tmp_path: Path,
) -> None:
    recorded: dict[str, object] = {}

    def fake_refresh_status_snapshot(**_kwargs):
        return SimpleNamespace(
            bridge_liveness={"reviewer_mode": "active_dual_agent"},
            review_state=SimpleNamespace(to_dict=lambda: {"packet_inbox": {}, "packets": []}),
        )

    def fake_append_event(_events_path, event, *, existing_events):
        recorded["event"] = event
        recorded["existing_events"] = existing_events
        return event

    artifact_paths = SimpleNamespace(
        event_log_path=str(tmp_path / "events/trace.ndjson"),
        state_path=str(tmp_path / "state/latest.json"),
        projections_root=str(tmp_path / "projections/latest"),
    )

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed", terminal="none"),
        repo_root=tmp_path,
        paths={
            "bridge_path": tmp_path / "bridge.md",
            "review_channel_path": tmp_path / "dev/active/review_channel.md",
            "status_dir": tmp_path / "dev/reports/review_channel/latest",
            "artifact_paths": artifact_paths,
        },
        packet={
            "packet_id": "pkt-codex",
            "trace_id": "trace-1",
            "from_agent": "claude",
            "to_agent": "codex",
            "kind": "finding",
            "status": "pending",
            "target_role": "implementer",
            "target_session_id": "session-codex",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fake_refresh_status_snapshot,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=lambda **_kwargs: "remote_control",
            maybe_wake_waiting_reviewer_conductor_fn=lambda **_kwargs: None,
            load_or_refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(
                review_state={}
            ),
            load_events_fn=lambda _path: [],
            append_event_fn=fake_append_event,
            refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(),
        ),
    )

    assert result["wake_method"] == "session_poll"
    assert result["reason"] == "target_session_poll_required"
    assert result["target_role"] == "implementer"
    assert result["target_session_id"] == "session-codex"
    assert result["visible_session_woke"] is False
    event = recorded["event"]
    assert event["event_type"] == "packet_wake_attempted"
    assert event["packet_id"] == "pkt-codex"
    assert event["wake_receipt"]["attention_decision_shape"] == "packet_arrival"
    assert event["wake_receipt"]["next_pivot_event"] == "packet_wake_attempted"
    assert event["wake_receipt"]["wake_method"] == "session_poll"


def test_maybe_wake_posted_reviewer_packet_reports_startup_blocked_wake(
    tmp_path: Path,
) -> None:
    recorded: dict[str, object] = {}

    def fake_refresh_status_snapshot(**_kwargs):
        return SimpleNamespace(
            bridge_liveness={"reviewer_mode": "active_dual_agent"},
            review_state=SimpleNamespace(
                to_dict=lambda: {
                    "packet_inbox": {},
                    "packets": [],
                    "agent_loop_decisions": [
                        {
                            "actor_id": "codex",
                            "actor_role": "implementer",
                            "loop_mode": "pivot_to_packet",
                            "required_action": "triage_pending_packet",
                            "top_blocker": (
                                "startup authority: import_index_atomicity"
                            ),
                            "safe_to_continue": False,
                            "may_mutate": False,
                            "attention_packet_id": "pkt-codex",
                        }
                    ],
                }
            ),
        )

    def fake_append_event(_events_path, event, *, existing_events):
        recorded["event"] = event
        recorded["existing_events"] = existing_events
        return event

    artifact_paths = SimpleNamespace(
        event_log_path=str(tmp_path / "events/trace.ndjson"),
        state_path=str(tmp_path / "state/latest.json"),
        projections_root=str(tmp_path / "projections/latest"),
    )

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed", terminal="none"),
        repo_root=tmp_path,
        paths={
            "bridge_path": tmp_path / "bridge.md",
            "review_channel_path": tmp_path / "dev/active/review_channel.md",
            "status_dir": tmp_path / "dev/reports/review_channel/latest",
            "artifact_paths": artifact_paths,
        },
        packet={
            "packet_id": "pkt-codex",
            "trace_id": "trace-1",
            "from_agent": "claude",
            "to_agent": "codex",
            "kind": "finding",
            "status": "pending",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fake_refresh_status_snapshot,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=lambda **_kwargs: "remote_control",
            maybe_wake_waiting_reviewer_conductor_fn=lambda **_kwargs: None,
            load_or_refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(
                review_state={}
            ),
            load_events_fn=lambda _path: [],
            append_event_fn=fake_append_event,
            refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(),
        ),
    )

    assert result["reason"] == "packet_arrival_blocked_by_startup_authority"
    assert result["attention_decision_shape"] == "startup_blocked"
    assert result["startup_blocker_kind"] == "import_index_atomicity"
    assert result["safe"] is False
    assert result["may_mutate"] is False
    assert result["closure_check_command"].endswith(
        "check_startup_authority_contract.py --format md"
    )
    event = recorded["event"]
    assert event["wake_receipt"]["attention_decision_shape"] == "startup_blocked"
    assert event["wake_receipt"]["startup_blocker"] == (
        "startup authority: import_index_atomicity"
    )


def test_maybe_wake_posted_reviewer_packet_skips_synthetic_target() -> None:
    def fail_refresh_status_snapshot(**_kwargs):
        raise AssertionError("synthetic targets must not refresh wake state")

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={},
        packet={
            "packet_id": "pkt-status",
            "to_agent": "system",
            "kind": "system_notice",
            "requested_action": "",
            "status": "pending",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fail_refresh_status_snapshot,
        ),
    )

    assert result == {
        "attempted": False,
        "woke": False,
        "reason": "non_conductor_target",
        "packet_id": "pkt-status",
        "requested_action": "",
    }


def test_maybe_wake_posted_reviewer_packet_reports_missing_runtime_paths() -> None:
    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths={},
        packet={"packet_id": "pkt-codex", "to_agent": "codex", "kind": "finding"},
    )

    assert result == {
        "attempted": True,
        "woke": False,
        "reason": "missing_runtime_paths",
        "packet_id": "pkt-codex",
        "requested_action": "",
        "warnings": [
            "Missing runtime paths for reviewer wake: bridge_path, review_channel_path, status_dir"
        ],
    }


def test_maybe_wake_posted_reviewer_packet_accepts_runtime_paths_object() -> None:
    observed: dict[str, object] = {}

    def fake_refresh_status_snapshot(**_kwargs):
        return SimpleNamespace(
            bridge_liveness={
                "reviewer_mode": "active_dual_agent",
                "session_state_hints": {
                    "codex": {"state": "waiting_for_user_input"},
                },
            },
            review_state=SimpleNamespace(
                to_dict=lambda: {
                    "packet_inbox": {
                        "attention_revision": "rev-2",
                        "agents": [
                            {
                                "agent": "codex",
                                "attention_status": "review_needed",
                                "wake_reason": "finding_pending",
                                "latest_finding_packet_id": "pkt-find-runtime",
                            }
                        ],
                    },
                    "packets": [
                        {
                            "packet_id": "pkt-find-runtime",
                            "to_agent": "codex",
                            "kind": "finding",
                            "requested_action": "",
                        }
                    ],
                    "coordination": {"resync_required": False},
                }
            ),
        )

    def fake_maybe_wake(**kwargs):
        observed["paths"] = kwargs["paths"]
        return {
            "attempted": True,
            "woke": True,
            "reason": "launched",
            "packet_id": "pkt-find-runtime",
            "requested_action": "",
        }

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths=RuntimePaths(
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
            bridge_path=Path("/tmp/repo/bridge.md"),
            status_dir=Path("/tmp/repo/dev/reports/review_channel/latest"),
            promotion_plan_path=Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            artifact_paths=SimpleNamespace(
                artifact_root="/tmp/repo/dev/reports/review_channel"
            ),
        ),
        packet={
            "packet_id": "pkt-find-runtime",
            "to_agent": "codex",
            "kind": "finding",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fake_refresh_status_snapshot,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=lambda **_kwargs: "remote_control",
            maybe_wake_waiting_reviewer_conductor_fn=fake_maybe_wake,
            load_or_refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(
                review_state={}
            ),
        ),
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-find-runtime",
        "requested_action": "",
    }
    assert observed["paths"] == {
        "bridge_path": Path("/tmp/repo/bridge.md"),
        "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
        "status_dir": Path("/tmp/repo/dev/reports/review_channel/latest"),
        "promotion_plan_path": Path("/tmp/repo/dev/active/ai_governance_platform.md"),
        "artifact_paths": RuntimePaths(
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
            bridge_path=Path("/tmp/repo/bridge.md"),
            status_dir=Path("/tmp/repo/dev/reports/review_channel/latest"),
            promotion_plan_path=Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            artifact_paths=SimpleNamespace(
                artifact_root="/tmp/repo/dev/reports/review_channel"
            ),
        ).artifact_paths,
    }


def test_maybe_wake_posted_reviewer_packet_prefers_event_review_state_payload() -> None:
    observed: dict[str, object] = {}

    def fake_refresh_status_snapshot(**_kwargs):
        return SimpleNamespace(
            bridge_liveness={
                "reviewer_mode": "active_dual_agent",
                "session_state_hints": {
                    "codex": {"state": "waiting_for_user_input"},
                },
            },
            review_state=SimpleNamespace(
                to_dict=lambda: {
                    "packet_inbox": {"attention_revision": "stale"},
                    "packets": [],
                }
            ),
        )

    def fake_maybe_wake(**kwargs):
        observed["report"] = kwargs["report"]
        observed["operator_interaction_mode"] = kwargs["operator_interaction_mode"]
        return {
            "attempted": True,
            "woke": True,
            "reason": "launched",
            "packet_id": "pkt-event",
            "requested_action": "",
        }

    result = maybe_wake_posted_reviewer_packet(
        args=SimpleNamespace(execution_mode="event-backed"),
        repo_root=Path("/tmp/repo"),
        paths=RuntimePaths(
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
            bridge_path=Path("/tmp/repo/bridge.md"),
            status_dir=Path("/tmp/repo/dev/reports/review_channel/latest"),
            promotion_plan_path=Path("/tmp/repo/dev/active/ai_governance_platform.md"),
            artifact_paths=SimpleNamespace(
                artifact_root="/tmp/repo/dev/reports/review_channel"
            ),
        ),
        packet={
            "packet_id": "pkt-event",
            "to_agent": "codex",
            "kind": "finding",
        },
        deps=EventPostWakeDeps(
            refresh_status_snapshot_fn=fake_refresh_status_snapshot,
            scan_repo_governance_fn=lambda _repo_root: SimpleNamespace(),
            derive_operator_interaction_mode_fn=lambda **_kwargs: "local_terminal",
            maybe_wake_waiting_reviewer_conductor_fn=fake_maybe_wake,
            load_or_refresh_event_bundle_fn=lambda **_kwargs: SimpleNamespace(
                review_state={
                    "packet_inbox": {
                        "attention_revision": "fresh",
                        "agents": [
                            {
                                "agent": "codex",
                                "attention_status": "review_needed",
                                "wake_reason": "finding_pending",
                                "latest_finding_packet_id": "pkt-event",
                            }
                        ],
                    },
                    "packets": [
                        {
                            "packet_id": "pkt-event",
                            "to_agent": "codex",
                            "kind": "finding",
                            "requested_action": "",
                        }
                    ],
                    "coordination": {"resync_required": True},
                    "agent_loop_decisions": [
                        {
                            "actor_id": "codex",
                            "active_packet_id": "pkt-event",
                        }
                    ],
                    "agent_work_board": {
                        "rows": [
                            {
                                "actor_id": "codex",
                                "active_packet_id": "pkt-event",
                            }
                        ]
                    },
                    "agent_sync": {"agents": {"codex": {}}},
                    "coordination_state": {
                        "coordination_topology": "multi_agent_active",
                    },
                    "authority_snapshot": {
                        "mutation_owner": "claude",
                        "verification_owner": "codex",
                        "verification_status": "live",
                        "watcher_owner": "claude",
                        "watcher_status": "live",
                    },
                }
            ),
        ),
    )

    assert result == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-event",
        "requested_action": "",
    }
    assert observed["operator_interaction_mode"] == "local_terminal"
    assert observed["report"]["packet_inbox"]["attention_revision"] == "fresh"
    assert observed["report"]["agent_loop_decisions"][0]["active_packet_id"] == "pkt-event"
    assert observed["report"]["agent_work_board"]["rows"][0]["active_packet_id"] == "pkt-event"
    assert observed["report"]["agent_sync"] == {"agents": {"codex": {}}}
    assert observed["report"]["coordination_state"] == {
        "coordination_topology": "multi_agent_active"
    }
    assert observed["report"]["authority_snapshot"]["watcher_owner"] == "claude"
    assert observed["report"]["coordination"] == {"resync_required": True}


def test_run_event_action_attaches_reviewer_wake_for_post(monkeypatch) -> None:
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.run_post_action",
        lambda **_kwargs: (
            {"packet": {"packet_id": "pkt-1", "to_agent": "codex"}},
            0,
            {},
        ),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.maybe_wake_posted_reviewer_packet",
        lambda **_kwargs: {
            "attempted": True,
            "woke": True,
            "reason": "launched",
            "packet_id": "pkt-1",
            "requested_action": "restore_reviewer_turn",
        },
    )

    report, exit_code = _run_event_action(
        args=SimpleNamespace(action="post"),
        repo_root=Path("/tmp/repo"),
        paths={
            "review_channel_path": Path("/tmp/repo/dev/active/review_channel.md"),
            "artifact_paths": SimpleNamespace(artifact_root="/tmp/repo/dev/reports/review_channel"),
        },
    )

    assert exit_code == 0
    assert report["reviewer_wake"] == {
        "attempted": True,
        "woke": True,
        "reason": "launched",
        "packet_id": "pkt-1",
        "requested_action": "restore_reviewer_turn",
    }


def test_run_event_action_syncs_bridge_when_post_becomes_instruction(
    monkeypatch,
    tmp_path: Path,
) -> None:
    bridge_path = tmp_path / "bridge.md"
    bridge_path.write_text("# Review Bridge\n\nstale\n", encoding="utf-8")
    observed: dict[str, object] = {}

    review_state_payload = {
        "queue": {
            "derived_next_instruction": "- Review the SYSTEM_MAP S0 receipt.",
            "derived_next_instruction_source": {"packet_id": "pkt-instruction"},
        },
        "current_session": {
            "current_instruction": "- Review the SYSTEM_MAP S0 receipt.",
            "current_instruction_revision": "rev-s0",
        },
    }

    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.run_post_action",
        lambda **_kwargs: (
            {
                "packet": {
                    "packet_id": "pkt-instruction",
                    "to_agent": "claude",
                    "kind": "instruction",
                }
            },
            0,
            review_state_payload,
        ),
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.maybe_wake_posted_reviewer_packet",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.compute_non_audit_worktree_hash",
        lambda **_kwargs: "b" * 64,
    )

    def fake_render_bridge_projection(**kwargs):
        observed["review_state"] = kwargs["review_state"]
        observed["last_worktree_hash"] = kwargs["last_worktree_hash"]
        return (
            "# Review Bridge\n\n## Current Instruction For Claude\n\n"
            "- Review the SYSTEM_MAP S0 receipt.\n",
            object(),
        )

    monkeypatch.setattr(
        "dev.scripts.devctl.commands.review_channel.event_handler.render_bridge_projection",
        fake_render_bridge_projection,
    )

    report, exit_code = _run_event_action(
        args=SimpleNamespace(action="post"),
        repo_root=tmp_path,
        paths={
            "review_channel_path": tmp_path / "dev/active/review_channel.md",
            "bridge_path": bridge_path,
            "artifact_paths": SimpleNamespace(
                artifact_root=tmp_path / "dev/reports/review_channel"
            ),
        },
    )

    assert exit_code == 0
    assert report["post_bridge_sync"] == {
        "synced": True,
        "reason": "posted_current_instruction",
        "packet_id": "pkt-instruction",
    }
    assert observed["review_state"] == review_state_payload
    assert observed["last_worktree_hash"] == "b" * 64
    assert "- Review the SYSTEM_MAP S0 receipt." in bridge_path.read_text(
        encoding="utf-8"
    )
