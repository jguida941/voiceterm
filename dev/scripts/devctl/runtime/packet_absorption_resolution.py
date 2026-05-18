"""Shared predicates for deciding whether packet absorption clears pressure."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .packet_absorption import packet_absorbed
from .value_coercion import coerce_string, coerce_string_items

_COMMAND_LANE_KINDS = {"action_request", "approval_request", "commit_approval"}
_TERMINAL_ABSORPTION_DISPOSITIONS = {
    "blocked",
    "rejected",
    "deferred",
    "superseded",
    "already_shipped",
    "needs_operator_decision",
}


def absorption_resolves_packet_pressure(
    packet: Mapping[str, object],
    *,
    absorption_receipts: Sequence[Mapping[str, object]] = (),
) -> bool:
    """Return whether absorption is enough to remove live packet pressure.

    Absorption proves the packet body was semantically disposed. It is not, by
    itself, proof that command-lane work was consumed or that accepted durable
    work was bound into typed plan/action state.
    """

    if not packet_absorbed(packet, absorption_receipts=absorption_receipts):
        return False
    if _packet_kind(packet) in _COMMAND_LANE_KINDS:
        return _command_lane_packet_consumed(packet)
    if not packet_requires_durable_binding(packet):
        return True
    if packet_has_effective_durable_binding(packet):
        return True
    return packet_has_terminal_absorption_disposition(packet)


def packet_requires_durable_binding(packet: Mapping[str, object]) -> bool:
    """Return whether a packet needs durable binding before pressure clears."""

    kind = _packet_kind(packet)
    if kind in _COMMAND_LANE_KINDS:
        return True
    if kind in {
        "finding",
        "plan_gap_review",
        "plan_patch_review",
        "plan_ready_gate",
        "draft",
    }:
        return True
    if _packet_text(packet, "target_kind") == "plan":
        return True
    if _packet_text(packet, "target_ref"):
        return True
    if _packet_text(packet, "intake_ref"):
        return True
    anchor_refs = packet.get("anchor_refs")
    if isinstance(anchor_refs, (list, tuple)) and any(
        coerce_string(item) for item in anchor_refs
    ):
        return True
    plan_proposal = packet.get("plan_proposal")
    if isinstance(plan_proposal, Mapping) and plan_proposal:
        return True
    text = " ".join(
        _packet_text(packet, field_name).lower()
        for field_name in ("kind", "summary", "body", "requested_action", "policy_hint")
    )
    return any(token in text for token in ("guard", "probe", "knowledge", "pattern", "research"))


def packet_has_effective_durable_binding(packet: Mapping[str, object]) -> bool:
    """Return whether packet state points at a real durable typed owner."""

    for key in (
        "durable_binding",
        "packet_durable_ingestion_receipt",
        "packet_creation_binding",
    ):
        binding = packet.get(key)
        if not isinstance(binding, Mapping) or not binding:
            continue
        if _binding_is_effective(binding):
            return True
    return False


def packet_has_terminal_absorption_disposition(packet: Mapping[str, object]) -> bool:
    """Return whether absorption carried an explicit terminal disposition."""

    for receipt in _inline_absorption_receipts(packet):
        dispositions = _receipt_absorption_dispositions(receipt)
        terminal = tuple(
            disposition
            for disposition in dispositions
            if disposition in _TERMINAL_ABSORPTION_DISPOSITIONS
        )
        if terminal and _terminal_receipt_evidence_complete(receipt, terminal):
            return True
    return False


def packet_absorption_dispositions(packet: Mapping[str, object]) -> tuple[str, ...]:
    """Return normalized action-item dispositions from inline absorption receipts."""

    rows: list[str] = []
    for receipt in _inline_absorption_receipts(packet):
        rows.extend(_receipt_absorption_dispositions(receipt))
    return tuple(dict.fromkeys(rows))


def _inline_absorption_receipts(packet: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    receipts: list[Mapping[str, object]] = []
    for key in ("absorption_receipt", "packet_absorption_receipt"):
        receipt = packet.get(key)
        if isinstance(receipt, Mapping):
            receipts.append(receipt)
    for events_key in ("absorption_events", "packet_absorption_events"):
        value = packet.get(events_key)
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            continue
        for item in value:
            if not isinstance(item, Mapping):
                continue
            receipt = item.get("packet_absorption_receipt")
            if isinstance(receipt, Mapping):
                receipts.append(receipt)
            elif coerce_string(item.get("contract_id")) == "PacketAbsorptionReceipt":
                receipts.append(item)
    return tuple(receipts)


def _command_lane_packet_consumed(packet: Mapping[str, object]) -> bool:
    lifecycle = _packet_text(packet, "lifecycle_current_state")
    if lifecycle in {"applied", "dismissed", "archived"}:
        return True
    disposition = packet.get("disposition")
    if isinstance(disposition, Mapping):
        if _packet_text(disposition, "sink") in {"applied", "dismissed", "archived"}:
            return True
    return bool(
        _packet_text(packet, "execution_failed_at_utc")
        or _packet_text(packet, "apply_pending_after_execution_at_utc")
    )


def _receipt_absorption_dispositions(receipt: Mapping[str, object]) -> tuple[str, ...]:
    rows: list[str] = []
    value = receipt.get("action_item_dispositions")
    if not isinstance(value, (list, tuple)):
        return ()
    for item in value:
        disposition = _disposition_status(coerce_string(item))
        if disposition:
            rows.append(disposition)
    return tuple(dict.fromkeys(rows))


def _terminal_receipt_evidence_complete(
    receipt: Mapping[str, object],
    dispositions: tuple[str, ...],
) -> bool:
    if not coerce_string(receipt.get("source_semantic_ingestion_receipt_id")):
        return False
    if not coerce_string_items(receipt.get("evidence_refs")):
        return False
    next_slice_refs = coerce_string_items(receipt.get("next_slice_refs"))
    blocked_reason = coerce_string(receipt.get("blocked_reason"))
    defer_reason = coerce_string(receipt.get("defer_reason"))
    superseded_packet_id = coerce_string(receipt.get("superseded_packet_id"))
    decision_rationale = coerce_string(receipt.get("decision_rationale"))
    for disposition in dispositions:
        if disposition == "deferred" and not (defer_reason and next_slice_refs):
            return False
        if disposition in {"blocked", "rejected"} and not blocked_reason:
            return False
        if disposition == "needs_operator_decision" and not (
            blocked_reason and next_slice_refs
        ):
            return False
        if disposition == "superseded" and not superseded_packet_id:
            return False
        if disposition == "already_shipped" and not decision_rationale:
            return False
    return True


def _binding_is_effective(binding: Mapping[str, object]) -> bool:
    status = _packet_text(binding, "status")
    if status in {"failed", "skipped", "deferred"}:
        return False
    if _packet_text(binding, "binding_target_kind") == "communication_only":
        return False
    return True


def _disposition_status(value: str) -> str:
    text = coerce_string(value).strip().lower()
    if not text:
        return ""
    if ":" in text:
        return text.rsplit(":", 1)[-1].strip()
    return text


def _packet_kind(packet: Mapping[str, object]) -> str:
    return _packet_text(packet, "kind")


def _packet_text(packet: Mapping[str, object], field_name: str) -> str:
    return coerce_string(packet.get(field_name)).strip()


__all__ = [
    "absorption_resolves_packet_pressure",
    "packet_absorption_dispositions",
    "packet_has_effective_durable_binding",
    "packet_has_terminal_absorption_disposition",
    "packet_requires_durable_binding",
]
