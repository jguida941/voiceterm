from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.event_watch_support import (
    EventWatchContext,
    load_target_packets,
)
from dev.scripts.devctl.commands.review_channel.event_handler import (
    _build_event_report,
)
from dev.scripts.devctl.review_channel.event_reducer_inbox import filter_inbox_packets
from dev.scripts.devctl.review_channel.event_render import render_event_md
from dev.scripts.devctl.review_channel.event_store import ReviewChannelArtifactPaths
from dev.scripts.devctl.review_channel.packet_body_observation import packet_body_digest
from dev.scripts.devctl.review_channel.projection_bundle import (
    ReviewChannelProjectionPaths,
)


def test_targeted_inbox_queue_uses_target_filtered_packets() -> None:
    args = SimpleNamespace(
        action="inbox",
        target="codex",
        status="pending",
        limit=20,
        terminal_profile=None,
        approval_mode=None,
    )
    bundle = SimpleNamespace(
        review_state={
            "warnings": [],
            "errors": [],
            "queue": {
                "pending_total": 2,
                "pending_codex": 1,
                "pending_claude": 1,
                "derived_next_instruction": "Priority action_request: Claude work",
                "derived_next_instruction_source": {
                    "packet_id": "rev_pkt_claude",
                    "to_agent": "claude",
                },
                "stale_packet_count": 0,
            },
        },
        projection_paths=ReviewChannelProjectionPaths(
            root_dir="",
            review_state_path="",
            compact_path="",
            full_path="",
            actions_path="",
            trace_path="",
            latest_markdown_path="",
            agent_registry_path="",
            commit_pipeline_path="",
        ),
        artifact_paths=ReviewChannelArtifactPaths(
            artifact_root="",
            event_log_path="",
            state_path="",
            projections_root="",
        ),
    )

    report, exit_code = _build_event_report(
        args=args,
        bundle=bundle,
        packets=[
            {
                "packet_id": "rev_pkt_codex_finding",
                "status": "pending",
                "kind": "finding",
                "summary": "Codex finding",
                "from_agent": "claude",
                "to_agent": "codex",
            }
        ],
    )

    assert exit_code == 0
    assert report["queue"]["pending_total"] == 1
    assert report["queue"]["pending_codex"] == 1
    assert report["queue"]["derived_next_instruction_source"] == {}


def test_targeted_inbox_surfaces_agent_sync_pending_when_filter_is_empty() -> None:
    args = SimpleNamespace(
        action="inbox",
        target="claude",
        status="pending",
        limit=20,
        terminal_profile=None,
        approval_mode=None,
    )
    bundle = SimpleNamespace(
        review_state={
            "warnings": [],
            "errors": [],
            "queue": {"pending_total": 0, "stale_packet_count": 0},
            "agent_sync": {
                "agents": {
                    "claude": {
                        "pending_packets_to_me": ["rev_pkt_finding"],
                    }
                }
            },
        },
        projection_paths=ReviewChannelProjectionPaths(
            root_dir="",
            review_state_path="",
            compact_path="",
            full_path="",
            actions_path="",
            trace_path="",
            latest_markdown_path="",
            agent_registry_path="",
            commit_pipeline_path="",
        ),
        artifact_paths=ReviewChannelArtifactPaths(
            artifact_root="",
            event_log_path="",
            state_path="",
            projections_root="",
        ),
    )

    report, exit_code = _build_event_report(args=args, bundle=bundle, packets=[])

    assert exit_code == 0
    assert report["queue"]["pending_total"] == 0
    assert report["queue"]["agent_sync_pending_total"] == 1
    assert report["queue"]["agent_sync_pending_packet_ids"] == ["rev_pkt_finding"]
    assert "outside the actionable inbox filter" in report["queue"]["filtered_pending_note"]


def test_targeted_inbox_hides_agent_sync_ids_without_live_packet_rows() -> None:
    args = SimpleNamespace(
        action="inbox",
        target="codex",
        status="pending",
        limit=20,
        terminal_profile=None,
        approval_mode=None,
    )
    bundle = SimpleNamespace(
        review_state={
            "warnings": [],
            "errors": [],
            "queue": {"pending_total": 0, "stale_packet_count": 0},
            "packets": [
                {
                    "packet_id": "rev_pkt_bound",
                    "to_agent": "codex",
                    "from_agent": "claude",
                    "kind": "finding",
                    "status": "pending",
                    "lifecycle_current_state": "pending",
                    "durable_binding": {
                        "status": "inserted",
                        "binding_target_kind": "plan_row",
                    },
                }
            ],
            "agent_sync": {
                "agents": {
                    "codex": {
                        "pending_packets_to_me": ["rev_pkt_bound"],
                    }
                }
            },
        },
        projection_paths=ReviewChannelProjectionPaths(
            root_dir="",
            review_state_path="",
            compact_path="",
            full_path="",
            actions_path="",
            trace_path="",
            latest_markdown_path="",
            agent_registry_path="",
            commit_pipeline_path="",
        ),
        artifact_paths=ReviewChannelArtifactPaths(
            artifact_root="",
            event_log_path="",
            state_path="",
            projections_root="",
        ),
    )

    report, exit_code = _build_event_report(args=args, bundle=bundle, packets=[])

    assert exit_code == 0
    assert report["queue"]["pending_total"] == 0
    assert "agent_sync_pending_total" not in report["queue"]


def test_targeted_inbox_surfaces_route_scoped_plan_packet_until_read() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_plan_bound",
                "to_agent": "codex",
                "from_agent": "operator",
                "kind": "finding",
                "status": "pending",
                "target_role": "implementer",
                "body": "Route-scoped inventory needs actor visibility.",
                "durable_binding": {
                    "status": "inserted",
                    "binding_target_kind": "plan_row",
                },
            }
        ]
    }

    packets = filter_inbox_packets(
        review_state,
        target="codex",
        status="pending",
    )

    assert [packet["packet_id"] for packet in packets] == ["rev_pkt_plan_bound"]
    assert packets[0]["inbox_routing_status"] == "route_scoped_to_actor"


def test_targeted_inbox_markdown_keeps_unread_route_scoped_plan_packet_live() -> None:
    packet = {
        "packet_id": "rev_pkt_plan_bound",
        "to_agent": "claude",
        "from_agent": "codex",
        "kind": "continuation_anchor",
        "summary": "Current-row communication proof",
        "status": "pending",
        "target_role": "implementer",
        "target_session_id": "claude-session",
        "latest_event_id": "rev_evt_85803",
        "body": "Reply with typed task_progress.",
        "durable_binding": {
            "status": "inserted",
            "binding_target_kind": "plan_row_evidence",
        },
        "disposition": {
            "sink": "queued",
            "resolution_anchor": "slice_target:claude_packet_queue",
        },
    }
    older_live_packet = {
        "packet_id": "rev_pkt_old_action",
        "to_agent": "claude",
        "from_agent": "operator",
        "kind": "action_request",
        "summary": "Older action request",
        "status": "pending",
        "target_role": "implementer",
        "latest_event_id": "rev_evt_85774",
    }
    review_state = {"packets": [older_live_packet, packet]}

    packets = filter_inbox_packets(
        review_state,
        target="claude",
        target_role="implementer",
        target_session_id="claude-session",
        status="pending",
    )
    markdown = render_event_md(
        {
            "ok": True,
            "action": "inbox",
            "execution_mode": "event-backed",
            "queue": {"pending_total": 1},
            "target": "claude",
            "status_filter": "pending",
            "limit": 20,
            "packets": packets,
        }
    )

    assert "## Live Packets" in markdown
    assert markdown.index("rev_pkt_plan_bound: pending") < markdown.index(
        "rev_pkt_old_action: pending"
    )
    assert "rev_pkt_plan_bound: pending" in markdown
    assert "## Packet History" not in markdown


def test_targeted_role_inbox_marks_wrong_role_packet_instead_of_hiding() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_wrong_role",
                "to_agent": "codex",
                "from_agent": "operator",
                "kind": "finding",
                "status": "pending",
                "target_role": "implementer",
                "body": "This is addressed to codex but a different role.",
                "durable_binding": {
                    "status": "inserted",
                    "binding_target_kind": "plan_row",
                },
            }
        ]
    }

    packets = filter_inbox_packets(
        review_state,
        target="codex",
        target_role="reviewer",
        status="pending",
    )

    assert [packet["packet_id"] for packet in packets] == ["rev_pkt_wrong_role"]
    assert packets[0]["inbox_routing_status"] == "wrong_role_for_actor"
    assert packets[0]["inbox_routing_expected_role"] == "reviewer"
    assert packets[0]["inbox_routing_packet_role"] == "implementer"


def test_targeted_inbox_drops_route_scoped_packet_after_actor_reads_body() -> None:
    packet = {
        "packet_id": "rev_pkt_wrong_role",
        "to_agent": "codex",
        "from_agent": "operator",
        "kind": "finding",
        "status": "pending",
        "target_role": "implementer",
        "body": "Codex reviewer opened this routing mismatch.",
        "durable_binding": {
            "status": "inserted",
            "binding_target_kind": "plan_row",
        },
    }
    packet["body_observation_events"] = [
        {
            "body_observed_by": "codex",
            "body_observed_role": "reviewer",
            "body_observed_session_id": "codex-review-session",
            "body_digest": packet_body_digest(packet),
        }
    ]
    review_state = {"packets": [packet]}

    packets = filter_inbox_packets(
        review_state,
        target="codex",
        status="pending",
    )

    assert packets == []


def test_inbox_filter_honors_session_scope_when_present() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_s1",
                "to_agent": "claude",
                "status": "pending",
                "target_role": "implementer",
                "target_session_id": "s1",
            },
            {
                "packet_id": "rev_pkt_s2",
                "to_agent": "claude",
                "status": "pending",
                "target_role": "implementer",
                "target_session_id": "s2",
            },
            {
                "packet_id": "rev_pkt_legacy",
                "to_agent": "claude",
                "status": "pending",
            },
        ]
    }

    packets = filter_inbox_packets(
        review_state,
        target="claude",
        target_role="implementer",
        target_session_id="s1",
        status="pending",
    )

    assert [packet["packet_id"] for packet in packets] == ["rev_pkt_s1"]


def test_inbox_filter_honors_role_scope_without_delivery_target() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_impl_a",
                "to_agent": "delivery-a",
                "status": "pending",
                "target_role": "implementer",
                "target_session_id": "s1",
            },
            {
                "packet_id": "rev_pkt_impl_b",
                "to_agent": "delivery-b",
                "status": "pending",
                "target_role": "implementer",
                "target_session_id": "s2",
            },
            {
                "packet_id": "rev_pkt_review",
                "to_agent": "delivery-a",
                "status": "pending",
                "target_role": "reviewer",
                "target_session_id": "s3",
            },
            {
                "packet_id": "rev_pkt_legacy",
                "to_agent": "delivery-a",
                "status": "pending",
            },
        ]
    }

    packets = filter_inbox_packets(
        review_state,
        target_role="implementer",
        status="pending",
    )

    assert [packet["packet_id"] for packet in packets] == [
        "rev_pkt_impl_a",
        "rev_pkt_impl_b",
    ]


def test_role_scoped_inbox_queue_uses_role_filtered_packets() -> None:
    args = SimpleNamespace(
        action="inbox",
        target="",
        target_role="implementer",
        target_session_id="",
        status="pending",
        limit=20,
        terminal_profile=None,
        approval_mode=None,
    )
    bundle = SimpleNamespace(
        review_state={
            "warnings": [],
            "errors": [],
            "queue": {
                "pending_total": 2,
                "pending_codex": 1,
                "pending_claude": 1,
                "stale_packet_count": 0,
            },
        },
        projection_paths=ReviewChannelProjectionPaths(
            root_dir="",
            review_state_path="",
            compact_path="",
            full_path="",
            actions_path="",
            trace_path="",
            latest_markdown_path="",
            agent_registry_path="",
            commit_pipeline_path="",
        ),
        artifact_paths=ReviewChannelArtifactPaths(
            artifact_root="",
            event_log_path="",
            state_path="",
            projections_root="",
        ),
    )

    report, exit_code = _build_event_report(
        args=args,
        bundle=bundle,
        packets=[
            {
                "packet_id": "rev_pkt_impl_a",
                "status": "pending",
                "kind": "task_progress",
                "summary": "Implementer lane packet",
                "to_agent": "delivery-a",
                "target_role": "implementer",
            }
        ],
    )

    assert exit_code == 0
    assert report["target_role"] == "implementer"
    assert report["queue"]["pending_total"] == 1
    assert report["queue"]["pending_role_implementer"] == 1
    assert report["queue"]["pending_codex"] == 0
    assert report["queue"]["pending_claude"] == 0
    assert report["queue"]["filtered_scope"] == {
        "target": "",
        "target_role": "implementer",
        "target_session_id": "",
        "scope_key": "role_implementer",
    }


def test_load_target_packets_accepts_role_scope_without_delivery_target() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_dashboard",
                "to_agent": "delivery-a",
                "from_agent": "system",
                "kind": "instruction",
                "status": "pending",
                "target_role": "dashboard",
                "target_session_id": "session-dashboard",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    _, packets = load_target_packets(
        context=EventWatchContext(
            args=SimpleNamespace(
                target="",
                target_role="dashboard",
                target_session_id="",
                status="pending",
                limit=20,
            ),
            bundle=SimpleNamespace(review_state=review_state),
            repo_root=Path("/tmp/repo"),
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
            artifact_paths=SimpleNamespace(
                artifact_root="/tmp/repo/dev/reports/review_channel"
            ),
        ),
        observe_action_requests=False,
    )

    assert [packet["packet_id"] for packet in packets] == ["rev_pkt_dashboard"]


def test_targeted_inbox_visibility_does_not_depend_on_actor_flag() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_scoped",
                "to_agent": "claude",
                "from_agent": "codex",
                "kind": "instruction",
                "status": "pending",
                "target_role": "dashboard",
                "target_session_id": "session-dashboard",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            }
        ]
    }

    def _load_packets_for_args(args):
        _, packets = load_target_packets(
            context=EventWatchContext(
                args=args,
                bundle=SimpleNamespace(review_state=review_state),
                repo_root=Path("/tmp/repo"),
                review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
                artifact_paths=SimpleNamespace(
                    artifact_root="/tmp/repo/dev/reports/review_channel"
                ),
            ),
            observe_action_requests=False,
        )
        return packets

    without_actor = _load_packets_for_args(
        SimpleNamespace(target="claude", status="pending", limit=20)
    )
    with_actor = _load_packets_for_args(
        SimpleNamespace(target="claude", actor="claude", status="pending", limit=20)
    )

    assert [packet["packet_id"] for packet in without_actor] == ["rev_pkt_scoped"]
    assert [packet["packet_id"] for packet in with_actor] == ["rev_pkt_scoped"]


def test_v4554_inbox_surfaces_freshest_packet_first() -> None:
    """v4.55.4 (rev_pkt_4786/4787) regression: when develop next names a
    fresh plan-bound packet for the agent, the inbox view must surface
    that packet at the top instead of older transport debt.
    `filter_inbox_packets` sorts by `latest_event_id` descending so the
    inbox and `develop next` agree on which packet is current.
    """
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_old_debt",
                "status": "pending",
                "kind": "task_progress",
                "from_agent": "codex",
                "to_agent": "claude",
                "latest_event_id": "rev_evt_84500",
                "posted_at": "2026-05-20T10:00:00Z",
            },
            {
                "packet_id": "rev_pkt_current_goal",
                "status": "pending",
                "kind": "finding",
                "attention_urgency": "blocking",
                "from_agent": "codex",
                "to_agent": "claude",
                "latest_event_id": "rev_evt_85258",
                "posted_at": "2026-05-21T14:00:57Z",
            },
            {
                "packet_id": "rev_pkt_middle_age",
                "status": "pending",
                "kind": "task_started",
                "from_agent": "codex",
                "to_agent": "claude",
                "latest_event_id": "rev_evt_85000",
                "posted_at": "2026-05-21T08:00:00Z",
            },
        ],
    }

    packets = filter_inbox_packets(
        review_state,
        target="claude",
        status="pending",
        limit=20,
    )

    assert [packet["packet_id"] for packet in packets] == [
        "rev_pkt_current_goal",
        "rev_pkt_middle_age",
        "rev_pkt_old_debt",
    ], (
        "v4.55.4 inbox must surface freshest packet first; got "
        f"{[p['packet_id'] for p in packets]!r}"
    )
