"""Carry-forward projection for packets that are seen but not owned."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
import re

from .packet_carry_forward_binding import (
    creation_binding,
    has_durable_packet_binding,
)
from .packet_carry_forward_sources import (
    durable_packet_ids_from_finding_rows,
    durable_packet_ids_from_plan_rows,
)
from .packet_review_only import is_review_only_notice


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
    if has_durable_packet_binding(packet):
        return ""
    binding = creation_binding(packet)
    has_durable_intent = _packet_has_durable_intent(packet)
    binding_reason = _binding_carry_forward_reason(binding, has_durable_intent)
    if binding_reason:
        return binding_reason
    outcome_reason = _outcome_carry_forward_reason(packet, has_durable_intent)
    if outcome_reason:
        return outcome_reason
    disposition_reason = _disposition_carry_forward_reason(packet)
    if disposition_reason:
        return disposition_reason
    return _status_carry_forward_reason(packet, has_durable_intent)


def _binding_carry_forward_reason(
    binding: Mapping[str, object],
    has_durable_intent: bool,
) -> str:
    if not has_durable_intent:
        return ""
    return {
        "failed": "creation_binding_failed_without_durable_owner",
        "deferred": "creation_binding_deferred_without_durable_owner",
        "skipped": "durable_intent_classified_communication_only",
    }.get(_text(binding.get("status")), "")


def _outcome_carry_forward_reason(
    packet: Mapping[str, object],
    has_durable_intent: bool,
) -> str:
    outcome = packet.get("packet_outcome")
    outcome_text = ""
    if isinstance(outcome, Mapping):
        outcome_text = _text(outcome.get("outcome"))
    if outcome_text == "promoted_to_finding":
        return "promoted_to_finding_without_durable_owner"
    if outcome_text in {"archived", "expired_unrecoverable", "lost"} and has_durable_intent:
        return "expired_packet_without_durable_owner"
    return ""


def _disposition_carry_forward_reason(packet: Mapping[str, object]) -> str:
    disposition = packet.get("disposition")
    disposition_sink = ""
    if isinstance(disposition, Mapping):
        disposition_sink = _text(disposition.get("sink"))
    if disposition_sink == "recovery_required":
        return _text(packet.get("lifecycle_current_state")) or "recovery_required"
    return ""


def _status_carry_forward_reason(
    packet: Mapping[str, object],
    has_durable_intent: bool,
) -> str:
    status = _text(packet.get("status"))
    if status == "pending" and has_durable_intent:
        return "pending_durable_intent_without_creation_binding"
    if status != "acked":
        return ""
    if _rows(packet.get("acted_on_events")):
        return ""
    if not has_durable_intent:
        return ""
    return "acked_without_terminal_or_durable_owner"


def _packet_has_durable_intent(packet: Mapping[str, object]) -> bool:
    kind = _text(packet.get("kind"))
    if is_review_only_notice(packet, kind=kind):
        return False
    if kind in _COMMUNICATION_ONLY_KINDS:
        if _text(packet.get("target_kind")) == "plan":
            return True
        if isinstance(packet.get("plan_proposal"), Mapping):
            return True
        text = _packet_intent_text(packet)
        intent_tokens = (
            "architecture",
            "bug",
            "finding",
            "fix",
            "ingest",
            "issue",
            "promote",
        )
        return any(token in text for token in intent_tokens)
    if _text(packet.get("target_kind")) == "plan":
        return True
    if _text(packet.get("target_ref")) or _text(packet.get("intake_ref")):
        return True
    if _rows(packet.get("anchor_refs")):
        return True
    if isinstance(packet.get("plan_proposal"), Mapping):
        return True
    if kind in {"finding", "plan_gap_review", "plan_patch_review"}:
        return True
    text = _packet_intent_text(packet)
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


def _packet_intent_text(packet: Mapping[str, object]) -> str:
    return " ".join(
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


_COMMUNICATION_ONLY_KINDS = frozenset(
    {
        "approval_request",
        "commit_approval",
        "instruction",
        "question",
        "system_notice",
    }
)


def _rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


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
