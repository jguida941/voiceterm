"""Per-packet ingest decisions for the typed ``/develop`` controller."""

from __future__ import annotations

from dataclasses import dataclass

from .development_packet_pressure_classification import has_durable_owner_gap
from .development_packet_pressure_models import (
    PacketIngestDecision,
    PacketIntentClassification,
    TERMINAL_PACKET_CLASSIFICATIONS,
)


@dataclass(frozen=True)
class _DecisionFields:
    decision: str
    reason_code: str
    required_action: str
    next_command: str = ""
    terminal_status: str = ""
    fail_closed: bool = False


def packet_ingest_decision(
    classification: PacketIntentClassification,
    *,
    actor: str,
) -> PacketIngestDecision:
    """Classify one packet's next typed ingest/ack step."""
    if classification.durable_owner:
        return _decision(
            classification,
            _DecisionFields(
                decision="defer_existing_proof",
                reason_code="durable_owner_present",
                required_action="none",
            ),
        )
    if classification.classification in TERMINAL_PACKET_CLASSIFICATIONS:
        return _decision(
            classification,
            _DecisionFields(
                decision="terminal_receipt",
                reason_code="terminal_packet_classification",
                required_action="write_terminal_receipt",
                next_command=_terminal_command(classification),
                terminal_status=classification.classification,
            ),
        )
    if classification.classification == "manual-triage-required":
        return _decision(
            classification,
            _DecisionFields(
                decision="operator_triage",
                reason_code="manual_triage_required",
                required_action="operator_packet_triage",
                next_command=_show_command(classification),
                fail_closed=True,
            ),
        )
    if classification.terminal_receipt:
        return _decision(
            classification,
            _DecisionFields(
                decision="defer_existing_proof",
                reason_code="terminal_receipt_present",
                required_action="none",
                terminal_status=classification.terminal_receipt,
            ),
        )
    if has_durable_owner_gap(classification):
        return _decision(
            classification,
            _DecisionFields(
                decision="ingest",
                reason_code="durable_owner_gap",
                required_action="write_typed_owner_or_terminal_receipt",
                next_command=_ingest_command(classification),
            ),
        )
    if classification.classification in {"communication-only", "lifecycle-only"}:
        return _decision(
            classification,
            _DecisionFields(
                decision="ack",
                reason_code=f"{classification.classification}_packet",
                required_action="acknowledge_packet_transport",
                next_command=_ack_command(classification, actor),
            ),
        )
    return _decision(
        classification,
        _DecisionFields(
            decision="operator_triage",
            reason_code="unhandled_packet_classification",
            required_action="operator_packet_triage",
            next_command=_show_command(classification),
            fail_closed=True,
        ),
    )


def packet_ingest_decisions(
    classifications: tuple[PacketIntentClassification, ...] | list[PacketIntentClassification],
    *,
    actor: str,
) -> tuple[PacketIngestDecision, ...]:
    """Return per-packet ingest decisions for selected packet classifications."""
    return tuple(
        packet_ingest_decision(classification, actor=actor)
        for classification in classifications
    )


def _decision(
    classification: PacketIntentClassification,
    fields: _DecisionFields,
) -> PacketIngestDecision:
    return PacketIngestDecision(
        packet_id=classification.packet_id,
        classification=classification.classification,
        decision=fields.decision,
        reason_code=fields.reason_code,
        required_action=fields.required_action,
        next_command=fields.next_command,
        target_kind=_target_kind(classification),
        target_ref=classification.target_ref,
        terminal_status=fields.terminal_status,
        fail_closed=fields.fail_closed,
    )


def _target_kind(classification: PacketIntentClassification) -> str:
    if classification.target_ref.startswith("plan:"):
        return "plan"
    if classification.classification in {"durable plan", "finding", "guard", "knowledge"}:
        return "plan"
    return ""


def _ingest_command(classification: PacketIntentClassification) -> str:
    return (
        "python3 dev/scripts/devctl.py develop ingest-intent "
        f"--packet-id {classification.packet_id} --format md"
    )


def _terminal_command(classification: PacketIntentClassification) -> str:
    return (
        "python3 dev/scripts/devctl.py develop ingest-intent "
        f"--packet-id {classification.packet_id} "
        f"--terminal-status {classification.classification} --format md"
    )


def _ack_command(classification: PacketIntentClassification, actor: str) -> str:
    normalized_actor = str(actor or "").strip() or "codex"
    return (
        "python3 dev/scripts/devctl.py review-channel --action ack "
        f"--packet-id {classification.packet_id} --actor {normalized_actor} "
        "--terminal none --format md"
    )


def _show_command(classification: PacketIntentClassification) -> str:
    return (
        "python3 dev/scripts/devctl.py review-channel --action show "
        f"--packet-id {classification.packet_id} --terminal none --format md"
    )


__all__ = [
    "packet_ingest_decision",
    "packet_ingest_decisions",
]
