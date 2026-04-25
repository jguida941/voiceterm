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


def test_packet_outcome_ledger_marks_unresolved_expired_packet_lost() -> None:
    ledger = build_packet_outcome_ledger(
        packets=[_expired_packet("rev_pkt_100")],
        events=[],
        generated_at_utc="2026-04-25T02:00:00Z",
        source="test",
    )

    assert ledger.records[0].outcome == PacketOutcome.LOST
    assert ledger.records[0].evidence_ref == "expiry:2026-04-25T00:30:00Z"


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
    assert enriched[0]["packet_outcome"]["outcome"] == "lost"
