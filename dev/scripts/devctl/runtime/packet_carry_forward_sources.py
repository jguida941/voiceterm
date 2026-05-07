"""Durable source-packet extraction for carry-forward analysis."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import re


def durable_packet_ids_from_plan_rows(
    plan_rows: Iterable[object],
) -> tuple[str, ...]:
    """Return packet ids already promoted into typed plan rows."""
    packet_ids: list[str] = []
    for row in plan_rows:
        for packet_id in packet_ids_from_plan_row(row):
            if packet_id and packet_id not in packet_ids:
                packet_ids.append(packet_id)
    return tuple(packet_ids)


def packet_ids_from_plan_row(row: object) -> tuple[str, ...]:
    """Return packet ids referenced by one typed plan row."""
    return _source_packet_ids(
        row,
        preferred_fields=(
            "sourced_from_packets",
            "anchor_refs",
            "work_evidence_ids",
            "source_doc_path",
            "target_ref",
        ),
        fallback_text_fields=(),
    )


def durable_packet_ids_from_finding_rows(
    finding_rows: Iterable[object],
) -> tuple[str, ...]:
    """Return packet ids already promoted into durable finding-review rows."""
    packet_ids: list[str] = []
    preferred_fields = (
        "sourced_from_packets",
        "source_packet_ids",
        "source_packets",
        "packet_ids",
        "causal_packet_ids",
        "responds_to_packet_ids",
        "responds_to_packet_id",
        "source_packet_id",
        "packet_id",
    )
    fallback_text_fields = (
        "notes",
        "source_command",
        "risk_type",
        "finding_id",
        "check_id",
    )
    for row in finding_rows:
        for packet_id in _source_packet_ids(
            row,
            preferred_fields=preferred_fields,
            fallback_text_fields=fallback_text_fields,
        ):
            if packet_id and packet_id not in packet_ids:
                packet_ids.append(packet_id)
    return tuple(packet_ids)


def _source_packet_ids(
    row: object,
    *,
    preferred_fields: tuple[str, ...],
    fallback_text_fields: tuple[str, ...],
) -> tuple[str, ...]:
    packet_ids: list[str] = []
    if isinstance(row, Mapping):
        for field in preferred_fields:
            value = row.get(field)
            if isinstance(value, str):
                packet_ids.extend(_packet_ids_from_text(value))
            else:
                packet_ids.extend(_rows(value))
        for field in fallback_text_fields:
            packet_ids.extend(_packet_ids_from_text(_text(row.get(field))))
        return _dedupe(packet_ids)
    for field in preferred_fields:
        value = getattr(row, field, ())
        if isinstance(value, str):
            packet_ids.extend(_packet_ids_from_text(value))
        else:
            packet_ids.extend(_rows(value))
    for field in fallback_text_fields:
        packet_ids.extend(_packet_ids_from_text(_text(getattr(row, field, ""))))
    return _dedupe(packet_ids)


def _packet_ids_from_text(value: str) -> list[str]:
    return re.findall(r"\brev_pkt_\d+\b", value)


def _dedupe(values: list[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    return tuple(seen)


def _rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    packet_ids: list[str] = []
    for item in value:
        packet_ids.extend(_packet_ids_from_text(str(item or "").strip()))
    return packet_ids


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "durable_packet_ids_from_finding_rows",
    "durable_packet_ids_from_plan_rows",
    "packet_ids_from_plan_row",
]
