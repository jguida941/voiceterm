"""Packet lifecycle attention helpers for control-decision payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .packet_absorption import packet_semantically_ingested
from .packet_absorption_resolution import absorption_resolves_packet_pressure
from .value_coercion import coerce_string


def packet_by_id(payload: Mapping[str, object], packet_id: str) -> Mapping[str, object]:
    packets = payload.get("packets")
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return {}
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        if coerce_string(packet.get("packet_id")).strip() == packet_id:
            return packet
    return {}


def packet_lifecycle_attention(
    packet: Mapping[str, object],
    *,
    packet_id: str,
) -> dict[str, object]:
    base = {
        "latest_attention_packet_id": packet_id,
        "pending_packet_count": 1,
        "pivot_required": True,
    }
    if packet and _packet_has_absorption_receipt(packet):
        return {}
    if packet and _packet_has_any_absorption_receipt(packet):
        return base
    if packet and packet_semantically_ingested(packet):
        return {
            **base,
            "absorption_required": True,
            "absorption_packet_id": packet_id,
            "absorption_command": (
                "python3 dev/scripts/devctl.py review-channel --action absorb "
                f"--packet-id {packet_id}"
            ),
            "absorption_reason": "packet_semantically_ingested_without_absorption",
        }
    if packet and _packet_body_observed(packet):
        return {
            **base,
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
    return {
        **base,
        "body_open_required": True,
        "body_open_packet_id": packet_id,
        "unopened_body_packet_ids": [packet_id],
    }


def _packet_has_absorption_receipt(packet: Mapping[str, object]) -> bool:
    receipts = _packet_absorption_receipts(packet)
    return bool(receipts) and absorption_resolves_packet_pressure(
        packet,
        absorption_receipts=tuple(receipts),
    )


def _packet_has_any_absorption_receipt(packet: Mapping[str, object]) -> bool:
    return bool(_packet_absorption_receipts(packet))


def _packet_body_observed(packet: Mapping[str, object]) -> bool:
    return bool(
        coerce_string(packet.get("body_observed_at_utc")).strip()
        or coerce_string(packet.get("body_observed_event_id")).strip()
        or _sequence_has_rows(packet.get("body_observation_events"))
    )


def _packet_absorption_receipts(packet: Mapping[str, object]) -> list[Mapping[str, object]]:
    receipts: list[Mapping[str, object]] = []
    for key in ("packet_absorption_receipt", "absorption_receipt"):
        receipt = packet.get(key)
        if isinstance(receipt, Mapping) and _nonempty_receipt(receipt):
            receipts.append(receipt)
    events = packet.get("absorption_events")
    if isinstance(events, Sequence) and not isinstance(events, (str, bytes)):
        for item in events:
            if not isinstance(item, Mapping):
                continue
            receipt = item.get("packet_absorption_receipt")
            if isinstance(receipt, Mapping) and _nonempty_receipt(receipt):
                receipts.append(receipt)
            elif _nonempty_receipt(item):
                receipts.append(item)
    return receipts


def _nonempty_receipt(value: object) -> bool:
    return isinstance(value, Mapping) and bool(
        coerce_string(value.get("packet_id")).strip()
        or coerce_string(value.get("receipt_id")).strip()
        or coerce_string(value.get("contract_id")).strip()
    )


def _sequence_has_rows(value: object) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and bool(value)
    )
