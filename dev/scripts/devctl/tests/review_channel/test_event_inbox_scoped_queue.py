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
from dev.scripts.devctl.review_channel.event_store import ReviewChannelArtifactPaths
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
