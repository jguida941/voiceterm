"""Coverage for typed packet outcome ledgers."""

from __future__ import annotations

from dev.scripts.devctl.review_channel.packet_outcomes import (
    PacketOutcome,
    attach_packet_outcomes,
    build_packet_outcome_ledger,
)


def _expired_packet(packet_id: str = "rev_pkt_100") -> dict[str, object]:
    return {
        "packet_id": packet_id,
        "status": "pending",
        "posted_at": "2026-04-25T00:00:00Z",
        "expires_at_utc": "2026-04-25T00:30:00Z",
        "summary": "Old packet",
    }


def _bound_expired_packet(packet_id: str = "rev_pkt_100") -> dict[str, object]:
    packet = _expired_packet(packet_id)
    packet["packet_creation_binding"] = {
        "contract_id": "PacketCreationBinding",
        "packet_id": packet_id,
        "status": "inserted",
        "reason": "packet_bound_to_plan_row_at_creation",
        "binding_target_kind": "plan_row",
        "binding_target": "PKT-BIND-REV-PKT-100",
    }
    return packet


def test_packet_outcome_ledger_classifies_commit_delivery_evidence() -> None:
    packet = _expired_packet("rev_pkt_100")
    events = [
        {
            "event_id": "evt_1",
            "event_type": "packet_posted",
            "packet_id": "rev_pkt_101",
            "timestamp_utc": "2026-04-25T01:00:00Z",
            "kind": "system_notice",
            "summary": "rev_pkt_100 landed in commit 62ad3234",
            "body": "S0 receipt names rev_pkt_100 as delivered.",
        }
    ]

    ledger = build_packet_outcome_ledger(
        packets=[packet],
        events=events,
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    assert ledger.records[0].outcome == PacketOutcome.DELIVERED_VIA_COMMIT
    assert ledger.records[0].evidence_ref == "commit:62ad3234"


def test_packet_outcome_ledger_classifies_workflow_receipt_evidence() -> None:
    packet = _expired_packet("rev_pkt_100")
    events = [
        {
            "event_id": "evt_task_produced",
            "event_type": "packet_posted",
            "packet_id": "rev_pkt_101",
            "timestamp_utc": "2026-04-25T01:00:00Z",
            "kind": "task_produced",
            "summary": "Task receipt for rev_pkt_100",
            "body": "rev_pkt_100 produced reviewable evidence.",
        }
    ]

    ledger = build_packet_outcome_ledger(
        packets=[packet],
        events=events,
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    assert ledger.records[0].outcome == PacketOutcome.DELIVERED_VIA_COMMIT
    assert ledger.records[0].evidence_ref == "event:evt_task_produced"


def test_packet_outcome_ledger_classifies_superseding_packet() -> None:
    packet = _expired_packet("rev_pkt_100")
    events = [
        {
            "event_id": "evt_2",
            "event_type": "packet_posted",
            "packet_id": "rev_pkt_102",
            "timestamp_utc": "2026-04-25T01:00:00Z",
            "kind": "instruction",
            "summary": "Supersedes rev_pkt_100 with narrower S2 scope",
            "body": "",
        }
    ]

    ledger = build_packet_outcome_ledger(
        packets=[packet],
        events=events,
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    assert ledger.records[0].outcome == PacketOutcome.SUPERSEDED_BY
    assert ledger.records[0].evidence_ref == "packet:rev_pkt_102"
    assert ledger.records[0].superseding_packet_id == "rev_pkt_102"


def test_packet_outcome_ledger_archives_unresolved_expired_packet() -> None:
    ledger = build_packet_outcome_ledger(
        packets=[_expired_packet("rev_pkt_100")],
        events=[],
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    assert ledger.records[0].outcome == PacketOutcome.ARCHIVED
    assert (
        ledger.records[0].evidence_ref
        == "archive_classification:clock_expired_without_disposition"
    )


def test_packet_outcome_ledger_marks_plan_bound_expired_packet_durable() -> None:
    ledger = build_packet_outcome_ledger(
        packets=[_bound_expired_packet("rev_pkt_100")],
        events=[],
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    assert ledger.records[0].outcome == PacketOutcome.ARCHIVED
    assert (
        ledger.records[0].evidence_ref
        == "archive_classification:expired_after_durable_binding"
    )
    assert "durable typed ownership" in ledger.records[0].reason


def test_packet_outcome_ledger_marks_explicit_expiry_with_binding_durable() -> None:
    packet = _bound_expired_packet("rev_pkt_100")
    packet["status"] = "expired"
    events = [
        {
            "event_id": "evt_2",
            "event_type": "packet_expired",
            "packet_id": "rev_pkt_100",
            "timestamp_utc": "2026-04-25T01:30:00Z",
        },
    ]

    ledger = build_packet_outcome_ledger(
        packets=[packet],
        events=events,
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    assert (
        ledger.records[0].evidence_ref
        == "archive_classification:expired_after_durable_binding"
    )
    assert ledger.records[0].source_event_id == "evt_2"


def test_packet_outcome_ledger_prefers_explicit_expiry_over_heuristic_evidence() -> None:
    packet = _expired_packet("rev_pkt_100")
    packet["status"] = "expired"
    events = [
        {
            "event_id": "evt_1",
            "event_type": "packet_posted",
            "packet_id": "rev_pkt_101",
            "timestamp_utc": "2026-04-25T01:00:00Z",
            "kind": "finding",
            "summary": "Promoted rev_pkt_100 to a finding",
            "body": "",
        },
        {
            "event_id": "evt_2",
            "event_type": "packet_expired",
            "packet_id": "rev_pkt_100",
            "timestamp_utc": "2026-04-25T01:30:00Z",
        },
    ]

    ledger = build_packet_outcome_ledger(
        packets=[packet],
        events=events,
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    assert ledger.records[0].outcome == PacketOutcome.ARCHIVED
    assert ledger.records[0].evidence_ref == "event:evt_2"


def test_attach_packet_outcomes_keeps_source_packets_immutable() -> None:
    packet = _expired_packet("rev_pkt_100")
    ledger = build_packet_outcome_ledger(
        packets=[packet],
        events=[],
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    enriched = attach_packet_outcomes([packet], ledger)

    assert "packet_outcome" not in packet
    assert enriched[0]["packet_outcome"]["outcome"] == "archived"
    assert enriched[0]["lifecycle_current_state"] == "archived"
    assert enriched[0]["disposition"]["sink"] == "archived"


def test_attach_packet_outcomes_projects_durable_binding_disposition() -> None:
    packet = _bound_expired_packet("rev_pkt_100")
    ledger = build_packet_outcome_ledger(
        packets=[packet],
        events=[],
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    enriched = attach_packet_outcomes([packet], ledger)

    assert (
        enriched[0]["packet_outcome"]["evidence_ref"]
        == "archive_classification:expired_after_durable_binding"
    )
    assert (
        enriched[0]["acted_on_events"][0]["target_anchor"]
        == "archive_classification:expired_after_durable_binding"
    )
    assert (
        enriched[0]["disposition"]["archive_classification"]
        == "expired_after_durable_binding"
    )
