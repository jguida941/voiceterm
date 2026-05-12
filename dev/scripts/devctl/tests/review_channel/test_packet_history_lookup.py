"""Regressions for direct packet history lookup."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from dev.scripts.devctl.commands.review_channel_command.constants import (
    ReviewChannelAction,
)
from dev.scripts.devctl.commands.review_channel_command.helpers import _validate_args
from dev.scripts.devctl.commands.review_channel.event_handler import _run_event_action
from dev.scripts.devctl.review_channel.event_reducer_inbox import (
    filter_history_events,
    filter_history_packets,
)
from dev.scripts.devctl.review_channel.event_reducer import refresh_event_bundle
from dev.scripts.devctl.review_channel.event_store import (
    ReviewChannelArtifactPaths,
    append_event,
)
from dev.scripts.devctl.review_channel.packet_body_observation import (
    PACKET_BODY_OBSERVATION_EVENT_TYPE,
    packet_body_observation_payload_for_packet,
    record_packet_body_observation,
)


def test_history_packet_id_finds_live_pending_packet_body() -> None:
    review_state = {
        "packets": [
            {
                "packet_id": "rev_pkt_100",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "summary": "Exact packet",
                "body": "The exact packet body must be readable.",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
            {
                "packet_id": "rev_pkt_101",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "finding",
                "status": "pending",
                "summary": "Other packet",
                "body": "Wrong body",
                "expires_at_utc": "2999-01-01T00:00:00Z",
            },
        ]
    }

    packets = filter_history_packets(review_state, packet_id="rev_pkt_100")

    assert [packet["packet_id"] for packet in packets] == ["rev_pkt_100"]
    assert packets[0]["body"] == "The exact packet body must be readable."


def test_history_events_filter_by_packet_id() -> None:
    events = [
        {"event_id": "rev_evt_1", "packet_id": "rev_pkt_100"},
        {"event_id": "rev_evt_2", "packet_id": "rev_pkt_101"},
        {"event_id": "rev_evt_3", "packet_id": "rev_pkt_100"},
    ]

    filtered = filter_history_events(events, packet_id="rev_pkt_100")

    assert [event["event_id"] for event in filtered] == ["rev_evt_1", "rev_evt_3"]


def test_show_body_observation_records_typed_packet_receipt(tmp_path) -> None:
    review_channel_path = tmp_path / "review_channel.md"
    review_channel_path.write_text("", encoding="utf-8")
    artifact_root = tmp_path / "review_artifacts"
    artifact_paths = ReviewChannelArtifactPaths(
        artifact_root=str(artifact_root),
        event_log_path=str(artifact_root / "events" / "trace.ndjson"),
        state_path=str(tmp_path / "review_state.json"),
        projections_root=str(tmp_path / "projections"),
    )
    append_event(
        artifact_root / "events" / "trace.ndjson",
        {
            "event_type": "packet_posted",
            "timestamp_utc": "2026-05-11T01:00:00Z",
            "project_id": "test-project",
            "session_id": "test-session",
            "trace_id": "trace-test",
            "plan_id": "MP-377",
            "packet_id": "rev_pkt_100",
            "from_agent": "claude",
            "to_agent": "codex",
            "kind": "task_progress",
            "summary": "Unread body",
            "body": "Codex must open this body before continuing.",
            "status": "pending",
        },
        existing_events=[],
    )
    bundle = refresh_event_bundle(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )

    refreshed, event = record_packet_body_observation(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
        bundle=bundle,
        packet=bundle.review_state["packets"][0],
        actor="codex",
        session_id="session-codex",
    )

    assert event is not None
    assert event["event_type"] == PACKET_BODY_OBSERVATION_EVENT_TYPE
    packet = refreshed.review_state["packets"][0]
    assert packet["body_observed_by"] == "codex"
    assert packet["body_observed_event_id"] == event["event_id"]
    assert packet["body_observation_events"][0]["contract_id"] == "PacketBodyObservation"
    assert event["correlation_id"] == packet["correlation_id"]
    assert event["causation_id"].startswith("cause-")
    assert event["run_id"] == packet["run_id"]
    assert (
        packet["body_observation_events"][0]["correlation_id"]
        == packet["correlation_id"]
    )


def test_body_observation_payload_backfills_legacy_lineage_from_packet() -> None:
    payload = packet_body_observation_payload_for_packet(
        {
            "event_id": "rev_evt_2",
            "packet_id": "rev_pkt_100",
            "body_observed_by": "codex",
        },
        {
            "packet_id": "rev_pkt_100",
            "correlation_id": "corr-packet",
            "causation_id": "cause-packet",
            "run_id": "run-packet",
        },
    )

    assert payload["correlation_id"] == "corr-packet"
    assert payload["causation_id"] == "cause-packet"
    assert payload["run_id"] == "run-packet"


def test_body_observation_payload_derives_legacy_lineage_without_packet_fields() -> None:
    payload = packet_body_observation_payload_for_packet(
        {
            "event_id": "rev_evt_2",
            "packet_id": "rev_pkt_100",
            "body_observed_by": "codex",
            "source_packet_event_id": "rev_evt_1",
        },
        {"packet_id": "rev_pkt_100"},
    )

    assert payload["correlation_id"].startswith("corr-")
    assert payload["causation_id"].startswith("cause-")
    assert payload["run_id"].startswith("run-")


def test_show_respects_external_artifact_write_suppression(
    tmp_path, monkeypatch
) -> None:
    review_channel_path = tmp_path / "review_channel.md"
    review_channel_path.write_text("", encoding="utf-8")
    artifact_root = tmp_path / "review_artifacts"
    event_log_path = artifact_root / "events" / "trace.ndjson"
    artifact_paths = ReviewChannelArtifactPaths(
        artifact_root=str(artifact_root),
        event_log_path=str(event_log_path),
        state_path=str(tmp_path / "review_state.json"),
        projections_root=str(tmp_path / "projections"),
    )
    append_event(
        event_log_path,
        {
            "event_type": "packet_posted",
            "timestamp_utc": "2026-05-11T01:00:00Z",
            "project_id": "test-project",
            "session_id": "test-session",
            "trace_id": "trace-test",
            "plan_id": "MP-377",
            "packet_id": "rev_pkt_100",
            "from_agent": "claude",
            "to_agent": "codex",
            "kind": "task_progress",
            "summary": "Unread body",
            "body": "Codex must open this body before continuing.",
            "status": "pending",
        },
        existing_events=[],
    )
    args = SimpleNamespace(
        action="show",
        actor="codex",
        approval_mode=None,
        include_outcomes=False,
        limit=20,
        packet_id="rev_pkt_100",
        status=None,
        target=None,
        target_role="",
        target_session_id="",
        terminal_profile=None,
        trace_id=None,
    )

    monkeypatch.setenv("DEVCTL_NO_ARTIFACT_WRITES", "1")

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"] is None
    assert report["packet"]["packet_id"] == "rev_pkt_100"
    assert not report["packet"].get("body_observed_event_id")
    assert not report["packet"].get("body_observation_events")
    events = [
        line
        for line in event_log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(events) == 1


def _show_args(**overrides: object) -> SimpleNamespace:
    args = {
        "action": "show",
        "await_ack_seconds": 0,
        "expires_in_minutes": 30,
        "follow": False,
        "follow_interval_seconds": 120,
        "format": "md",
        "limit": 20,
        "max_follow_snapshots": 0,
        "packet_id": "rev_pkt_100",
        "rollover_threshold_pct": 50,
        "stale_minutes": 30,
        "start_publisher_if_missing": False,
        "stop_grace_seconds": 0.0,
        "to_agent": None,
    }
    args.update(overrides)
    return SimpleNamespace(**args)


def test_show_validation_requires_packet_id() -> None:
    with pytest.raises(ValueError, match="--packet-id is required"):
        _validate_args(_show_args(packet_id=None), ReviewChannelAction.SHOW)


def test_show_validation_still_rejects_post_only_to_agent() -> None:
    with pytest.raises(ValueError, match="--to-agent is only valid"):
        _validate_args(_show_args(to_agent="codex"), ReviewChannelAction.SHOW)
