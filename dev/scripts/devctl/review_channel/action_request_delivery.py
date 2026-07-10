"""Delivery receipts for event-backed action_request packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from ..time_utils import utc_timestamp
from .packet_lifecycle import project_packet_lifecycle

_RECEIPT_SCHEMA_VERSION = 1
_RECEIPT_CONTRACT_ID = "ActionRequestDeliveryReceipt"
_RECEIPT_DIRNAME = "action_request_delivery"
_DELIVERY_FIELDS = (
    "delivery_emitted_at_utc",
    "delivery_observed_at_utc",
    "delivery_observed_by",
    "execution_started_at_utc",
    "execution_started_by",
    "execution_failed_at_utc",
    "execution_failed_by",
    "execution_failed_reason",
    "apply_pending_after_execution_at_utc",
    "apply_pending_after_execution_by",
    "apply_pending_after_execution_reason",
    "command_output_observed_at_utc",
    "command_output_observed_by",
    "command_output_ref",
    "command_output_summary",
)


def seed_action_request_delivery_receipt(
    *,
    artifact_root: Path,
    packet: Mapping[str, object],
) -> None:
    """Ensure one action-request receipt exists as soon as the packet is posted."""
    if not _is_action_request(packet):
        return
    receipt = _load_receipt(_receipt_path(artifact_root, packet_id=_packet_id(packet)))
    receipt = _merge_receipt_defaults(receipt=receipt, packet=packet)
    _write_receipt(artifact_root=artifact_root, receipt=receipt)


def mark_action_request_packets_observed(
    *,
    artifact_root: Path,
    packets: Sequence[object],
    observer: str,
) -> bool:
    """Mark live action-request packets as observed by one targeted inbox poll."""
    changed = False
    observer_id = str(observer).strip()
    if not observer_id:
        return False
    observed_at = utc_timestamp()
    for raw_packet in packets:
        packet = raw_packet if isinstance(raw_packet, Mapping) else None
        if packet is None or not _is_action_request(packet):
            continue
        receipt = _load_receipt(
            _receipt_path(artifact_root, packet_id=_packet_id(packet))
        )
        receipt = _merge_receipt_defaults(receipt=receipt, packet=packet)
        if str(receipt.get("delivery_observed_at_utc") or "").strip():
            continue
        receipt["delivery_observed_at_utc"] = observed_at
        receipt["delivery_observed_by"] = observer_id
        _write_receipt(artifact_root=artifact_root, receipt=receipt)
        changed = True
    return changed


def record_action_request_execution_start(
    *,
    artifact_root: Path,
    packet: Mapping[str, object],
    actor: str,
    started_at_utc: str,
) -> None:
    """Persist execution-start evidence for one action_request ack/apply transition."""
    if not _is_action_request(packet):
        return
    started_at = str(started_at_utc).strip() or utc_timestamp()
    actor_id = str(actor).strip() or str(packet.get("to_agent") or "").strip()
    receipt = _load_receipt(_receipt_path(artifact_root, packet_id=_packet_id(packet)))
    receipt = _merge_receipt_defaults(receipt=receipt, packet=packet)
    if not str(receipt.get("delivery_observed_at_utc") or "").strip():
        receipt["delivery_observed_at_utc"] = started_at
        receipt["delivery_observed_by"] = actor_id
    if not str(receipt.get("execution_started_at_utc") or "").strip():
        receipt["execution_started_at_utc"] = started_at
    if actor_id:
        receipt["execution_started_by"] = actor_id
    _write_receipt(artifact_root=artifact_root, receipt=receipt)


def record_action_request_execution_failure(
    *,
    artifact_root: Path,
    packet: Mapping[str, object],
    actor: str,
    failed_at_utc: str,
    reason: str,
) -> None:
    """Persist blocked execution evidence for one action_request."""
    if not _is_action_request(packet):
        return
    failed_at = str(failed_at_utc).strip() or utc_timestamp()
    actor_id = str(actor).strip() or str(packet.get("to_agent") or "").strip()
    receipt = _load_receipt(_receipt_path(artifact_root, packet_id=_packet_id(packet)))
    receipt = _merge_receipt_defaults(receipt=receipt, packet=packet)
    if not str(receipt.get("execution_started_at_utc") or "").strip():
        receipt["execution_started_at_utc"] = failed_at
        receipt["execution_started_by"] = actor_id
    receipt["execution_failed_at_utc"] = failed_at
    receipt["execution_failed_by"] = actor_id
    receipt["execution_failed_reason"] = str(reason).strip() or "execution_blocked"
    _write_receipt(artifact_root=artifact_root, receipt=receipt)


def record_action_request_apply_pending_after_execution(
    *,
    artifact_root: Path,
    packet: Mapping[str, object],
    actor: str,
    pending_at_utc: str,
    reason: str,
) -> None:
    """Persist commit-landed-but-packet-apply-pending evidence."""
    if not _is_action_request(packet):
        return
    pending_at = str(pending_at_utc).strip() or utc_timestamp()
    actor_id = str(actor).strip() or str(packet.get("to_agent") or "").strip()
    receipt = _load_receipt(_receipt_path(artifact_root, packet_id=_packet_id(packet)))
    receipt = _merge_receipt_defaults(receipt=receipt, packet=packet)
    if not str(receipt.get("execution_started_at_utc") or "").strip():
        receipt["execution_started_at_utc"] = pending_at
        receipt["execution_started_by"] = actor_id
    receipt["apply_pending_after_execution_at_utc"] = pending_at
    receipt["apply_pending_after_execution_by"] = actor_id
    receipt["apply_pending_after_execution_reason"] = (
        str(reason).strip() or "packet_apply_failed_after_commit"
    )
    _write_receipt(artifact_root=artifact_root, receipt=receipt)


def attach_action_request_delivery_receipts(
    *,
    packets: Sequence[object],
    artifact_root: Path | None,
) -> list[dict[str, object]]:
    """Hydrate action-request delivery receipt fields into reduced packet rows."""
    hydrated: list[dict[str, object]] = []
    for raw_packet in packets:
        if not isinstance(raw_packet, Mapping):
            continue
        packet = dict(raw_packet)
        if not _is_action_request(packet):
            hydrated.append(packet)
            continue
        for field in _DELIVERY_FIELDS:
            packet.setdefault(field, "")
        if not str(packet.get("delivery_emitted_at_utc") or "").strip():
            packet["delivery_emitted_at_utc"] = str(
                packet.get("posted_at") or packet.get("timestamp_utc") or ""
            ).strip()
        if not str(packet.get("execution_started_at_utc") or "").strip():
            packet["execution_started_at_utc"] = _default_execution_started_at(packet)
        if not str(packet.get("execution_started_by") or "").strip():
            packet["execution_started_by"] = _default_execution_started_by(packet)
        if artifact_root is not None:
            receipt = _load_receipt(
                _receipt_path(artifact_root, packet_id=_packet_id(packet))
            )
            if receipt:
                for field in _DELIVERY_FIELDS:
                    value = str(receipt.get(field) or "").strip()
                    if value and not str(packet.get(field) or "").strip():
                        packet[field] = value
        packet = project_packet_lifecycle(packet)
        hydrated.append(packet)
    return hydrated


def _default_execution_started_at(packet: Mapping[str, object]) -> str:
    for candidate in ("execution_started_at_utc", "applied_at_utc"):
        value = str(packet.get(candidate) or "").strip()
        if value:
            return value
    return ""


def _default_execution_started_by(packet: Mapping[str, object]) -> str:
    return str(packet.get("execution_started_by") or "").strip()


def _merge_receipt_defaults(
    *,
    receipt: dict[str, object] | None,
    packet: Mapping[str, object],
) -> dict[str, object]:
    packet_id = _packet_id(packet)
    merged = dict(receipt or {})
    merged["schema_version"] = _RECEIPT_SCHEMA_VERSION
    merged["contract_id"] = _RECEIPT_CONTRACT_ID
    merged["packet_id"] = packet_id
    merged["trace_id"] = str(packet.get("trace_id") or "").strip()
    merged["to_agent"] = str(packet.get("to_agent") or "").strip()
    merged["requested_action"] = str(packet.get("requested_action") or "").strip()
    merged["target_kind"] = str(packet.get("target_kind") or "").strip()
    merged["target_ref"] = str(packet.get("target_ref") or "").strip()
    merged["target_revision"] = str(packet.get("target_revision") or "").strip()
    merged.setdefault(
        "delivery_emitted_at_utc",
        str(packet.get("delivery_emitted_at_utc") or packet.get("posted_at") or "").strip(),
    )
    merged.setdefault("delivery_observed_at_utc", "")
    merged.setdefault("delivery_observed_by", "")
    merged.setdefault(
        "execution_started_at_utc",
        _default_execution_started_at(packet),
    )
    merged.setdefault(
        "execution_started_by",
        _default_execution_started_by(packet),
    )
    merged.setdefault("execution_failed_at_utc", "")
    merged.setdefault("execution_failed_by", "")
    merged.setdefault("execution_failed_reason", "")
    merged.setdefault("apply_pending_after_execution_at_utc", "")
    merged.setdefault("apply_pending_after_execution_by", "")
    merged.setdefault("apply_pending_after_execution_reason", "")
    merged.setdefault("command_output_observed_at_utc", "")
    merged.setdefault("command_output_observed_by", "")
    merged.setdefault("command_output_ref", "")
    merged.setdefault("command_output_summary", "")
    return merged


def _receipt_root(artifact_root: Path) -> Path:
    return artifact_root / _RECEIPT_DIRNAME


def _receipt_path(artifact_root: Path, *, packet_id: str) -> Path:
    return _receipt_root(artifact_root) / f"{packet_id}.json"


def _load_receipt(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_receipt(*, artifact_root: Path, receipt: Mapping[str, object]) -> None:
    packet_id = str(receipt.get("packet_id") or "").strip()
    if not packet_id:
        return
    receipt_path = _receipt_path(artifact_root, packet_id=packet_id)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(dict(receipt), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _is_action_request(packet: Mapping[str, object]) -> bool:
    return str(packet.get("kind") or "").strip() == "action_request"


def _packet_id(packet: Mapping[str, object]) -> str:
    return str(packet.get("packet_id") or "").strip()
