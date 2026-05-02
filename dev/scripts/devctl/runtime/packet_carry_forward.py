"""Carry-forward projection for packets that are seen but not owned."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
import re


PACKET_CARRY_FORWARD_CONTRACT_ID = "PacketCarryForwardDebt"
PACKET_CARRY_FORWARD_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class PacketCarryForwardDebt:
    """One packet that still needs a durable owner or terminal disposition."""

    packet_id: str
    kind: str
    status: str
    lifecycle_state: str
    from_agent: str
    to_agent: str
    summary: str
    plan_id: str = ""
    intake_ref: str = ""
    anchor_refs: tuple[str, ...] = ()
    latest_event_id: str = ""
    posted_at: str = ""
    acked_at_utc: str = ""
    reason: str = "acked_without_terminal_or_durable_owner"
    schema_version: int = PACKET_CARRY_FORWARD_SCHEMA_VERSION
    contract_id: str = PACKET_CARRY_FORWARD_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["anchor_refs"] = list(self.anchor_refs)
        return payload


def packet_carry_forward_debts(
    packets: Iterable[Mapping[str, object]],
    *,
    durable_packet_ids: Iterable[str] = (),
    min_packet_number: int = 0,
) -> tuple[PacketCarryForwardDebt, ...]:
    """Return packets that lack terminal disposition or durable ownership."""
    durable = {str(packet_id).strip() for packet_id in durable_packet_ids}
    debts: list[PacketCarryForwardDebt] = []
    for packet in packets:
        packet_id = _text(packet.get("packet_id"))
        if not packet_id or _packet_number(packet_id) < min_packet_number:
            continue
        if packet_id in durable:
            continue
        reason = _carry_forward_reason(packet)
        if not reason:
            continue
        debts.append(_debt_from_packet(packet, packet_id=packet_id, reason=reason))
    return tuple(debts)


def durable_packet_ids_from_plan_rows(
    plan_rows: Iterable[object],
) -> tuple[str, ...]:
    """Return packet ids already promoted into typed plan rows."""
    return _unique_packet_ids_from_rows(plan_rows, preferred_fields=("sourced_from_packets",))


def durable_packet_ids_from_finding_rows(
    finding_rows: Iterable[object],
) -> tuple[str, ...]:
    """Return packet ids already promoted into durable finding-review rows."""
    return _unique_packet_ids_from_rows(
        finding_rows,
        preferred_fields=(
            "sourced_from_packets",
            "source_packet_ids",
            "source_packets",
            "packet_ids",
            "causal_packet_ids",
            "responds_to_packet_ids",
            "responds_to_packet_id",
            "source_packet_id",
            "packet_id",
        ),
        fallback_text_fields=(
            "notes",
            "source_command",
            "risk_type",
            "finding_id",
            "check_id",
        ),
    )


def _unique_packet_ids_from_rows(
    rows: Iterable[object],
    *,
    preferred_fields: tuple[str, ...],
    fallback_text_fields: tuple[str, ...] = (),
) -> tuple[str, ...]:
    packet_ids: list[str] = []
    for row in rows:
        for packet_id in _source_packet_ids(
            row,
            preferred_fields=preferred_fields,
            fallback_text_fields=fallback_text_fields,
        ):
            if packet_id and packet_id not in packet_ids:
                packet_ids.append(packet_id)
    return tuple(packet_ids)


def _debt_from_packet(
    packet: Mapping[str, object],
    *,
    packet_id: str,
    reason: str,
) -> PacketCarryForwardDebt:
    return PacketCarryForwardDebt(
        packet_id=packet_id,
        kind=_text(packet.get("kind")),
        status=_text(packet.get("status")),
        lifecycle_state=_text(packet.get("lifecycle_current_state")),
        from_agent=_text(packet.get("from_agent")),
        to_agent=_text(packet.get("to_agent")),
        summary=_text(packet.get("summary")),
        plan_id=_text(packet.get("plan_id")),
        intake_ref=_text(packet.get("intake_ref")),
        anchor_refs=tuple(_rows(packet.get("anchor_refs"))),
        latest_event_id=_text(packet.get("latest_event_id")),
        posted_at=_text(packet.get("posted_at")),
        acked_at_utc=_text(packet.get("acked_at_utc")),
        reason=reason,
    )


def _carry_forward_reason(packet: Mapping[str, object]) -> str:
    if _has_creation_binding(packet):
        return ""
    outcome = packet.get("packet_outcome")
    outcome_text = ""
    if isinstance(outcome, Mapping):
        outcome_text = _text(outcome.get("outcome"))
    if outcome_text == "promoted_to_finding":
        return "promoted_to_finding_without_durable_owner"
    if outcome_text in {"archived", "expired_unrecoverable", "lost"}:
        if _packet_has_durable_intent(packet):
            return "expired_packet_without_durable_owner"
    disposition = packet.get("disposition")
    disposition_sink = ""
    if isinstance(disposition, Mapping):
        disposition_sink = _text(disposition.get("sink"))
    if disposition_sink == "recovery_required":
        return _text(packet.get("lifecycle_current_state")) or "recovery_required"
    if _text(packet.get("status")) != "acked":
        return ""
    if _rows(packet.get("acted_on_events")):
        return ""
    return "acked_without_terminal_or_durable_owner"


def _packet_has_durable_intent(packet: Mapping[str, object]) -> bool:
    text = " ".join(
        _text(packet.get(key)).lower()
        for key in (
            "kind",
            "summary",
            "body",
            "requested_action",
            "policy_hint",
            "plan_id",
            "intake_ref",
        )
    )
    intent_tokens = (
        "finding",
        "plan",
        "guard",
        "probe",
        "issue",
        "bug",
        "architecture",
        "candidate",
        "promote",
        "master",
        "ingest",
    )
    return any(token in text for token in intent_tokens)


def _has_creation_binding(packet: Mapping[str, object]) -> bool:
    binding = packet.get("packet_creation_binding")
    if not isinstance(binding, Mapping):
        binding = packet.get("durable_binding")
    if not isinstance(binding, Mapping):
        return False
    status = _text(binding.get("status"))
    target = _text(binding.get("binding_target"))
    return bool(target and status in {"inserted", "updated", "already_present"})


def _source_packet_ids(
    row: object,
    *,
    preferred_fields: tuple[str, ...],
    fallback_text_fields: tuple[str, ...],
) -> tuple[str, ...]:
    packet_ids: list[str] = []
    if isinstance(row, Mapping):
        for field in preferred_fields:
            packet_ids.extend(_packet_id_values(row.get(field)))
        for field in fallback_text_fields:
            packet_ids.extend(_packet_ids_from_text(_text(row.get(field))))
        return _dedupe(packet_ids)
    for field in preferred_fields:
        packet_ids.extend(_packet_id_values(getattr(row, field, ())))
    for field in fallback_text_fields:
        packet_ids.extend(_packet_ids_from_text(_text(getattr(row, field, ""))))
    return _dedupe(packet_ids)


def _rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _packet_id_values(value: object) -> list[str]:
    if isinstance(value, str):
        return _packet_ids_from_text(value)
    return _rows(value)


def _packet_ids_from_text(value: str) -> list[str]:
    return re.findall(r"\brev_pkt_\d+\b", value)


def _dedupe(values: list[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.append(text)
    return tuple(seen)


def _packet_number(packet_id: str) -> int:
    match = re.search(r"(\d+)$", packet_id)
    if match is None:
        return 0
    return int(match.group(1))


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "PACKET_CARRY_FORWARD_CONTRACT_ID",
    "PACKET_CARRY_FORWARD_SCHEMA_VERSION",
    "PacketCarryForwardDebt",
    "durable_packet_ids_from_finding_rows",
    "durable_packet_ids_from_plan_rows",
    "packet_carry_forward_debts",
]
