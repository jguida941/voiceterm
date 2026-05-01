"""Packet continuity read model over reduced review-channel packet rows."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass


PACKET_CONTINUITY_INDEX_CONTRACT_ID = "PacketContinuityIndex"
PACKET_CONTINUITY_INDEX_SCHEMA_VERSION = 1
_VISIBLE_SINK_PRIORITY = {
    "live_queue": 0,
    "failed_ingestion": 1,
    "recovery_required": 2,
    "carry_forward_debt": 3,
    "applied_to_plan": 4,
    "archived": 5,
}


@dataclass(frozen=True, slots=True)
class PacketContinuityRow:
    """One packet assigned to exactly one continuity sink."""

    packet_id: str
    sink: str
    lifecycle_state: str
    status: str
    disposition_sink: str
    resolution_anchor: str = ""
    latest_event_id: str = ""
    plan_id: str = ""
    target_kind: str = ""
    target_ref: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PacketContinuityIndex:
    """Complete packet-to-sink index used after compaction/replay."""

    rows: tuple[PacketContinuityRow, ...]
    schema_version: int = PACKET_CONTINUITY_INDEX_SCHEMA_VERSION
    contract_id: str = PACKET_CONTINUITY_INDEX_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        rows = [row.to_dict() for row in self.rows]
        return {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "packet_count": len(rows),
            "sink_counts": _sink_counts(rows),
            "digest": _digest(rows),
            "rows": rows,
        }


def build_packet_continuity_index(
    packets: Iterable[Mapping[str, object]],
) -> PacketContinuityIndex:
    """Return a deterministic continuity index for reduced packet rows."""
    rows = tuple(
        PacketContinuityRow(
            packet_id=_text(packet.get("packet_id")),
            sink=_continuity_sink(packet),
            lifecycle_state=_text(packet.get("lifecycle_current_state")),
            status=_text(packet.get("status")),
            disposition_sink=_disposition_sink(packet),
            resolution_anchor=_disposition_field(packet, "resolution_anchor"),
            latest_event_id=_text(packet.get("latest_event_id")),
            plan_id=_text(packet.get("plan_id")),
            target_kind=_text(packet.get("target_kind")),
            target_ref=_text(packet.get("target_ref")),
            reason=_disposition_field(packet, "reason"),
        )
        for packet in sorted(
            (dict(row) for row in packets if isinstance(row, Mapping)),
            key=lambda row: _text(row.get("packet_id")),
        )
        if _text(packet.get("packet_id"))
    )
    return PacketContinuityIndex(rows=rows)


def packet_continuity_index_from_payload(
    payload: object,
) -> dict[str, object]:
    """Return an existing continuity payload or build one from packet rows."""
    if not isinstance(payload, Mapping):
        return {}
    existing = payload.get("packet_continuity")
    if isinstance(existing, Mapping):
        return dict(existing)
    packets = payload.get("packets")
    if isinstance(packets, (list, tuple)):
        return build_packet_continuity_index(packets).to_dict()
    return {}


def compact_packet_continuity_index(
    index: Mapping[str, object],
    *,
    limit: int = 12,
) -> dict[str, object]:
    """Return a compact but auditable continuity index for bootstrap surfaces."""
    rows = _visible_rows(index.get("rows"))[:limit]
    return {
        "schema_version": int(index.get("schema_version") or 1),
        "contract_id": _text(
            index.get("contract_id") or PACKET_CONTINUITY_INDEX_CONTRACT_ID
        ),
        "packet_count": int(index.get("packet_count") or len(rows)),
        "sink_counts": dict(index.get("sink_counts") or {}),
        "digest": _text(index.get("digest")),
        "rows": [
            {
                "packet_id": _text(row.get("packet_id")),
                "sink": _text(row.get("sink")),
                "lifecycle_state": _text(row.get("lifecycle_state")),
                "resolution_anchor": _text(row.get("resolution_anchor")),
            }
            for row in rows
        ],
    }


def _continuity_sink(packet: Mapping[str, object]) -> str:
    disposition_sink = _disposition_sink(packet)
    lifecycle_state = _text(packet.get("lifecycle_current_state"))
    status = _text(packet.get("status"))
    disposition_status = _disposition_field(packet, "status")
    if disposition_sink == "plan_integrated":
        return "applied_to_plan"
    if disposition_sink == "recovery_required":
        if disposition_status in {"plan_ingestion_failed", "plan_integration_failed"}:
            return "failed_ingestion"
        return "recovery_required"
    if disposition_sink == "archived":
        return "archived"
    if (
        status == "acked"
        or lifecycle_state in {"acknowledged", "apply_pending_after_execution"}
    ):
        return "carry_forward_debt"
    return "live_queue"


def _disposition_sink(packet: Mapping[str, object]) -> str:
    disposition = packet.get("disposition")
    if isinstance(disposition, Mapping):
        return _text(disposition.get("sink"))
    return ""


def _disposition_field(packet: Mapping[str, object], field: str) -> str:
    disposition = packet.get("disposition")
    if not isinstance(disposition, Mapping):
        return ""
    return _text(disposition.get(field))


def _sink_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        sink = _text(row.get("sink")) or "unknown"
        counts[sink] = counts.get(sink, 0) + 1
    return counts


def _visible_rows(value: object) -> list[dict[str, object]]:
    rows = _dict_rows(value)
    return sorted(rows, key=_visible_row_sort_key)


def _visible_row_sort_key(row: Mapping[str, object]) -> tuple[int, int, str]:
    packet_id = _text(row.get("packet_id"))
    sink = _text(row.get("sink"))
    return (
        _VISIBLE_SINK_PRIORITY.get(sink, 99),
        -_packet_ordinal(packet_id),
        packet_id,
    )


def _packet_ordinal(packet_id: str) -> int:
    numbers = re.findall(r"\d+", packet_id)
    if not numbers:
        return 0
    try:
        return int(numbers[-1])
    except ValueError:
        return 0


def _digest(rows: list[dict[str, object]]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _dict_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [dict(row) for row in value if isinstance(row, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "PACKET_CONTINUITY_INDEX_CONTRACT_ID",
    "PACKET_CONTINUITY_INDEX_SCHEMA_VERSION",
    "PacketContinuityIndex",
    "PacketContinuityRow",
    "build_packet_continuity_index",
    "compact_packet_continuity_index",
    "packet_continuity_index_from_payload",
]
