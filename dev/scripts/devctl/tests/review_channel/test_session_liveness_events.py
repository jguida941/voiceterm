"""Coverage for Q94 participant_liveness_expired event emission.

Asserts that dead sessions only emit typed `participant_liveness_expired`
rows from the explicit refresh-time producer, not from projection helpers.
Repeated producer calls must still deduplicate by idempotency key. The
reducer must recognize the event type without raising
`Encountered review event without packet_id`.
"""

from __future__ import annotations

import json
from pathlib import Path

from dev.scripts.devctl.review_channel import event_reducer
from dev.scripts.devctl.review_channel import session_liveness_events
from dev.scripts.devctl.review_channel import status_projection_helpers
from dev.scripts.devctl.review_channel.event_store import (
    load_events,
    resolve_artifact_paths,
)
from dev.scripts.devctl.review_channel.session_probe import (
    ConductorSessionRecord,
)


def _dead_record(provider: str, role: str) -> ConductorSessionRecord:
    return ConductorSessionRecord(
        provider=provider,
        role=role,
        provider_name=provider.title(),
        session_name=f"{provider}-conductor",
        capture_mode="visible",
        prepared_at="2026-04-08T00:00:00Z",
        repo_root="",
        script_path="",
        log_path="",
        launch_command="",
        supervision_mode="",
        approval_mode="balanced",
        planned_lane_count=0,
        requested_worker_budget=None,
        terminal_window_id=None,
        session_pid=None,
        planned_lanes=(),
        metadata_path="/tmp/fake-conductor.json",
        live=False,
        age_seconds=600,
        live_reason="detached_exit",
        script_probe_state="not_running",
        terminal_window_state="",
        launch_authority_state="",
    )


def test_status_tick_liveness_producer_emits_liveness_expired(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """A dead session should write one participant_liveness_expired event."""
    records = (_dead_record("claude", "implementer"),)
    monkeypatch.setattr(
        session_liveness_events,
        "load_conductor_sessions",
        lambda *, session_output_root: records,
    )
    monkeypatch.setattr(
        status_projection_helpers,
        "active_conductor_providers",
        lambda *, session_output_root: (),
    )
    monkeypatch.setattr(
        status_projection_helpers,
        "conductor_visibility",
        lambda *, session_output_root: "none",
    )

    bridge_liveness: dict[str, object] = {
        "reviewer_mode": "active_dual_agent",
    }
    status_projection_helpers.attach_conductor_session_state(
        bridge_liveness=bridge_liveness,
        output_root=tmp_path,
    )
    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    assert not Path(artifact_paths.event_log_path).exists()

    emitted = session_liveness_events.emit_status_tick_participant_liveness_events(
        repo_root=tmp_path,
        session_output_root=tmp_path,
    )
    bridge_liveness["participant_liveness_expired_events"] = (
        session_liveness_events.summarize_participant_liveness_events(emitted)
    )

    events = load_events(Path(artifact_paths.event_log_path))
    expired = [
        event
        for event in events
        if event.get("event_type") == "participant_liveness_expired"
    ]
    assert len(expired) == 1
    assert expired[0]["provider"] == "claude"
    assert expired[0]["session_name"] == "claude-conductor"
    assert expired[0]["live_reason"] == "detached_exit"
    assert "idempotency_key" in expired[0]
    assert bridge_liveness.get("participant_liveness_expired_events")


def test_status_tick_liveness_producer_dedups_repeat_polls(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Repeat status ticks must not re-emit the same expiry event."""
    records = (_dead_record("claude", "implementer"),)
    monkeypatch.setattr(
        session_liveness_events,
        "load_conductor_sessions",
        lambda *, session_output_root: records,
    )
    monkeypatch.setattr(
        status_projection_helpers,
        "active_conductor_providers",
        lambda *, session_output_root: (),
    )
    monkeypatch.setattr(
        status_projection_helpers,
        "conductor_visibility",
        lambda *, session_output_root: "none",
    )

    for _ in range(3):
        status_projection_helpers.attach_conductor_session_state(
            bridge_liveness={"reviewer_mode": "active_dual_agent"},
            output_root=tmp_path,
        )
        session_liveness_events.emit_status_tick_participant_liveness_events(
            repo_root=tmp_path,
            session_output_root=tmp_path,
        )

    artifact_paths = resolve_artifact_paths(repo_root=tmp_path)
    events = load_events(Path(artifact_paths.event_log_path))
    expired = [
        event
        for event in events
        if event.get("event_type") == "participant_liveness_expired"
    ]
    assert len(expired) == 1


def test_reduce_events_tracks_liveness_expired(tmp_path: Path) -> None:
    """The reducer must accept the new event type without packet_id errors."""
    events_path = tmp_path / "trace.ndjson"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": 1,
        "event_id": "rev_evt_0001",
        "event_type": "participant_liveness_expired",
        "timestamp_utc": "2026-04-11T00:00:00Z",
        "provider": "claude",
        "session_name": "claude-conductor",
        "live_reason": "detached_exit",
        "age_seconds": 900,
        "idempotency_key": "dedup_001",
        "source": "review_channel",
        "metadata": {},
    }
    events_path.write_text(json.dumps(event) + "\n", encoding="utf-8")

    review_state, _registry = event_reducer.reduce_events(
        events=[event],
        repo_root=tmp_path,
        review_channel_path=tmp_path / "review_channel.md",
    )
    compat = review_state.get("_compat") or {}
    assert "claude:claude-conductor" in compat.get("expired_liveness_sessions", [])
    assert not review_state.get("errors"), (
        "reducer should not emit missing-packet_id errors for liveness events"
    )
