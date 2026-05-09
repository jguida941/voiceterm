"""Focused tests for review-channel projection bundle writes."""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.review_channel.event_reducer import (
    load_or_refresh_event_bundle,
    load_projected_event_bundle,
)
from dev.scripts.devctl.review_channel.event_store import resolve_artifact_paths
from dev.scripts.devctl.review_channel.projection_bundle import write_projection_bundle


def test_projection_bundle_writes_machine_json_compactly(tmp_path: Path) -> None:
    review_state = {
        "schema_version": 1,
        "contract_id": "ReviewState",
        "command": "review-channel",
        "action": "status",
        "timestamp": "2026-05-07T00:00:00Z",
        "ok": True,
        "review": {"session_id": "session-1"},
        "queue": {"pending_total": 0},
        "current_session": {},
        "bridge": {"reviewer_mode": "tools_only"},
        "packets": [
            {
                "packet_id": "rev_pkt_1",
                "requested_action": "review_only",
                "status": "pending",
            }
        ],
    }

    paths = write_projection_bundle(
        output_root=tmp_path / "latest",
        review_state=review_state,
        agent_registry={"schema_version": 1, "agents": []},
        action="status",
    )

    for path_text in (
        paths.review_state_path,
        paths.compact_path,
        paths.full_path,
        paths.actions_path,
        paths.agent_registry_path,
        paths.commit_pipeline_path,
    ):
        text = Path(path_text).read_text(encoding="utf-8")
        assert "\n" not in text
        assert isinstance(json.loads(text), dict)


def test_read_only_event_bundle_reduces_event_log_without_artifact_writes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    projections_root = Path(artifact_paths.projections_root)
    projections_root.mkdir(parents=True, exist_ok=True)
    projected_state = {
        "schema_version": 1,
        "contract_id": "ReviewState",
        "command": "review-channel",
        "queue": {"pending_total": 99},
        "packets": [],
    }
    (projections_root / "review_state.json").write_text(
        json.dumps(projected_state),
        encoding="utf-8",
    )
    event_log_path = Path(artifact_paths.event_log_path)
    event_log_path.parent.mkdir(parents=True, exist_ok=True)
    event_log_path.write_text(
        json.dumps(
            {
                "event_id": "rev_evt_0001",
                "packet_id": "rev_pkt_event_only",
                "event_type": "packet_posted",
                "from_agent": "claude",
                "to_agent": "codex",
                "kind": "finding",
                "summary": "event log row",
                "body": "event body",
                "status": "pending",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    review_channel_path = tmp_path / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
    monkeypatch.setenv("DEVCTL_NO_ARTIFACT_WRITES", "1")

    bundle = load_or_refresh_event_bundle(
        repo_root=tmp_path,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )

    assert bundle.review_state["queue"]["pending_total"] == 1
    assert bundle.events[0]["packet_id"] == "rev_pkt_event_only"


def test_projected_event_bundle_can_load_raw_events_for_post_ids(
    tmp_path: Path,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    projections_root = Path(artifact_paths.projections_root)
    projections_root.mkdir(parents=True, exist_ok=True)
    (projections_root / "review_state.json").write_text(
        json.dumps({"schema_version": 1, "packets": []}),
        encoding="utf-8",
    )
    event_log_path = Path(artifact_paths.event_log_path)
    event_log_path.parent.mkdir(parents=True, exist_ok=True)
    event_log_path.write_text(
        json.dumps({"event_id": "rev_evt_0001", "event_type": "packet_posted"})
        + "\n",
        encoding="utf-8",
    )

    bundle = load_projected_event_bundle(
        artifact_paths=artifact_paths,
        include_events=True,
    )

    assert bundle is not None
    assert [event["event_id"] for event in bundle.events] == ["rev_evt_0001"]
