"""Tests for per-packet ingest decisions."""

from __future__ import annotations

from dev.scripts.devctl.runtime.development_packet_ingest_decision import (
    packet_ingest_decision,
)
from dev.scripts.devctl.runtime.development_packet_pressure_models import (
    PacketIntentClassification,
)


def test_durable_owner_gap_ingests_existing_plan_path() -> None:
    decision = packet_ingest_decision(
        _classification(
            classification="durable plan",
            packet_id="rev_pkt_1",
            target_ref="plan:MP-377",
        ),
        actor="codex",
    )

    assert decision.decision == "ingest"
    assert decision.required_action == "write_typed_owner_or_terminal_receipt"
    assert decision.target_kind == "plan"
    assert "develop ingest-intent --packet-id rev_pkt_1" in decision.next_command


def test_communication_packet_uses_existing_ack_lifecycle() -> None:
    decision = packet_ingest_decision(
        _classification(classification="communication-only", packet_id="rev_pkt_2"),
        actor="claude",
    )

    assert decision.decision == "ack"
    assert decision.required_action == "acknowledge_packet_transport"
    assert "review-channel --action ack" in decision.next_command
    assert "--actor claude" in decision.next_command


def test_terminal_classification_writes_terminal_receipt() -> None:
    decision = packet_ingest_decision(
        _classification(classification="obsolete", packet_id="rev_pkt_3"),
        actor="codex",
    )

    assert decision.decision == "terminal_receipt"
    assert decision.terminal_status == "obsolete"
    assert "--terminal-status obsolete" in decision.next_command


def test_existing_owner_defers_to_existing_proof() -> None:
    decision = packet_ingest_decision(
        _classification(
            classification="finding",
            packet_id="rev_pkt_4",
            durable_owner="PKT-BIND-REV-PKT-4",
        ),
        actor="codex",
    )

    assert decision.decision == "defer_existing_proof"
    assert decision.required_action == "none"
    assert decision.next_command == ""


def test_manual_triage_fails_closed_to_operator_packet_review() -> None:
    decision = packet_ingest_decision(
        _classification(classification="manual-review-required", packet_id="rev_pkt_5"),
        actor="codex",
    )

    assert decision.decision == "operator_review"
    assert decision.required_action == "operator_packet_review"
    assert decision.fail_closed is True
    assert "review-channel --action show --packet-id rev_pkt_5" in decision.next_command


def _classification(
    *,
    classification: str,
    packet_id: str,
    durable_owner: str = "",
    target_ref: str = "",
) -> PacketIntentClassification:
    return PacketIntentClassification(
        packet_id=packet_id,
        kind="finding",
        status="pending",
        to_role="codex",
        classification=classification,
        durable_owner=durable_owner,
        target_ref=target_ref,
    )
