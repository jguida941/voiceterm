"""Regressions for direct packet history lookup."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dev.scripts.devctl import cli
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
from dev.scripts.devctl.review_channel.pending_packets import live_pending_packets
from dev.scripts.devctl.review_channel.packet_body_observation import (
    PACKET_BODY_OBSERVATION_EVENT_TYPE,
    packet_body_observation_payload_for_packet,
    record_packet_body_observation,
)
from dev.scripts.devctl.review_channel.packet_semantic_ingestion import (
    PACKET_SEMANTIC_INGESTION_EVENT_TYPE,
)
from dev.scripts.devctl.review_channel.packet_absorption import (
    PACKET_ABSORPTION_EVENT_TYPE,
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
            "expires_at_utc": "2999-01-01T00:00:00Z",
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
    assert packet["packet_observation_receipt"]["contract_id"] == (
        "PacketObservationReceipt"
    )
    assert packet["packet_observation_receipt"]["observed_packet_id"] == "rev_pkt_100"
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
            "expires_at_utc": "2999-01-01T00:00:00Z",
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


def test_ingest_requires_prior_matching_body_observation(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    args = _show_args(
        action="ingest",
        actor="codex",
        semantic_action_item=[_semantic_action_item_json("rev_pkt_100")],
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert report["ok"] is False
    assert "matching_packet_body_observation_required" in report["errors"]


def test_ingest_records_semantic_receipt_after_matching_show(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
    )
    show_args = _show_args(
        action="show",
        actor="codex",
        target_role="reviewer",
        target_session_id="session-a",
    )
    show_report, show_exit = _run_event_action(
        args=show_args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    assert show_exit == 0
    assert show_report["event"]["event_type"] == PACKET_BODY_OBSERVATION_EVENT_TYPE
    assert show_report["packet"]["packet_observation_receipt"]["contract_id"] == (
        "PacketObservationReceipt"
    )
    drain_report = show_report["packet_attention_drain_report"]
    assert drain_report["contract_id"] == "PacketAttentionDrainReport"
    assert "rev_pkt_100" in drain_report["drained_packet_ids"]
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    ingest_args = _show_args(
        action="ingest",
        actor="codex",
        semantic_action_item=[_semantic_action_item_json("rev_pkt_100")],
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=ingest_args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == PACKET_SEMANTIC_INGESTION_EVENT_TYPE
    receipt = report["packet"]["packet_semantic_ingestion_receipt"]
    assert receipt["contract_id"] == "PacketSemanticIngestionReceipt"
    assert receipt["action_item_rows"][0]["contract_id"] == "PacketSemanticActionItem"


def test_ingest_requires_structured_action_item_rows(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
    )
    show_args = _show_args(
        action="show",
        actor="codex",
        target_role="reviewer",
        target_session_id="session-a",
    )
    _run_event_action(
        args=show_args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    ingest_args = _show_args(
        action="ingest",
        actor="codex",
        semantic_action_item=[],
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=ingest_args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert report["ok"] is False
    assert "packet_semantic_ingestion_requires_action_item_rows" in report["errors"]


def test_show_body_observation_runs_control_decision_gate(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
    )
    args = _show_args(
        action="show",
        actor="codex",
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == PACKET_BODY_OBSERVATION_EVENT_TYPE
    assert report["control_decision_obedience"]["ok"] is True


def test_show_observation_uses_actor_route_not_packet_target_route(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
        actor_id="codex",
        actor_role="reviewer",
        session_id="codex-review-session",
    )
    args = _show_args(
        action="show",
        actor="codex",
        actor_role="reviewer",
        session_id="codex-review-session",
        target_role="implementer",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    event = report["event"]
    assert event["event_type"] == PACKET_BODY_OBSERVATION_EVENT_TYPE
    assert event["body_observed_by"] == "codex"
    assert event["body_observed_role"] == "reviewer"
    assert event["body_observed_session_id"] == "codex-review-session"
    assert report["control_decision_obedience"]["ok"] is True


def test_show_blocks_packet_body_when_actor_route_mismatches_packet_route(
    tmp_path,
) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(
        tmp_path,
        target_role="implementer",
        target_session_id="claude-implementer-session",
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
        actor_id="claude",
        actor_role="dashboard",
        session_id="claude-dashboard-session",
    )
    before = _event_count(artifact_paths)

    report, exit_code = _run_event_action(
        args=_show_args(
            action="show",
            actor="claude",
            actor_role="dashboard",
            session_id="claude-dashboard-session",
            target_role="dashboard",
            target_session_id="claude-dashboard-session",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "packet_route_scope_mismatch" in report["errors"]
    assert report["packet"] is None
    assert report["packets"] == []
    assert "Codex must open this body before continuing." not in json.dumps(report)
    assert _event_count(artifact_paths) == before


def test_ingest_blocks_when_actor_route_mismatches_packet_route(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(
        tmp_path,
        target_role="implementer",
        target_session_id="claude-implementer-session",
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
        actor_id="claude",
        actor_role="implementer",
        session_id="claude-implementer-session",
    )
    _run_event_action(
        args=_show_args(
            action="show",
            actor="claude",
            actor_role="implementer",
            session_id="claude-implementer-session",
            target_role="implementer",
            target_session_id="claude-implementer-session",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
        actor_id="claude",
        actor_role="dashboard",
        session_id="claude-dashboard-session",
    )
    before = _event_count(artifact_paths)

    report, exit_code = _run_event_action(
        args=_show_args(
            action="ingest",
            actor="claude",
            actor_role="dashboard",
            session_id="claude-dashboard-session",
            semantic_action_item=[_semantic_action_item_json("rev_pkt_100")],
            target_role="dashboard",
            target_session_id="claude-dashboard-session",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "packet_route_scope_mismatch" in report["errors"]
    assert _event_count(artifact_paths) == before


def test_absorb_blocks_when_actor_route_mismatches_packet_route(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(
        tmp_path,
        target_role="implementer",
        target_session_id="claude-implementer-session",
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
        actor_id="claude",
        actor_role="implementer",
        session_id="claude-implementer-session",
    )
    _run_event_action(
        args=_show_args(
            action="show",
            actor="claude",
            actor_role="implementer",
            session_id="claude-implementer-session",
            target_role="implementer",
            target_session_id="claude-implementer-session",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
        actor_id="claude",
        actor_role="implementer",
        session_id="claude-implementer-session",
    )
    _run_event_action(
        args=_show_args(
            action="ingest",
            actor="claude",
            actor_role="implementer",
            session_id="claude-implementer-session",
            semantic_action_item=[_semantic_action_item_json("rev_pkt_100")],
            target_role="implementer",
            target_session_id="claude-implementer-session",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        absorption_required=True,
        actor_id="claude",
        actor_role="dashboard",
        session_id="claude-dashboard-session",
    )
    before = _event_count(artifact_paths)

    report, exit_code = _run_event_action(
        args=_show_args(
            action="absorb",
            actor="claude",
            actor_role="dashboard",
            session_id="claude-dashboard-session",
            target_role="dashboard",
            target_session_id="claude-dashboard-session",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "packet_route_scope_mismatch" in report["errors"]
    assert _event_count(artifact_paths) == before


def test_show_blocks_before_body_disclosure_without_control_decision(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    before = _event_count(artifact_paths)
    args = _show_args(
        action="show",
        actor="codex",
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert report["packet"] is None
    assert report["packets"] == []
    assert "Codex must open this body before continuing." not in json.dumps(report)
    assert _event_count(artifact_paths) == before


def test_show_proxy_records_executor_subject_binding(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CODEX_THREAD_ID", "codex-session")
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
        actor_id="claude",
        actor_role="dashboard",
        session_id="claude-session",
        source_snapshot_id="agent-runtime-clock:rev_evt_1",
    )
    args = _show_args(
        action="show",
        actor="claude",
        target_role="dashboard",
        target_session_id="claude-session",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    attempted = report["control_decision_obedience"]["attempted_action_receipt"]
    assert exit_code == 0
    assert report["control_decision_obedience"]["ok"] is True
    assert attempted["executor_actor"] == "codex"
    assert attempted["executor_session_id"] == "codex-session"
    assert attempted["subject_actor"] == "claude"
    assert attempted["subject_role"] == "dashboard"
    assert attempted["subject_session_id"] == "claude-session"
    assert attempted["proxy_execution"] is True
    assert attempted["proxy_authority_ref"] == "agent-runtime-clock:rev_evt_1"


def test_show_proxy_wrong_packet_blocks_before_event_append(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("CODEX_THREAD_ID", "codex-session")
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_other",
        body_open_required=True,
        actor_id="claude",
        actor_role="dashboard",
        session_id="claude-session",
        source_snapshot_id="agent-runtime-clock:rev_evt_1",
    )
    before = _event_count(artifact_paths)
    args = _show_args(
        action="show",
        actor="claude",
        target_role="dashboard",
        target_session_id="claude-session",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert report["control_decision_obedience"]["ok"] is False
    assert _event_count(artifact_paths) == before


def test_ingest_wrong_packet_blocks_before_event_append(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_other",
        semantic_ingestion_required=True,
    )
    show_args = _show_args(
        action="show",
        actor="codex",
        target_role="reviewer",
        target_session_id="session-a",
        allow_missing_control_decision_for_test=True,
    )
    _run_event_action(
        args=show_args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    before = _event_count(artifact_paths)
    ingest_args = _show_args(
        action="ingest",
        actor="codex",
        semantic_action_item=[_semantic_action_item_json("rev_pkt_100")],
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=ingest_args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert report["control_decision_obedience"]["ok"] is False
    assert _event_count(artifact_paths) == before


def test_ack_lifecycle_mutation_blocks_before_event_append(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    before = _event_count(artifact_paths)
    args = _show_args(
        action="ack",
        actor="codex",
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert _event_count(artifact_paths) == before


def test_post_lifecycle_mutation_blocks_before_event_append(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    before = _event_count(artifact_paths)
    args = _show_args(
        action="post",
        actor="codex",
        from_agent="codex",
        to_agent="claude",
        kind="task_progress",
        summary="Blocked post",
        body="This must not append while the controller is waiting.",
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert _event_count(artifact_paths) == before


def test_allowed_finding_post_appends_attempted_action_receipt(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_finding"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="finding",
        summary="Checkpoint authority needed",
        body="Typed finding body",
        evidence_ref=["test:post_finding_allowed"],
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == "packet_posted"
    assert report["control_decision_obedience"]["ok"] is True
    attempted = report["control_decision_obedience"]["attempted_action_receipt"]
    assert attempted["action_kind"] == "review-channel.post"
    assert attempted["argv"][attempted["argv"].index("--kind") + 1] == "finding"
    assert _event_count(artifact_paths) == before + 2


def test_allowed_action_request_post_appends_attempted_action_receipt(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_action_request"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="action_request",
        summary="Checkpoint action request",
        body="Request governed checkpoint staging for the current local patch.",
        requested_action="stage_commit_pipeline",
        target_kind="runtime",
        target_ref="devctl_commit:lifecycle_proxy_absorb_checkpoint",
        target_revision="HEAD",
        full_guard_bundle_evidence="bundle.tooling",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["kind"] == "action_request"
    assert report["packet"]["requested_action"] == "stage_commit_pipeline"
    assert report["packet"]["target_kind"] == "runtime"
    assert report["packet"]["target_ref"].startswith("devctl_commit:")
    assert report["control_decision_obedience"]["ok"] is True
    attempted = report["control_decision_obedience"]["attempted_action_receipt"]
    assert attempted["argv"][attempted["argv"].index("--kind") + 1] == "action_request"
    assert attempted["argv"][attempted["argv"].index("--requested-action") + 1] == (
        "stage_commit_pipeline"
    )
    assert attempted["argv"][attempted["argv"].index("--target-ref") + 1].startswith(
        "devctl_commit:"
    )
    assert _event_count(artifact_paths) == before + 3


def test_non_runtime_implementer_handoff_action_request_passes_with_typed_route(
    tmp_path,
) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_agent_mind(tmp_path, agent="codex", session_id="session-a")
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_action_request"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="action_request",
        summary="Typed implementer handoff",
        body="Implement the role-lane guard under the current plan row.",
        requested_action="implementer_handoff",
        target_kind="plan",
        target_ref="MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        target_role="implementer",
        target_session_id="claude-implementer-session",
        from_agent="codex",
        to_agent="claude",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["kind"] == "action_request"
    assert report["packet"]["requested_action"] == "implementer_handoff"
    assert report["packet"]["target_kind"] == "plan"
    assert report["packet"]["target_ref"] == (
        "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
    )
    assert report["packet"]["target_role"] == "implementer"
    assert report["packet"]["target_session_id"] == "claude-implementer-session"
    assert report["control_decision_obedience"]["ok"] is True
    assert _event_count(artifact_paths) == before + 2


def test_non_runtime_implementer_handoff_is_provider_neutral_claude_to_codex(
    tmp_path,
) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_agent_mind(tmp_path, agent="claude", session_id="claude-review-session")
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        actor_id="claude",
        actor_role="reviewer",
        session_id="claude-review-session",
        allowed_actions=["review-channel.post_action_request"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        actor="claude",
        actor_role="reviewer",
        session_id="claude-review-session",
        kind="action_request",
        summary="Typed implementer handoff",
        body="Implement the role-lane guard under the current plan row.",
        requested_action="implementer_handoff",
        target_kind="plan",
        target_ref="MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        target_role="implementer",
        from_agent="claude",
        to_agent="codex",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["from_agent"] == "claude"
    assert report["packet"]["to_agent"] == "codex"
    assert report["packet"]["actor_role"] == "reviewer"
    assert report["packet"]["target_role"] == "implementer"
    assert report["control_decision_obedience"]["ok"] is True
    assert _event_count(artifact_paths) == before + 2


def test_non_runtime_implementer_handoff_rejects_implementer_source_role(
    tmp_path,
) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_agent_mind(tmp_path, agent="codex", session_id="codex-implementer-session")
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        actor_id="codex",
        actor_role="implementer",
        session_id="codex-implementer-session",
        allowed_actions=["review-channel.post_action_request"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        actor="codex",
        actor_role="implementer",
        session_id="codex-implementer-session",
        kind="action_request",
        summary="Typed implementer handoff",
        body="Implementer role cannot self-route implementer handoff.",
        requested_action="implementer_handoff",
        target_kind="plan",
        target_ref="MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        target_role="implementer",
        from_agent="codex",
        to_agent="claude",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert report["control_decision_obedience"]["ok"] is False
    assert _event_count(artifact_paths) == before


def test_non_runtime_implementer_handoff_without_allowed_action_blocks(
    tmp_path,
) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_finding"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="action_request",
        summary="Typed implementer handoff",
        body="Implement the role-lane guard under the current plan row.",
        requested_action="implementer_handoff",
        target_kind="plan",
        target_ref="MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        target_role="implementer",
        target_session_id="claude-implementer-session",
        from_agent="codex",
        to_agent="claude",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert report["control_decision_obedience"]["ok"] is False
    assert _event_count(artifact_paths) == before


def test_allowed_task_progress_post_appends_attempted_action_receipt(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_task_progress"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="task_progress",
        summary="Phase 0.6.A progress",
        body="Reducer repair is in progress.",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["kind"] == "task_progress"
    assert report["control_decision_obedience"]["ok"] is True
    attempted = report["control_decision_obedience"]["attempted_action_receipt"]
    assert attempted["argv"][attempted["argv"].index("--kind") + 1] == "task_progress"
    assert _event_count(artifact_paths) == before + 2


def test_remote_lane_task_progress_accepts_explicit_control_decision(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    decision_path = tmp_path / "task_progress_decision.json"
    decision_path.write_text(
        json.dumps(
            {
                "contract_id": "AgentLoopDecision",
                "actor_id": "codex",
                "actor_role": "reviewer",
                "session_id": "codex-review-session",
                "decision": "wait",
                "required_action": "wait_for_scoped_packet",
                "may_mutate": False,
                "can_run_next_command": False,
                "allowed_actions": ["review-channel.post_task_progress"],
                "source_latest_event_id": "rev_evt_1",
            }
        ),
        encoding="utf-8",
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="task_progress",
        summary="Remote lane progress",
        body="Codex is sending typed progress to Claude through the remote lane.",
        actor="codex",
        actor_role="reviewer",
        session_id="codex-review-session",
        from_agent="codex",
        to_agent="claude",
        target_role="implementer",
        target_session_id="claude-implementer-session",
        control_decision_input=str(decision_path),
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["from_agent"] == "codex"
    assert report["packet"]["to_agent"] == "claude"
    assert report["packet"]["kind"] == "task_progress"
    assert report["packet"]["target_role"] == "implementer"
    assert report["control_decision_obedience"]["ok"] is True
    attempted = report["control_decision_obedience"]["attempted_action_receipt"]
    assert attempted["actor"] == "codex"
    assert attempted["role"] == "reviewer"
    assert attempted["session_id"] == "codex-review-session"
    assert attempted["argv"][attempted["argv"].index("--target-role") + 1] == (
        "implementer"
    )
    assert _event_count(artifact_paths) == before + 2


def test_claude_task_progress_can_reply_to_continuation_anchor_without_post_decision(
    monkeypatch,
    tmp_path,
) -> None:
    _isolate_runtime_session_roots(monkeypatch, tmp_path)
    review_channel_path = tmp_path / "review_channel.md"
    review_channel_path.write_text("", encoding="utf-8")
    artifact_root = tmp_path / "dev/reports/review_channel"
    event_log_path = artifact_root / "events" / "trace.ndjson"
    artifact_paths = ReviewChannelArtifactPaths(
        artifact_root=str(artifact_root),
        event_log_path=str(event_log_path),
        state_path=str(artifact_root / "state/latest.json"),
        projections_root=str(artifact_root / "projections/latest"),
    )
    _write_agent_mind(tmp_path, agent="codex", session_id="codex-session")
    _write_agent_mind(tmp_path, agent="claude", session_id="claude-session")
    append_event(
        event_log_path,
        {
            "event_type": "packet_posted",
            "timestamp_utc": "2026-05-22T16:14:48Z",
            "project_id": "test-project",
            "session_id": "codex-session",
            "trace_id": "trace-test",
            "plan_id": "MP-355",
            "packet_id": "rev_pkt_4829",
            "from_agent": "codex",
            "to_agent": "claude",
            "kind": "continuation_anchor",
            "summary": "Communication route proof",
            "body": "Claude should reply with task_progress.",
            "status": "pending",
            "target_kind": "plan",
            "target_ref": "plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
            "target_role": "implementer",
            "target_session_id": "claude-session",
            "expires_at_utc": "2999-01-01T00:00:00Z",
        },
        existing_events=[],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        actor="claude",
        actor_role="implementer",
        session_id="claude-session",
        from_agent="claude",
        to_agent="codex",
        kind="task_progress",
        summary="Communication route proof received",
        body="Claude received rev_pkt_4829 and is replying from the implementer session.",
        target_kind="plan",
        target_ref="plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        target_role="reviewer",
        target_session_id="codex-session",
        evidence_ref=["packet:rev_pkt_4829"],
        parent_packet_id="rev_pkt_4829",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0, (
        report.get("errors"),
        report.get("control_decision_obedience"),
    )
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["kind"] == "task_progress"
    assert report["packet"]["from_agent"] == "claude"
    assert report["packet"]["to_agent"] == "codex"
    assert report["control_decision_obedience"]["ok"] is True
    assert report["control_decision_obedience"]["cascade_lifecycle_post_authority"] is True
    assert _event_count(artifact_paths) == before + 2


def test_claude_task_progress_can_reply_to_action_request_without_post_decision(
    monkeypatch,
    tmp_path,
) -> None:
    _isolate_runtime_session_roots(monkeypatch, tmp_path)
    review_channel_path = tmp_path / "review_channel.md"
    review_channel_path.write_text("", encoding="utf-8")
    artifact_root = tmp_path / "dev/reports/review_channel"
    event_log_path = artifact_root / "events" / "trace.ndjson"
    artifact_paths = ReviewChannelArtifactPaths(
        artifact_root=str(artifact_root),
        event_log_path=str(event_log_path),
        state_path=str(artifact_root / "state/latest.json"),
        projections_root=str(artifact_root / "projections/latest"),
    )
    _write_agent_mind(tmp_path, agent="codex", session_id="codex-session")
    _write_agent_mind(tmp_path, agent="claude", session_id="claude-session")
    append_event(
        event_log_path,
        {
            "event_type": "packet_posted",
            "timestamp_utc": "2026-05-22T19:06:23Z",
            "project_id": "test-project",
            "session_id": "codex-session",
            "trace_id": "trace-test",
            "plan_id": "MP-355",
            "packet_id": "rev_pkt_4841",
            "from_agent": "codex",
            "to_agent": "claude",
            "kind": "action_request",
            "requested_action": "implementer_handoff",
            "summary": "G23 action request",
            "body": "Claude should reply with task_progress.",
            "status": "pending",
            "target_kind": "plan",
            "target_ref": "plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
            "target_role": "implementer",
            "target_session_id": "claude-session",
            "expires_at_utc": "2999-01-01T00:00:00Z",
        },
        existing_events=[],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        actor="claude",
        actor_role="implementer",
        session_id="claude-session",
        from_agent="claude",
        to_agent="codex",
        kind="task_progress",
        summary="G23 action request received",
        body="Claude received rev_pkt_4841 and is replying from the implementer session.",
        target_kind="plan",
        target_ref="plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        target_role="reviewer",
        target_session_id="codex-session",
        evidence_ref=["packet:rev_pkt_4841"],
        parent_packet_id="rev_pkt_4841",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0, (
        report.get("errors"),
        report.get("control_decision_obedience"),
    )
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["kind"] == "task_progress"
    assert report["packet"]["from_agent"] == "claude"
    assert report["packet"]["to_agent"] == "codex"
    assert report["control_decision_obedience"]["ok"] is True
    assert report["control_decision_obedience"]["cascade_lifecycle_post_authority"] is True
    assert _event_count(artifact_paths) == before + 2


def test_scoped_body_open_can_observe_newer_packet_during_prior_ingestion_gate(
    monkeypatch,
    tmp_path,
) -> None:
    _isolate_runtime_session_roots(monkeypatch, tmp_path)
    review_channel_path, artifact_paths = _seed_packet_event_state(
        tmp_path,
        target_role="implementer",
        target_session_id="claude-session",
        target_ref="plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
    )
    event_log_path = Path(artifact_paths.event_log_path)
    append_event(
        event_log_path,
        {
            "event_type": "packet_posted",
            "timestamp_utc": "2026-05-22T19:19:56Z",
            "project_id": "test-project",
            "session_id": "codex-session",
            "trace_id": "trace-test-newer",
            "plan_id": "MP-355",
            "packet_id": "rev_pkt_4844",
            "from_agent": "codex",
            "to_agent": "claude",
            "kind": "action_request",
            "requested_action": "implementer_handoff",
            "summary": "G23 correction",
            "body": "Claude must be able to open this newer scoped packet.",
            "status": "pending",
            "target_kind": "plan",
            "target_ref": "plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
            "target_role": "implementer",
            "target_session_id": "claude-session",
            "expires_at_utc": "2999-01-01T00:00:00Z",
        },
        existing_events=[],
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
        actor_id="claude",
        actor_role="implementer",
        session_id="claude-session",
        allowed_actions=["review-channel.ingest"],
    )
    before = _event_count(artifact_paths)
    args = _show_args(
        packet_id="rev_pkt_4844",
        actor="claude",
        actor_role="implementer",
        session_id="claude-session",
        target_role="implementer",
        target_session_id="claude-session",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0, (
        report.get("errors"),
        report.get("control_decision_obedience"),
    )
    assert report["event"]["event_type"] == PACKET_BODY_OBSERVATION_EVENT_TYPE
    assert report["event"]["packet_id"] == "rev_pkt_4844"
    assert report["event"]["body_observed_by"] == "claude"
    assert report["control_decision_obedience"]["ok"] is True
    assert (
        report["control_decision_obedience"]["scoped_packet_body_open_authority"]
        is True
    )
    assert _event_count(artifact_paths) == before + 1


def test_live_agent_post_stamps_agent_mind_session_before_control_gate(tmp_path) -> None:
    """Current-row communication proof: fallback post sessions must resolve to
    the live AgentMind session before ControlDecisionObeyedGuard runs.
    """
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    live_session_id = "codex-live-session"
    agent_mind_path = tmp_path / "dev/reports/agent_minds/codex_latest.json"
    agent_mind_path.parent.mkdir(parents=True, exist_ok=True)
    agent_mind_path.write_text(
        json.dumps(
            {
                "contract_id": "AgentMindSlice",
                "agent_provider": "codex",
                "session_id": live_session_id,
                "last_cursor": "2026-05-22T15:58:00Z",
            }
        ),
        encoding="utf-8",
    )
    _write_latest_control_decision(
        tmp_path,
        actor_id="codex",
        actor_role="reviewer",
        session_id=live_session_id,
        allowed_actions=["review-channel.post_continuation_anchor"],
        packet_id="rev_pkt_100",
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="continuation_anchor",
        summary="Keep current-row communication alive",
        body="Continue until Codex and Claude can exchange typed packets.",
        actor="codex",
        actor_role="reviewer",
        session_id="local-review",
        from_agent="codex",
        to_agent="claude",
        target_kind="plan",
        target_ref="plan:MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        target_role="implementer",
        anchor_scope="plan",
        expires_in_minutes=480,
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["packet"]["kind"] == "continuation_anchor"
    assert report["packet"]["from_agent"] == "codex"
    assert report["packet"]["to_agent"] == "claude"
    assert report["event"]["session_id"] == live_session_id
    gate = report["control_decision_obedience"]
    assert gate["ok"] is True
    attempted = gate["attempted_action_receipt"]
    assert attempted["session_id"] == live_session_id
    assert attempted["argv"][attempted["argv"].index("--session-id") + 1] == (
        live_session_id
    )
    assert _event_count(artifact_paths) == before + 2


def test_review_channel_parser_accepts_control_decision_input_for_remote_lane() -> None:
    args = cli.build_parser().parse_args(
        [
            "review-channel",
            "--action",
            "post",
            "--from-agent",
            "codex",
            "--to-agent",
            "claude",
            "--kind",
            "task_progress",
            "--summary",
            "Remote lane progress",
            "--body",
            "body",
            "--actor",
            "codex",
            "--actor-role",
            "reviewer",
            "--session-id",
            "codex-review-session",
            "--target-role",
            "implementer",
            "--control-decision-input",
            "decision.json",
        ]
    )

    assert args.control_decision_input == "decision.json"
    assert args.actor == "codex"
    assert args.actor_role == "reviewer"
    assert args.target_role == "implementer"


def test_allowed_task_produced_post_appends_attempted_action_receipt(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_task_produced"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="task_produced",
        summary="Phase 0.6.A task output",
        body="Reviewable implementation evidence is available.",
        commit_sha="abc1234",
        evidence_ref=["command_output:test-python:task-produced"],
        target_kind="code",
        target_ref="dev/scripts/devctl/runtime/control_decision_obedience.py",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["kind"] == "task_produced"
    assert report["control_decision_obedience"]["ok"] is True
    attempted = report["control_decision_obedience"]["attempted_action_receipt"]
    assert attempted["argv"][attempted["argv"].index("--kind") + 1] == "task_produced"
    assert _event_count(artifact_paths) == before + 2


def test_artifact_task_produced_requires_post_evidence_allowed_action(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_evidence"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="task_produced",
        summary="Phase 0.6.A evidence",
        body="Focused command-output receipt is available.",
        commit_sha="abc1234",
        evidence_ref=["command_output:test-python:post-evidence"],
        target_kind="artifact",
        target_ref="command_output:test-python:post-evidence",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == "packet_posted"
    assert report["packet"]["kind"] == "task_produced"
    assert report["packet"]["target_kind"] == "artifact"
    assert report["control_decision_obedience"]["ok"] is True
    attempted = report["control_decision_obedience"]["attempted_action_receipt"]
    assert attempted["argv"][attempted["argv"].index("--target-kind") + 1] == "artifact"
    assert _event_count(artifact_paths) == before + 2


def test_post_action_request_without_allowed_action_blocks_before_event_append(
    tmp_path,
) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_finding"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="action_request",
        summary="Checkpoint action request",
        body="Request governed checkpoint staging for the current local patch.",
        requested_action="stage_commit_pipeline",
        target_kind="runtime",
        target_ref="devctl_commit:lifecycle_proxy_absorb_checkpoint",
        target_revision="HEAD",
        full_guard_bundle_evidence="bundle.tooling",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert report["control_decision_obedience"]["ok"] is False
    assert _event_count(artifact_paths) == before


def test_allowed_stop_anchor_post_appends_attempted_action_receipt(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_stop_anchor"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="stop_anchor",
        summary="Stop at typed closure",
        body="Stop only through typed controller closure.",
        anchor_scope="session",
        target_session_id="session-a",
        expires_in_minutes=360,
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["packet"]["kind"] == "stop_anchor"
    assert report["packet"]["anchor_scope"] == "session"
    assert report["control_decision_obedience"]["ok"] is True
    attempted = report["control_decision_obedience"]["attempted_action_receipt"]
    assert attempted["argv"][attempted["argv"].index("--kind") + 1] == "stop_anchor"
    assert _event_count(artifact_paths) == before + 2


def test_stop_anchor_post_without_allowed_action_blocks_before_event_append(
    tmp_path,
) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        allowed_actions=["review-channel.post_finding"],
    )
    before = _event_count(artifact_paths)
    args = _post_args(
        kind="stop_anchor",
        summary="Stop at typed closure",
        body="Stop only through typed controller closure.",
        anchor_scope="session",
        target_session_id="session-a",
        expires_in_minutes=360,
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert report["control_decision_obedience"]["ok"] is False
    assert _event_count(artifact_paths) == before


def test_absorb_requires_matching_semantic_ingestion_before_event_append(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        absorption_required=True,
    )
    before = _event_count(artifact_paths)
    args = _show_args(
        action="absorb",
        actor="codex",
        target_role="reviewer",
        target_session_id="session-a",
    )

    report, exit_code = _run_event_action(
        args=args,
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "matching_packet_semantic_ingestion_required" in report["errors"]
    assert _event_count(artifact_paths) == before


def test_absorb_wrong_actor_scope_blocks_before_event_append(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
    )
    _run_event_action(
        args=_show_args(
            action="show",
            actor="codex",
            target_role="reviewer",
            target_session_id="session-a",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    _run_event_action(
        args=_show_args(
            action="ingest",
            actor="codex",
            semantic_action_item=[_semantic_action_item_json("rev_pkt_100")],
            target_role="reviewer",
            target_session_id="session-a",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        absorption_required=True,
    )
    before = _event_count(artifact_paths)

    report, exit_code = _run_event_action(
        args=_show_args(
            action="absorb",
            actor="codex",
            target_role="reviewer",
            target_session_id="session-b",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "control_decision_obedience_failed" in report["errors"]
    assert _event_count(artifact_paths) == before


def test_absorb_records_receipt_after_valid_semantic_ingestion(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
    )
    _run_event_action(
        args=_show_args(
            action="show",
            actor="codex",
            target_role="reviewer",
            target_session_id="session-a",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    ingest_report, ingest_exit = _run_event_action(
        args=_show_args(
            action="ingest",
            actor="codex",
            semantic_action_item=[_semantic_action_item_json("rev_pkt_100")],
            target_role="reviewer",
            target_session_id="session-a",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    assert ingest_exit == 0
    semantic_receipt_id = ingest_report["event"]["packet_semantic_ingestion_receipt"][
        "receipt_id"
    ]
    semantic_event_id = ingest_report["event"]["event_id"]
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        absorption_required=True,
    )

    report, exit_code = _run_event_action(
        args=_show_args(
            action="absorb",
            actor="codex",
            target_role="reviewer",
            target_session_id="session-a",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == PACKET_ABSORPTION_EVENT_TYPE
    receipt = report["event"]["packet_absorption_receipt"]
    assert receipt["contract_id"] == "PacketAbsorptionReceipt"
    assert receipt["source_semantic_ingestion_receipt_id"] == semantic_receipt_id
    assert receipt["source_semantic_ingestion_event_id"] == semantic_event_id
    assert report["packet"]["lifecycle_current_state"] == "absorbed"
    refreshed = refresh_event_bundle(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    assert live_pending_packets(refreshed.review_state["packets"]) == ()


def test_absorb_blocks_plan_affecting_rows_without_plan_evidence(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(tmp_path)
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
    )
    _run_event_action(
        args=_show_args(
            action="show",
            actor="codex",
            target_role="reviewer",
            target_session_id="session-a",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    _run_event_action(
        args=_show_args(
            action="ingest",
            actor="codex",
            semantic_action_item=[
                json.dumps(
                    {
                        "action_item_id": "rev_pkt_100:plan",
                        "kind": "plan_update",
                        "disposition": "accepted",
                        "target_ref": "plan:MP-TEST",
                        "packet_ref": "packet:rev_pkt_100",
                        "reason": "would change typed plan state",
                        "evidence_refs": ["packet:rev_pkt_100#body_observed"],
                    },
                    sort_keys=True,
                )
            ],
            target_role="reviewer",
            target_session_id="session-a",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        absorption_required=True,
    )
    before = _event_count(artifact_paths)

    report, exit_code = _run_event_action(
        args=_show_args(
            action="absorb",
            actor="codex",
            target_role="reviewer",
            target_session_id="session-a",
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 1
    assert "matching_packet_semantic_ingestion_required" in report["errors"]
    assert _event_count(artifact_paths) == before


def test_absorb_accepts_inserted_packet_plan_binding_as_plan_evidence(tmp_path) -> None:
    review_channel_path, artifact_paths = _seed_packet_event_state(
        tmp_path,
        target_ref="plan:MP-TEST",
    )
    append_event(
        Path(artifact_paths.event_log_path),
        {
            "event_type": "packet_creation_binding_recorded",
            "timestamp_utc": "2026-05-11T01:00:01Z",
            "packet_id": "rev_pkt_100",
            "packet_creation_binding": {
                "status": "inserted",
                "binding_target_kind": "plan_row_evidence",
            },
        },
        existing_events=[],
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        body_open_required=True,
    )
    _run_event_action(
        args=_show_args(action="show", actor="codex"),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        semantic_ingestion_required=True,
    )
    _run_event_action(
        args=_show_args(
            action="ingest",
            actor="codex",
            semantic_action_item=[
                json.dumps(
                    {
                        "action_item_id": "rev_pkt_100:plan",
                        "kind": "task_progress",
                        "disposition": "accepted",
                        "target_ref": "plan://MP-TEST",
                        "slice_ref": "plan://MP-TEST",
                        "packet_ref": "packet:rev_pkt_100",
                        "reason": "plan-bound collaboration progress",
                        "evidence_refs": ["packet:rev_pkt_100#body_observed"],
                    },
                    sort_keys=True,
                )
            ],
        ),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )
    _write_latest_control_decision(
        tmp_path,
        packet_id="rev_pkt_100",
        absorption_required=True,
    )

    report, exit_code = _run_event_action(
        args=_show_args(action="absorb", actor="codex"),
        repo_root=tmp_path,
        paths={
            "review_channel_path": review_channel_path,
            "artifact_paths": artifact_paths,
        },
    )

    assert exit_code == 0
    assert report["event"]["event_type"] == PACKET_ABSORPTION_EVENT_TYPE


def _show_args(**overrides: object) -> SimpleNamespace:
    args = {
        "action": "show",
        "actor_role": "",
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
        "semantic_action_item": [],
        "session_id": "session-a",
        "plan_id": "MP-TEST",
        "target_role": "reviewer",
        "target_session_id": "session-a",
        "to_agent": None,
    }
    args.update(overrides)
    return SimpleNamespace(**args)


def _post_args(**overrides: object) -> SimpleNamespace:
    args = {
        "action": "post",
        "actor": "codex",
        "actor_role": "reviewer",
        "anchor_ref": [],
        "anchor_scope": None,
        "approval_required": False,
        "attention_class": "auto",
        "attention_urgency": "auto",
        "body": "body",
        "body_file": None,
        "confidence": 1.0,
        "context_pack_adapter_profile": "canonical",
        "context_pack_ref": [],
        "controller_run_id": None,
        "commit_sha": None,
        "correlation_id": "",
        "causation_id": "",
        "evidence_artifact_path": [],
        "evidence_ref": [],
        "expires_in_minutes": None,
        "follow": False,
        "format": "md",
        "from_agent": "codex",
        "full_guard_bundle_evidence": None,
        "guard_results_summary": None,
        "kind": "finding",
        "limit": 20,
        "mutation_op": None,
        "packet_id": None,
        "pipeline_generation": None,
        "plan_id": "MP-TEST",
        "plan_revision_after": None,
        "plan_revision_before": None,
        "policy_hint": "review_only",
        "requested_action": "review_only",
        "requested_session_visibility": None,
        "run_record_id": [],
        "run_id": "",
        "session_id": "session-a",
        "staged_snapshot_hash": None,
        "summary": "summary",
        "target_kind": None,
        "target_ref": None,
        "target_revision": None,
        "target_role": "",
        "target_session_id": "",
        "to_agent": "operator",
        "trace_id": None,
    }
    args.update(overrides)
    return SimpleNamespace(**args)


def _seed_packet_event_state(
    tmp_path,
    *,
    target_ref: str = "",
    target_role: str = "",
    target_session_id: str = "",
    anchor_scope: str = "",
) -> tuple[object, ReviewChannelArtifactPaths]:
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
    packet_event = {
            "event_type": "packet_posted",
            "timestamp_utc": "2026-05-11T01:00:00Z",
            "project_id": "test-project",
            "session_id": "test-session",
            "trace_id": "trace-test",
            "plan_id": "MP-377",
            "packet_id": "rev_pkt_100",
            "from_agent": "claude",
            "to_agent": "codex",
            "kind": "finding",
            "summary": "Unread body",
            "body": "Codex must open this body before continuing.",
            "status": "pending",
            "expires_at_utc": "2999-01-01T00:00:00Z",
        }
    if target_role:
        packet_event["target_role"] = target_role
    if target_session_id:
        packet_event["target_session_id"] = target_session_id
    if target_ref:
        packet_event["target_kind"] = "plan"
        packet_event["target_ref"] = target_ref
    if anchor_scope:
        packet_event["anchor_scope"] = anchor_scope
    append_event(
        event_log_path,
        packet_event,
        existing_events=[],
    )
    return review_channel_path, artifact_paths


def _semantic_action_item_json(packet_id: str) -> str:
    return json.dumps(
        {
            "action_item_id": f"{packet_id}:finding",
            "kind": "finding",
            "disposition": "deferred",
            "target_ref": f"packet:{packet_id}",
            "packet_ref": f"packet:{packet_id}",
            "reason": "packet finding requires follow-up after semantic ingestion",
            "evidence_refs": [f"packet:{packet_id}#body_observed"],
            "next_slice_refs": [f"packet:{packet_id}#absorption"],
        },
        sort_keys=True,
    )


def _write_latest_control_decision(
    tmp_path,
    *,
    packet_id: str,
    body_open_required: bool = False,
    semantic_ingestion_required: bool = False,
    absorption_required: bool = False,
    actor_id: str = "codex",
    actor_role: str = "reviewer",
    session_id: str = "session-a",
    source_snapshot_id: str = "",
    allowed_actions: list[str] | None = None,
) -> None:
    (tmp_path / "dev/scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "dev/scripts/devctl.py").write_text("# test marker\n", encoding="utf-8")
    latest = tmp_path / "dev/reports/review_channel/state/latest.json"
    latest.parent.mkdir(parents=True, exist_ok=True)
    packet_attention = {
        "latest_attention_packet_id": packet_id,
        "active_packet_id": packet_id,
        "pending_packet_count": 1,
    }
    if body_open_required:
        packet_attention.update(
            {
                "body_open_required": True,
                "body_open_packet_id": packet_id,
            }
        )
    if semantic_ingestion_required:
        packet_attention.update(
            {
                "semantic_ingestion_required": True,
                "semantic_ingestion_packet_id": packet_id,
                "semantic_ingestion_command": (
                    "python3 dev/scripts/devctl.py review-channel --action ingest "
                    f"--packet-id {packet_id}"
                ),
                "semantic_ingestion_reason": (
                    "packet_body_observed_without_semantic_ingestion"
                ),
            }
        )
    if absorption_required:
        packet_attention.update(
            {
                "absorption_required": True,
                "absorption_packet_id": packet_id,
                "absorption_command": (
                    "python3 dev/scripts/devctl.py review-channel --action absorb "
                    f"--packet-id {packet_id}"
                ),
                "absorption_reason": (
                    "packet_semantically_ingested_without_absorption"
                ),
            }
        )
    latest.write_text(
        json.dumps(
            {
                "contract_id": "ReviewState",
                "agent_runtime_clock": {"source_latest_event_id": "rev_evt_1"},
                "packet_attention": packet_attention,
                "agent_loop_decisions": [
                    {
                        "contract_id": "AgentLoopDecision",
                        "actor_id": actor_id,
                        "actor_role": actor_role,
                        "session_id": session_id,
                        "decision": "wait",
                        "required_action": "wait_for_scoped_packet",
                        "may_mutate": False,
                        "can_run_next_command": False,
                        "allowed_actions": allowed_actions or [],
                        "operator_override": {
                            "requested": True,
                            "active": False,
                            "state": "target_required",
                        },
                        "source_latest_event_id": "rev_evt_1",
                        "source_snapshot_id": source_snapshot_id,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _event_count(artifact_paths: ReviewChannelArtifactPaths) -> int:
    path = artifact_paths.event_log_path
    return len(
        [
            line
            for line in open(path, encoding="utf-8").read().splitlines()
            if line.strip()
        ]
    )


def _isolate_runtime_session_roots(monkeypatch, tmp_path) -> None:
    """Keep route-resolution tests independent from the operator's live sessions."""

    from dev.scripts.devctl.review_channel import agent_work_board_projection

    codex_root = tmp_path / "runtime_sessions/codex"
    claude_root = tmp_path / "runtime_sessions/claude"
    codex_root.mkdir(parents=True, exist_ok=True)
    claude_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(agent_work_board_projection, "CODEX_SESSIONS_ROOT", codex_root)
    monkeypatch.setattr(
        agent_work_board_projection,
        "CLAUDE_PROJECTS_ROOT",
        claude_root,
    )


def _write_agent_mind(tmp_path, *, agent: str, session_id: str) -> None:
    projection_dir = tmp_path / "dev/reports/agent_minds"
    projection_dir.mkdir(parents=True, exist_ok=True)
    (projection_dir / f"{agent}_latest.json").write_text(
        json.dumps(
            {
                "contract_id": "AgentMindSlice",
                "schema_version": 1,
                "agent_provider": agent,
                "session_id": session_id,
                "last_cursor": "2026-05-21T00:00:00Z",
                "session_path": f"/fake/sessions/{agent}-{session_id}.jsonl",
            }
        ),
        encoding="utf-8",
    )


def test_show_validation_requires_packet_id() -> None:
    with pytest.raises(ValueError, match="--packet-id is required"):
        _validate_args(_show_args(packet_id=None), ReviewChannelAction.SHOW)


def test_show_validation_still_rejects_post_only_to_agent() -> None:
    with pytest.raises(ValueError, match="--to-agent is only valid"):
        _validate_args(_show_args(to_agent="codex"), ReviewChannelAction.SHOW)
