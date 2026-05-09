"""Selected-packet classification helpers for ``/develop`` pressure."""

from __future__ import annotations

from collections.abc import Mapping

from .development_packet_pressure_models import (
    DURABLE_PACKET_CLASSIFICATIONS,
    PacketIntentClassification,
    TERMINAL_PACKET_CLASSIFICATIONS,
)
from .development_packet_failure_owner import (
    CLOCK_EXPIRED_WITHOUT_DISPOSITION,
    packet_failure_class,
)
from .master_plan_contract import PlanRow
from .packet_carry_forward_sources import packet_ids_from_plan_row
from .packet_review_only import is_review_only_notice


def classify_packet(
    packet: Mapping[str, object],
    *,
    row_owner_by_packet: Mapping[str, str],
    class_owner_by_failure: Mapping[str, str] | None = None,
    terminal_receipt_by_packet: Mapping[str, str] | None = None,
) -> PacketIntentClassification:
    """Classify one packet without granting durable authority."""
    terminal_receipts = terminal_receipt_by_packet or {}
    packet_id = _text(packet.get("packet_id"))
    kind = _text(packet.get("kind"))
    status = _text(packet.get("status"))
    receipt_terminal = _text(terminal_receipts.get(packet_id))
    classification = (
        receipt_terminal
        if receipt_terminal in TERMINAL_PACKET_CLASSIFICATIONS
        else _classification(packet, kind=kind, status=status)
    )
    durable_owner = _durable_owner(
        packet,
        row_owner_by_packet=row_owner_by_packet,
        class_owner_by_failure=class_owner_by_failure or {},
    )
    terminal_receipt = receipt_terminal or _terminal_receipt(
        packet,
        classification=classification,
    )
    return PacketIntentClassification(
        packet_id=packet_id,
        kind=kind,
        status=status,
        to_role=role_for_packet(packet),
        classification=classification,
        durable_owner=durable_owner,
        terminal_receipt=terminal_receipt,
        action_required=classification in DURABLE_PACKET_CLASSIFICATIONS
        and not (durable_owner or terminal_receipt),
        reason=_classification_reason(packet, classification=classification),
        target_ref=_text(packet.get("target_ref")) or _text(packet.get("plan_id")),
        expires_at_utc=_text(packet.get("expires_at_utc")),
    )


def selected_packets(
    live_packets: list[Mapping[str, object]],
    expired_packets: list[Mapping[str, object]],
    debt_ids: set[str],
) -> list[Mapping[str, object]]:
    """Select packets that need classification coverage."""
    selected: dict[str, Mapping[str, object]] = {}
    for packet in (*live_packets, *expired_packets):
        packet_id = _text(packet.get("packet_id"))
        if packet_id:
            selected[packet_id] = packet
    for packet in live_packets:
        packet_id = _text(packet.get("packet_id"))
        if packet_id in debt_ids:
            selected[packet_id] = packet
    return list(selected.values())


def has_durable_owner_gap(item: PacketIntentClassification) -> bool:
    return (
        item.classification in DURABLE_PACKET_CLASSIFICATIONS
        and not item.durable_owner
        and not item.terminal_receipt
    )


def row_owner_by_packet(rows: tuple[PlanRow, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        for packet_id in packet_ids_from_plan_row(row):
            result[str(packet_id).strip()] = row.row_id
    return result


def role_for_packet(packet: Mapping[str, object]) -> str:
    return _text(packet.get("target_role")) or _text(packet.get("to_agent")) or "unknown"


def _classification(packet: Mapping[str, object], *, kind: str, status: str) -> str:
    terminal = _terminal_marker(packet, status=status)
    if terminal in TERMINAL_PACKET_CLASSIFICATIONS:
        return terminal
    if kind in {"action_request", "approval_request", "commit_approval"}:
        return "lifecycle-only"
    if kind == "decision" and not _has_plan_shape(packet, kind=kind):
        return "lifecycle-only"
    if _has_plan_shape(packet, kind=kind):
        return "durable plan"
    if kind == "finding":
        return "finding"
    text = _intent_text(packet)
    if "guard" in text or "probe" in text:
        return "guard"
    if any(token in text for token in ("knowledge", "pattern", "research")):
        return "knowledge"
    if kind == "decision":
        return "lifecycle-only"
    if kind in {"system_notice", "question", "instruction"}:
        return "communication-only"
    return "manual-triage-required"


def _has_plan_shape(packet: Mapping[str, object], *, kind: str) -> bool:
    if is_review_only_notice(packet, kind=kind):
        return False
    return (
        _text(packet.get("target_kind")) == "plan"
        or bool(_text(packet.get("target_ref")))
        or bool(_text(packet.get("intake_ref")))
        or bool(_rows(packet.get("anchor_refs")))
        or isinstance(packet.get("plan_proposal"), Mapping)
        or kind in {"plan_gap_review", "plan_patch_review", "plan_ready_gate", "draft"}
    )


def _durable_owner(
    packet: Mapping[str, object],
    *,
    row_owner_by_packet: Mapping[str, str],
    class_owner_by_failure: Mapping[str, str],
) -> str:
    packet_id = _text(packet.get("packet_id"))
    if row_owner_by_packet.get(packet_id):
        return row_owner_by_packet[packet_id]
    failure_class = packet_failure_class(packet)
    if failure_class and class_owner_by_failure.get(failure_class):
        return class_owner_by_failure[failure_class]
    binding = packet.get("packet_durable_ingestion_receipt") or packet.get("durable_binding")
    if isinstance(binding, Mapping):
        return _text(binding.get("target_ref")) or _text(binding.get("contract_id"))
    return ""


def _terminal_receipt(packet: Mapping[str, object], *, classification: str) -> str:
    if classification in TERMINAL_PACKET_CLASSIFICATIONS:
        return classification
    if _has_unresolved_expired_archive_classification(packet):
        return ""
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if lifecycle in {"archived", "applied", "dismissed"}:
        return lifecycle
    disposition = packet.get("disposition")
    if isinstance(disposition, Mapping):
        return _text(disposition.get("sink"))
    return ""


def _terminal_marker(packet: Mapping[str, object], *, status: str) -> str:
    if status in TERMINAL_PACKET_CLASSIFICATIONS:
        return status
    disposition = packet.get("disposition")
    if isinstance(disposition, Mapping):
        return _text(disposition.get("classification")) or _text(disposition.get("sink"))
    return _text(packet.get("terminal_status"))


def _classification_reason(
    packet: Mapping[str, object],
    *,
    classification: str,
) -> str:
    if classification == "communication-only":
        return "packet carries no typed durable target"
    if classification == "lifecycle-only":
        return "packet belongs to packet/runtime lifecycle"
    if classification in TERMINAL_PACKET_CLASSIFICATIONS:
        return "packet already has terminal classification or typed terminal receipt"
    if _text(packet.get("target_ref")) or _text(packet.get("target_kind")) == "plan":
        return "packet carries typed target metadata"
    return "content or kind indicates durable intent"


def _intent_text(packet: Mapping[str, object]) -> str:
    return " ".join(
        _text(packet.get(field)).lower()
        for field in ("kind", "summary", "body", "requested_action", "policy_hint")
    )


def _rows(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _has_unresolved_expired_archive_classification(packet: Mapping[str, object]) -> bool:
    return packet_failure_class(packet) == CLOCK_EXPIRED_WITHOUT_DISPOSITION


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "CLOCK_EXPIRED_WITHOUT_DISPOSITION",
    "classify_packet",
    "has_durable_owner_gap",
    "role_for_packet",
    "row_owner_by_packet",
    "selected_packets",
]
