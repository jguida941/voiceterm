"""Coverage for event-backed packet lifecycle/disposition projection."""

from __future__ import annotations

from pathlib import Path

from dev.scripts.devctl.review_channel.event_reducer import reduce_events
from dev.scripts.devctl.review_channel.packet_plan_integration import (
    maybe_append_packet_plan_row,
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

    review_state, _ = reduce_events(
        events=[posted, acked, applied],
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


def test_stale_pending_packet_gets_archived_disposition(tmp_path: Path) -> None:
    posted = _posted_packet(
        packet_id="rev_pkt_stale",
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
