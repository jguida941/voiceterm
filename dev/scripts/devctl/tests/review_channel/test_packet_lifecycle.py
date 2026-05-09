"""Coverage for event-backed packet lifecycle/disposition projection."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.review_channel.event_reducer import reduce_events
from dev.scripts.devctl.review_channel.packet_plan_integration import (
    maybe_append_packet_plan_row,
)
from dev.scripts.devctl.review_channel.packet_lifecycle import project_packet_lifecycle
from dev.scripts.devctl.runtime.packet_continuity import (
    build_packet_continuity_index,
    compact_packet_continuity_index,
)
from dev.scripts.devctl.runtime.review_state_parser_rows import packet_states_from_value


def _review_channel_path(root: Path) -> Path:
    path = root / "dev/active/review_channel.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Review Channel",
                "",
                "| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |",
                "|---|---|---|---|---|---|",
                "| `codex` | reviewer | `dev/active/ai_governance_platform.md` | MP-377 | . | feature/governance-quality-sweep |",
                "| `claude` | implementer | `dev/active/ai_governance_platform.md` | MP-377 | . | feature/governance-quality-sweep |",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _posted_packet(**updates: object) -> dict[str, object]:
    packet = {
        "packet_id": "rev_pkt_lifecycle",
        "trace_id": "trace_lifecycle",
        "event_id": "rev_evt_001",
        "event_type": "packet_posted",
        "timestamp_utc": "2026-04-29T01:00:00Z",
        "session_id": "session-1",
        "plan_id": "MP-377",
        "from_agent": "codex",
        "to_agent": "claude",
        "kind": "finding",
        "summary": "Lifecycle packet",
        "body": "Route this packet without clock-loss semantics.",
        "status": "pending",
        "expires_at_utc": "2099-04-29T01:30:00Z",
    }
    packet.update(updates)
    return packet


def test_packet_lifecycle_tracks_ack_and_apply_events(tmp_path: Path) -> None:
    posted = _posted_packet(
        target_kind="plan",
        target_ref="dev/active/ai_governance_platform.md#MP377-P0-T08A",
        target_revision="0233390",
    )
    acked = {
        **posted,
        "event_id": "rev_evt_002",
        "event_type": "packet_acked",
        "timestamp_utc": "2026-04-29T01:05:00Z",
        "status": "acked",
        "metadata": {"actor": "claude"},
    }
    applied = {
        **posted,
        "event_id": "rev_evt_003",
        "event_type": "packet_applied",
        "timestamp_utc": "2026-04-29T01:10:00Z",
        "status": "applied",
        "metadata": {"actor": "claude"},
    }
    integration = {
        **posted,
        "event_id": "rev_evt_004",
        "event_type": "packet_plan_ingestion_recorded",
        "timestamp_utc": "2026-04-29T01:10:01Z",
        "status": "applied",
        "plan_ingestion": {
            "contract_id": "PacketPlanIntegration",
            "status": "inserted",
            "reason": "plan_target_packet_applied",
            "packet_id": "rev_pkt_lifecycle",
            "target_ref": "dev/active/ai_governance_platform.md#MP377-P0-T08A",
        },
        "metadata": {"actor": "claude"},
    }

    review_state, _ = reduce_events(
        events=[posted, acked, applied, integration],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]

    assert packet["lifecycle_current_state"] == "applied"
    assert packet["acknowledged_events"][0]["event_id"] == "rev_evt_002"
    assert packet["acknowledged_events"][0]["by_agent"] == "claude"
    assert packet["acted_on_events"][0]["event_id"] == "rev_evt_003"
    assert packet["disposition"]["sink"] == "plan_integrated"
    assert (
        packet["disposition"]["plan_target"]
        == "plan_target:dev/active/ai_governance_platform.md#MP377-P0-T08A@0233390"
    )
    assert (
        packet["lifecycle_history"]["contract_id"]
        == "PacketLifecycleHistory"
    )
    assert review_state["packet_continuity"]["packet_count"] == 1
    assert review_state["packet_continuity"]["sink_counts"]["applied_to_plan"] == 1


def test_plan_target_apply_without_ingestion_record_requires_recovery(
    tmp_path: Path,
) -> None:
    posted = _posted_packet(
        packet_id="rev_pkt_plan_unrecorded",
        target_kind="plan",
        target_ref="dev/active/ai_governance_platform.md#MP377-P0-T08A",
    )
    applied = {
        **posted,
        "event_id": "rev_evt_009",
        "event_type": "packet_applied",
        "timestamp_utc": "2026-04-29T01:10:00Z",
        "status": "applied",
        "metadata": {"actor": "claude"},
    }

    review_state, _ = reduce_events(
        events=[posted, applied],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]

    assert packet["lifecycle_current_state"] == "plan_ingestion_failed"
    assert packet["disposition"]["sink"] == "recovery_required"
    assert (
        packet["disposition"]["next_slice_target"]
        == "packet_plan_ingestion_repair"
    )
    assert review_state["packet_continuity"]["sink_counts"]["failed_ingestion"] == 1


def test_legacy_plan_integration_event_replays_as_ingestion(
    tmp_path: Path,
) -> None:
    posted = _posted_packet(
        packet_id="rev_pkt_legacy_ingestion",
        target_kind="plan",
        target_ref="dev/active/ai_governance_platform.md#MP377-P0-T08A",
    )
    applied = {
        **posted,
        "event_id": "rev_evt_010",
        "event_type": "packet_applied",
        "timestamp_utc": "2026-04-29T01:10:00Z",
        "status": "applied",
        "metadata": {"actor": "claude"},
    }
    legacy_integration = {
        **posted,
        "event_id": "rev_evt_011",
        "event_type": "packet_plan_integration_recorded",
        "timestamp_utc": "2026-04-29T01:10:01Z",
        "status": "applied",
        "plan_integration": {
            "contract_id": "PacketPlanIntegration",
            "status": "inserted",
            "reason": "plan_target_packet_applied",
            "packet_id": "rev_pkt_legacy_ingestion",
        },
        "metadata": {"actor": "claude"},
    }

    review_state, _ = reduce_events(
        events=[posted, applied, legacy_integration],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]

    assert packet["lifecycle_current_state"] == "applied"
    assert packet["plan_ingestion"]["status"] == "inserted"
    assert review_state["packet_continuity"]["sink_counts"]["applied_to_plan"] == 1


def test_compact_packet_continuity_prioritizes_latest_live_packets() -> None:
    index = build_packet_continuity_index(
        [
            {
                "packet_id": "rev_pkt_0001",
                "status": "dismissed",
                "disposition": {"sink": "archived"},
            },
            {
                "packet_id": "rev_pkt_2670",
                "status": "pending",
                "disposition": {"sink": "queued"},
            },
            {
                "packet_id": "rev_pkt_2671",
                "status": "pending",
                "disposition": {"sink": "queued"},
            },
        ]
    ).to_dict()

    compact = compact_packet_continuity_index(index, limit=1)

    assert compact["sink_counts"]["live_queue"] == 2
    assert compact["rows"][0]["packet_id"] == "rev_pkt_2671"
    assert compact["rows"][0]["sink"] == "live_queue"


def test_stale_pending_packet_gets_archived_disposition(tmp_path: Path) -> None:
    posted = _posted_packet(
        packet_id="rev_pkt_stale",
        kind="action_request",
        expires_at_utc="2000-01-01T00:00:00Z",
    )

    review_state, _ = reduce_events(
        events=[posted],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]

    assert review_state["queue"]["stale_packet_count"] == 1
    assert packet["status"] == "pending"
    assert packet["lifecycle_current_state"] == "archived"
    assert packet["acted_on_events"][0]["action"] == "archived"
    assert packet["acted_on_events"][0]["by_agent"] == "system"
    assert packet["disposition"]["sink"] == "archived"
    assert (
        packet["disposition"]["archive_classification"]
        == "clock_expired_without_disposition"
    )


def test_explicit_packet_expired_event_records_acted_on_history(
    tmp_path: Path,
) -> None:
    posted = _posted_packet(packet_id="rev_pkt_explicit")
    expired = {
        **posted,
        "event_id": "rev_evt_004",
        "event_type": "packet_expired",
        "timestamp_utc": "2026-04-29T01:31:00Z",
        "status": "expired",
        "metadata": {"actor": "system"},
    }

    review_state, _ = reduce_events(
        events=[posted, expired],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]

    assert packet["status"] == "expired"
    assert packet["lifecycle_current_state"] == "archived"
    assert packet["acted_on_events"][0]["event_id"] == "rev_evt_004"
    assert packet["disposition"]["sink"] == "archived"


def test_review_packet_state_parser_preserves_lifecycle_fields(
    tmp_path: Path,
) -> None:
    posted = _posted_packet(packet_id="rev_pkt_parser")
    acked = {
        **posted,
        "event_id": "rev_evt_005",
        "event_type": "packet_acked",
        "timestamp_utc": "2026-04-29T01:05:00Z",
        "status": "acked",
        "metadata": {"actor": "claude"},
    }
    review_state, _ = reduce_events(
        events=[posted, acked],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    states = packet_states_from_value(review_state["packets"])

    assert states[0].lifecycle_current_state == "acknowledged"
    assert states[0].acknowledged_events[0]["by_agent"] == "claude"
    assert states[0].disposition["sink"] == "queued"


def test_action_request_execution_start_reduces_through_lifecycle_history(
    tmp_path: Path,
) -> None:
    posted = _posted_packet(
        packet_id="rev_pkt_action_start",
        kind="action_request",
        requested_action="stage_commit_pipeline",
    )
    acked = {
        **posted,
        "event_id": "rev_evt_006",
        "event_type": "packet_acked",
        "timestamp_utc": "2026-04-29T13:00:00Z",
        "status": "acked",
        "metadata": {"actor": "claude"},
    }

    review_state, _ = reduce_events(
        events=[posted, acked],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]

    assert packet["lifecycle_current_state"] == "in_progress"
    assert packet["execution_started_at_utc"] == "2026-04-29T13:00:00Z"
    assert packet["execution_started_by"] == "claude"
    assert packet["acknowledged_events"][0]["event_kind"] == "ack"
    assert packet["acknowledged_events"][1]["event_kind"] == "execution_started"
    assert (
        packet["lifecycle_history"]["acknowledged_events"][1]["action"]
        == "execution_started"
    )


def test_action_request_failure_event_reduces_through_lifecycle_history(
    tmp_path: Path,
) -> None:
    posted = _posted_packet(
        packet_id="rev_pkt_action_failed",
        kind="action_request",
        requested_action="stage_commit_pipeline",
    )
    failed = {
        **posted,
        "event_id": "rev_evt_007",
        "event_type": "action_request_execution_failed",
        "timestamp_utc": "2026-04-29T13:01:00Z",
        "status": "failed",
        "metadata": {
            "actor": "claude",
            "reason": "pending_reviewer_packets",
        },
    }

    review_state, _ = reduce_events(
        events=[posted, failed],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]

    assert packet["lifecycle_current_state"] == "failed"
    assert packet["execution_failed_at_utc"] == "2026-04-29T13:01:00Z"
    assert packet["execution_failed_by"] == "claude"
    assert packet["execution_failed_reason"] == "pending_reviewer_packets"
    assert packet["acted_on_events"][0]["event_kind"] == "failed"
    assert packet["disposition"]["sink"] == "recovery_required"
    assert packet["disposition"]["next_slice_target"] == "fresh_action_request"


def test_action_request_apply_pending_event_reduces_through_lifecycle_history(
    tmp_path: Path,
) -> None:
    posted = _posted_packet(
        packet_id="rev_pkt_action_apply_pending",
        kind="action_request",
        requested_action="stage_commit_pipeline",
    )
    apply_pending = {
        **posted,
        "event_id": "rev_evt_008",
        "event_type": "action_request_apply_pending_after_execution",
        "timestamp_utc": "2026-04-29T13:02:00Z",
        "status": "apply_pending_after_execution",
        "metadata": {
            "actor": "claude",
            "reason": "packet_apply_failed_after_commit",
        },
    }

    review_state, _ = reduce_events(
        events=[posted, apply_pending],
        repo_root=tmp_path,
        review_channel_path=_review_channel_path(tmp_path),
    )

    packet = review_state["packets"][0]

    assert packet["lifecycle_current_state"] == "apply_pending_after_execution"
    assert packet["apply_pending_after_execution_at_utc"] == "2026-04-29T13:02:00Z"
    assert packet["apply_pending_after_execution_by"] == "claude"
    assert (
        packet["apply_pending_after_execution_reason"]
        == "packet_apply_failed_after_commit"
    )
    assert packet["acted_on_events"][0]["event_kind"] == (
        "apply_pending_after_execution"
    )
    assert packet["disposition"]["sink"] == "recovery_required"
    assert (
        packet["disposition"]["next_slice_target"]
        == "fresh_action_request_or_explicit_recovery"
    )


def test_action_request_failure_receipt_is_terminal_lifecycle_state() -> None:
    packet = project_packet_lifecycle(
        _posted_packet(
            kind="action_request",
            requested_action="stage_commit_pipeline",
            execution_failed_at_utc="2026-04-29T13:00:00Z",
            execution_failed_by="claude",
            execution_failed_reason="pending_reviewer_packets",
        )
    )

    assert packet["lifecycle_current_state"] == "failed"
    assert packet["disposition"]["sink"] == "recovery_required"
    assert packet["disposition"]["next_slice_target"] == "fresh_action_request"


def test_action_request_apply_pending_receipt_is_terminal_lifecycle_state() -> None:
    packet = project_packet_lifecycle(
        _posted_packet(
            kind="action_request",
            requested_action="stage_commit_pipeline",
            apply_pending_after_execution_at_utc="2026-04-29T13:02:00Z",
            apply_pending_after_execution_by="claude",
            apply_pending_after_execution_reason="packet_apply_failed_after_commit",
        )
    )

    assert packet["lifecycle_current_state"] == "apply_pending_after_execution"
    assert packet["disposition"]["sink"] == "recovery_required"
    assert (
        packet["disposition"]["next_slice_target"]
        == "fresh_action_request_or_explicit_recovery"
    )


def test_plan_target_apply_appends_idempotent_master_plan_row(
    tmp_path: Path,
) -> None:
    master_plan = tmp_path / "dev/active/MASTER_PLAN.md"
    master_plan.parent.mkdir(parents=True, exist_ok=True)
    master_plan.write_text("# Master Plan\n", encoding="utf-8")
    packet = _posted_packet(
        packet_id="rev_pkt_plan",
        target_kind="plan",
        target_ref="dev/active/ai_governance_platform.md#MP377-P0-T08A",
        target_revision="0233390",
        summary="Integrate lifecycle packet into plan",
    )
    event = {
        "event_type": "packet_applied",
        "timestamp_utc": "2026-04-29T01:10:00Z",
        "metadata": {"actor": "claude"},
    }

    first = maybe_append_packet_plan_row(
        repo_root=tmp_path,
        packet=packet,
        event=event,
    )
    second = maybe_append_packet_plan_row(
        repo_root=tmp_path,
        packet=packet,
        event=event,
    )

    text = master_plan.read_text(encoding="utf-8")

    assert first["status"] == "inserted"
    assert second["status"] == "already_present"
    assert first["path"].endswith("dev/state/plan_index.jsonl")
    assert text.count("source `rev_pkt_plan`") == 1
    assert "Generated Review Packet Plan Integrations" in text
    assert "`PKT-REV-PKT-PLAN`" in text


def test_plan_target_apply_fails_without_master_plan_authority(
    tmp_path: Path,
) -> None:
    packet = _posted_packet(
        packet_id="rev_pkt_plan",
        target_kind="plan",
        target_ref="plan://MP-377",
        summary="Integrate lifecycle packet into plan",
    )
    event = {
        "event_type": "packet_applied",
        "timestamp_utc": "2026-04-29T01:10:00Z",
        "metadata": {"actor": "claude"},
    }

    result = maybe_append_packet_plan_row(
        repo_root=tmp_path,
        packet=packet,
        event=event,
    )

    assert result["status"] == "failed"
    assert result["reason"] == "master_plan_authority_unresolved"
    assert not (tmp_path / "dev/state/plan_index.jsonl").exists()
