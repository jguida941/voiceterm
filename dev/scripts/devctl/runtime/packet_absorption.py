"""Runtime helpers for packet acknowledgment versus semantic absorption."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from .value_coercion import coerce_int, coerce_string, coerce_string_items

PACKET_ABSORPTION_RECEIPT_CONTRACT_ID = "PacketAbsorptionReceipt"
PACKET_SEMANTIC_INGESTION_RECEIPT_CONTRACT_ID = "PacketSemanticIngestionReceipt"
PACKET_ABSORPTION_GUARD_CONTRACT_ID = "PacketAbsorptionRequiredGuard"
PACKET_ABSORPTION_SCHEMA_VERSION = 1

ACTIONABLE_PACKET_KINDS = frozenset(
    {
        "action_request",
        "decision",
        "finding",
        "proposal",
        "task_started",
        "task_produced",
    }
)
PACKET_ABSORPTION_ALLOWED_DISPOSITIONS = frozenset(
    {
        "accepted",
        "rejected",
        "deferred",
        "superseded",
        "already_shipped",
        "needs_operator_decision",
    }
)
PACKET_SEMANTIC_INGESTION_ALLOWED_DISPOSITIONS = (
    PACKET_ABSORPTION_ALLOWED_DISPOSITIONS | frozenset({"blocked"})
)


@dataclass(frozen=True, slots=True)
class PacketAbsorptionReceipt:
    """Proof that a packet body was parsed into typed action dispositions."""

    receipt_id: str
    packet_id: str
    body_sha256: str
    absorbed_by_actor: str
    absorbed_by_role: str
    absorbed_by_session_id: str
    absorbed_at_utc: str
    action_item_dispositions: tuple[str, ...] = ()
    resulting_decision: str = ""
    decision_rationale: str = ""
    defer_reason: str = ""
    blocked_reason: str = ""
    next_slice_refs: tuple[str, ...] = ()
    superseded_packet_id: str = ""
    evidence_refs: tuple[str, ...] = ()
    schema_version: int = PACKET_ABSORPTION_SCHEMA_VERSION
    contract_id: str = PACKET_ABSORPTION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["action_item_dispositions"] = list(self.action_item_dispositions)
        payload["next_slice_refs"] = list(self.next_slice_refs)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class PacketSemanticActionItem:
    """One parsed action item from a packet body."""

    action_item_id: str
    kind: str
    disposition: str
    target_ref: str = ""
    slice_ref: str = ""
    packet_ref: str = ""
    reason: str = ""
    evidence_refs: tuple[str, ...] = ()
    next_slice_refs: tuple[str, ...] = ()
    blocked_reason: str = ""
    superseded_packet_id: str = ""
    operator_question_ref: str = ""
    schema_version: int = PACKET_ABSORPTION_SCHEMA_VERSION
    contract_id: str = "PacketSemanticActionItem"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["next_slice_refs"] = list(self.next_slice_refs)
        return payload


@dataclass(frozen=True, slots=True)
class PacketSemanticIngestionReceipt:
    """Proof that a packet body was parsed into typed action items."""

    receipt_id: str
    packet_id: str
    body_sha256: str
    ingested_by_actor: str
    ingested_by_role: str
    ingested_by_session_id: str
    ingested_at_utc: str
    action_items: tuple[str, ...] = ()
    action_item_rows: tuple[PacketSemanticActionItem, ...] = ()
    resulting_decision: str = ""
    decision_rationale: str = ""
    schema_version: int = PACKET_ABSORPTION_SCHEMA_VERSION
    contract_id: str = PACKET_SEMANTIC_INGESTION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["action_items"] = list(self.action_items)
        payload["action_item_rows"] = [
            item.to_dict() for item in self.action_item_rows
        ]
        return payload


@dataclass(frozen=True, slots=True)
class PacketAbsorptionViolation:
    packet_id: str
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PacketAbsorptionRequiredReport:
    ok: bool
    actionable_packet_count: int
    absorption_receipt_count: int
    semantic_ingestion_receipt_count: int
    body_observed_without_ingestion_count: int
    violation_count: int
    violations: tuple[dict[str, str], ...] = ()
    schema_version: int = PACKET_ABSORPTION_SCHEMA_VERSION
    contract_id: str = PACKET_ABSORPTION_GUARD_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_packet_absorption_receipt(
    *,
    packet_id: str,
    body_sha256: str,
    absorbed_by_actor: str,
    absorbed_by_role: str,
    absorbed_by_session_id: str,
    absorbed_at_utc: str,
    action_item_dispositions: Sequence[str] = (),
    resulting_decision: str = "",
    decision_rationale: str = "",
    defer_reason: str = "",
    blocked_reason: str = "",
    next_slice_refs: Sequence[str] = (),
    superseded_packet_id: str = "",
    evidence_refs: Sequence[str] = (),
) -> PacketAbsorptionReceipt:
    dispositions = _unique_strings(action_item_dispositions)
    next_slices = _unique_strings(next_slice_refs)
    evidence = _unique_strings(evidence_refs)
    fingerprint_source = "\x00".join(
        (
            coerce_string(packet_id),
            coerce_string(body_sha256),
            coerce_string(absorbed_by_actor),
            coerce_string(absorbed_by_role),
            coerce_string(absorbed_by_session_id),
            "\x1f".join(dispositions),
            coerce_string(resulting_decision),
            coerce_string(decision_rationale),
            coerce_string(defer_reason),
            coerce_string(blocked_reason),
            "\x1f".join(next_slices),
            coerce_string(superseded_packet_id),
            "\x1f".join(evidence),
        )
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    return PacketAbsorptionReceipt(
        receipt_id=f"packet_absorption:{coerce_string(packet_id)}:{fingerprint}",
        packet_id=coerce_string(packet_id),
        body_sha256=coerce_string(body_sha256),
        absorbed_by_actor=coerce_string(absorbed_by_actor),
        absorbed_by_role=coerce_string(absorbed_by_role),
        absorbed_by_session_id=coerce_string(absorbed_by_session_id),
        absorbed_at_utc=coerce_string(absorbed_at_utc),
        action_item_dispositions=dispositions,
        resulting_decision=coerce_string(resulting_decision),
        decision_rationale=coerce_string(decision_rationale),
        defer_reason=coerce_string(defer_reason),
        blocked_reason=coerce_string(blocked_reason),
        next_slice_refs=next_slices,
        superseded_packet_id=coerce_string(superseded_packet_id),
        evidence_refs=evidence,
    )


def build_packet_semantic_ingestion_receipt(
    *,
    packet_id: str,
    body_sha256: str,
    ingested_by_actor: str,
    ingested_by_role: str,
    ingested_by_session_id: str,
    ingested_at_utc: str,
    action_items: Sequence[str] = (),
    action_item_rows: Sequence[Mapping[str, object] | PacketSemanticActionItem] = (),
    resulting_decision: str = "",
    decision_rationale: str = "",
) -> PacketSemanticIngestionReceipt:
    action_item_tuple = _unique_strings(action_items)
    structured_rows = _coerce_semantic_action_item_rows(action_item_rows)
    row_fingerprint = json.dumps(
        [row.to_dict() for row in structured_rows],
        sort_keys=True,
        separators=(",", ":"),
    )
    fingerprint_source = "\x00".join(
        (
            coerce_string(packet_id),
            coerce_string(body_sha256),
            coerce_string(ingested_by_actor),
            coerce_string(ingested_by_role),
            coerce_string(ingested_by_session_id),
            "\x1f".join(action_item_tuple),
            row_fingerprint,
            coerce_string(resulting_decision),
            coerce_string(decision_rationale),
        )
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    return PacketSemanticIngestionReceipt(
        receipt_id=f"packet_semantic_ingestion:{coerce_string(packet_id)}:{fingerprint}",
        packet_id=coerce_string(packet_id),
        body_sha256=coerce_string(body_sha256),
        ingested_by_actor=coerce_string(ingested_by_actor),
        ingested_by_role=coerce_string(ingested_by_role),
        ingested_by_session_id=coerce_string(ingested_by_session_id),
        ingested_at_utc=coerce_string(ingested_at_utc),
        action_items=action_item_tuple,
        action_item_rows=structured_rows,
        resulting_decision=coerce_string(resulting_decision),
        decision_rationale=coerce_string(decision_rationale),
    )


def packet_absorption_receipt_from_mapping(
    payload: Mapping[str, object],
) -> PacketAbsorptionReceipt:
    return PacketAbsorptionReceipt(
        receipt_id=coerce_string(payload.get("receipt_id")),
        packet_id=coerce_string(payload.get("packet_id")),
        body_sha256=coerce_string(payload.get("body_sha256")),
        absorbed_by_actor=coerce_string(payload.get("absorbed_by_actor")),
        absorbed_by_role=coerce_string(payload.get("absorbed_by_role")),
        absorbed_by_session_id=coerce_string(payload.get("absorbed_by_session_id")),
        absorbed_at_utc=coerce_string(payload.get("absorbed_at_utc")),
        action_item_dispositions=coerce_string_items(
            payload.get("action_item_dispositions")
        ),
        resulting_decision=coerce_string(payload.get("resulting_decision")),
        decision_rationale=coerce_string(payload.get("decision_rationale")),
        defer_reason=coerce_string(payload.get("defer_reason")),
        blocked_reason=coerce_string(payload.get("blocked_reason")),
        next_slice_refs=coerce_string_items(payload.get("next_slice_refs")),
        superseded_packet_id=coerce_string(payload.get("superseded_packet_id")),
        evidence_refs=coerce_string_items(payload.get("evidence_refs")),
        schema_version=(
            coerce_int(payload.get("schema_version"))
            or PACKET_ABSORPTION_SCHEMA_VERSION
        ),
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or PACKET_ABSORPTION_RECEIPT_CONTRACT_ID
        ),
    )


def packet_semantic_ingestion_receipt_from_mapping(
    payload: Mapping[str, object],
) -> PacketSemanticIngestionReceipt:
    return PacketSemanticIngestionReceipt(
        receipt_id=coerce_string(payload.get("receipt_id")),
        packet_id=coerce_string(payload.get("packet_id")),
        body_sha256=coerce_string(payload.get("body_sha256")),
        ingested_by_actor=coerce_string(payload.get("ingested_by_actor")),
        ingested_by_role=coerce_string(payload.get("ingested_by_role")),
        ingested_by_session_id=coerce_string(payload.get("ingested_by_session_id")),
        ingested_at_utc=coerce_string(payload.get("ingested_at_utc")),
        action_items=coerce_string_items(payload.get("action_items")),
        action_item_rows=_coerce_semantic_action_item_rows(
            payload.get("action_item_rows")
            or payload.get("structured_action_items")
        ),
        resulting_decision=coerce_string(payload.get("resulting_decision")),
        decision_rationale=coerce_string(payload.get("decision_rationale")),
        schema_version=(
            coerce_int(payload.get("schema_version"))
            or PACKET_ABSORPTION_SCHEMA_VERSION
        ),
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or PACKET_SEMANTIC_INGESTION_RECEIPT_CONTRACT_ID
        ),
    )


def evaluate_packet_absorption_required(
    payload: object,
    *,
    allow_empty: bool = False,
    observation_without_ingestion_limit: int | None = 1,
) -> PacketAbsorptionRequiredReport:
    packets: list[Mapping[str, object]] = []
    receipts: list[Mapping[str, object]] = []
    semantic_ingestion_receipts: list[Mapping[str, object]] = []
    _collect_packets_and_receipts(
        payload,
        packets,
        receipts,
        semantic_ingestion_receipts,
    )
    receipts_by_packet_id = _receipts_by_packet_id(receipts)
    ingestion_by_packet_id = _receipts_by_packet_id(semantic_ingestion_receipts)
    actionable_count = 0
    body_observed_without_ingestion: list[str] = []
    violations: list[PacketAbsorptionViolation] = []
    if not packets and not allow_empty:
        violations.append(
            PacketAbsorptionViolation(
                packet_id="",
                reason="no_packet_absorption_input",
                detail="No packet payload was supplied or loaded.",
            )
        )
    for packet in packets:
        if not _actionable_packet(packet):
            continue
        actionable_count += 1
        packet_id = coerce_string(packet.get("packet_id"))
        packet_receipts = receipts_by_packet_id.get(packet_id, ())
        semantic_receipts = ingestion_by_packet_id.get(packet_id, ())
        violations.extend(
            _semantic_ingestion_receipt_violations(packet, semantic_receipts)
        )
        if _packet_body_observed(packet) and not packet_semantically_ingested(
            packet,
            semantic_ingestion_receipts=semantic_receipts,
            absorption_receipts=packet_receipts,
        ):
            body_observed_without_ingestion.append(packet_id)
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="packet_body_observed_without_semantic_ingestion",
                )
            )
        receipt_violations = _receipt_violations(packet, packet_receipts)
        if not receipt_violations and _absorbed(
            packet,
            absorption_receipts=packet_receipts,
        ):
            continue
        violations.extend(receipt_violations)
        if _packet_status(packet) == "acked":
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="ack_without_absorption_disposition",
                )
            )
    if packets and actionable_count == 0 and not allow_empty:
        violations.append(
            PacketAbsorptionViolation(
                packet_id="",
                reason="no_actionable_packet_source",
                detail="No actionable packet payload was supplied.",
            )
        )
    if (
        observation_without_ingestion_limit is not None
        and len(body_observed_without_ingestion) > observation_without_ingestion_limit
    ):
        violations.append(
            PacketAbsorptionViolation(
                packet_id="",
                reason="packet_observation_without_semantic_ingestion",
                detail=(
                    f"count={len(body_observed_without_ingestion)};"
                    f"limit={observation_without_ingestion_limit};"
                    f"packets={','.join(body_observed_without_ingestion)}"
                ),
            )
        )
    violation_payloads = tuple(violation.to_dict() for violation in violations)
    return PacketAbsorptionRequiredReport(
        ok=not violation_payloads,
        actionable_packet_count=actionable_count,
        absorption_receipt_count=len(receipts),
        semantic_ingestion_receipt_count=len(semantic_ingestion_receipts),
        body_observed_without_ingestion_count=len(body_observed_without_ingestion),
        violation_count=len(violation_payloads),
        violations=violation_payloads,
    )


def packet_absorbed(
    packet: Mapping[str, object],
    *,
    absorption_receipts: Sequence[Mapping[str, object]] = (),
) -> bool:
    packet_id = coerce_string(packet.get("packet_id"))
    receipts = tuple(
        receipt for receipt in absorption_receipts if isinstance(receipt, Mapping)
    )
    return bool(packet_id) and not _receipt_violations(packet, receipts) and _absorbed(
        packet,
        absorption_receipts=receipts,
    )


def packet_semantically_ingested(
    packet: Mapping[str, object],
    *,
    semantic_ingestion_receipts: Sequence[Mapping[str, object]] = (),
    absorption_receipts: Sequence[Mapping[str, object]] = (),
) -> bool:
    packet_id = coerce_string(packet.get("packet_id"))
    semantic_receipts = tuple(
        receipt
        for receipt in semantic_ingestion_receipts
        if isinstance(receipt, Mapping)
    )
    inline_receipts = _inline_semantic_ingestion_receipts(packet)
    semantic_receipts = (*semantic_receipts, *inline_receipts)
    absorption_rows = tuple(
        receipt for receipt in absorption_receipts if isinstance(receipt, Mapping)
    )
    if (
        packet_id
        and not _semantic_ingestion_receipt_violations(packet, semantic_receipts)
        and any(
            coerce_string(receipt.get("packet_id")) == packet_id
            for receipt in semantic_receipts
        )
    ):
        return True
    return packet_absorbed(packet, absorption_receipts=absorption_rows)


def packet_semantically_ingested_by(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str = "",
    session: str = "",
    semantic_ingestion_receipts: Sequence[Mapping[str, object]] = (),
    absorption_receipts: Sequence[Mapping[str, object]] = (),
) -> bool:
    """Return whether a specific actor/role/session semantically ingested a packet."""
    actor_id = coerce_string(actor)
    role_id = coerce_string(role)
    session_id = coerce_string(session)
    if not actor_id:
        return False
    receipts = _inline_semantic_ingestion_receipts(packet)
    receipts = (
        *tuple(row for row in semantic_ingestion_receipts if isinstance(row, Mapping)),
        *receipts,
    )
    scoped_receipts = tuple(
        receipt
        for receipt in receipts
        if coerce_string(receipt.get("ingested_by_actor")) == actor_id
        and (not role_id or coerce_string(receipt.get("ingested_by_role")) == role_id)
        and (
            not session_id
            or coerce_string(receipt.get("ingested_by_session_id")) == session_id
        )
    )
    return packet_semantically_ingested(
        packet,
        semantic_ingestion_receipts=scoped_receipts,
        absorption_receipts=absorption_receipts,
    )


def semantic_ingestion_missing_for_packet(
    packet: Mapping[str, object],
    *,
    semantic_ingestion_receipts: Sequence[Mapping[str, object]] = (),
    absorption_receipts: Sequence[Mapping[str, object]] = (),
) -> bool:
    """Return whether an actionable observed packet still needs semantic ingestion."""
    if not _actionable_packet(packet):
        return False
    if not _packet_body_observed(packet):
        return False
    return not packet_semantically_ingested(
        packet,
        semantic_ingestion_receipts=semantic_ingestion_receipts,
        absorption_receipts=absorption_receipts,
    )


def _collect_packets_and_receipts(
    payload: object,
    packets: list[Mapping[str, object]],
    receipts: list[Mapping[str, object]],
    semantic_ingestion_receipts: list[Mapping[str, object]],
) -> None:
    if isinstance(payload, Mapping):
        contract_id = coerce_string(payload.get("contract_id"))
        if contract_id == PACKET_ABSORPTION_RECEIPT_CONTRACT_ID:
            receipts.append(payload)
        elif contract_id == PACKET_SEMANTIC_INGESTION_RECEIPT_CONTRACT_ID:
            semantic_ingestion_receipts.append(payload)
        elif "packet_id" in payload and "kind" in payload and "status" in payload:
            packets.append(payload)
        for key in (
            "packets",
            "receipts",
            "packet_absorption_receipts",
            "semantic_ingestion_receipts",
            "packet_semantic_ingestion_receipts",
        ):
            value = payload.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                for item in value:
                    _collect_packets_and_receipts(
                        item,
                        packets,
                        receipts,
                        semantic_ingestion_receipts,
                    )
        inline_ingestion = payload.get("semantic_ingestion_receipt")
        if isinstance(inline_ingestion, Mapping):
            _collect_packets_and_receipts(
                inline_ingestion,
                packets,
                receipts,
                semantic_ingestion_receipts,
            )
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        for item in payload:
            _collect_packets_and_receipts(
                item,
                packets,
                receipts,
                semantic_ingestion_receipts,
            )


def _actionable_packet(packet: Mapping[str, object]) -> bool:
    return coerce_string(packet.get("kind")).lower() in ACTIONABLE_PACKET_KINDS


def _absorbed(
    packet: Mapping[str, object],
    *,
    absorption_receipts: Sequence[Mapping[str, object]],
) -> bool:
    packet_id = coerce_string(packet.get("packet_id"))
    if any(coerce_string(receipt.get("packet_id")) == packet_id for receipt in absorption_receipts):
        return True
    receipt = packet.get("absorption_receipt")
    if (
        isinstance(receipt, Mapping)
        and coerce_string(receipt.get("packet_id")) == packet_id
        and not _receipt_violations(packet, (receipt,))
    ):
        return True
    return False


def _receipts_by_packet_id(
    receipts: Sequence[Mapping[str, object]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for receipt in receipts:
        packet_id = coerce_string(receipt.get("packet_id"))
        if not packet_id:
            continue
        grouped.setdefault(packet_id, []).append(receipt)
    return {packet_id: tuple(items) for packet_id, items in grouped.items()}


def _semantic_ingestion_receipt_violations(
    packet: Mapping[str, object],
    receipts: Sequence[Mapping[str, object]],
) -> list[PacketAbsorptionViolation]:
    packet_id = coerce_string(packet.get("packet_id"))
    violations: list[PacketAbsorptionViolation] = []
    for receipt in receipts:
        missing = [
            field
            for field in (
                "packet_id",
                "body_sha256",
                "ingested_by_actor",
                "ingested_by_role",
                "ingested_by_session_id",
                "ingested_at_utc",
                "resulting_decision",
                "decision_rationale",
            )
            if not coerce_string(receipt.get(field))
        ]
        rows = _semantic_action_item_row_dicts(receipt)
        if not rows:
            missing.append("action_item_rows")
        if missing:
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="packet_semantic_ingestion_receipt_incomplete",
                    detail=",".join(missing),
                )
            )
            continue
        row_missing = _semantic_action_item_rows_missing_fields(rows)
        if row_missing:
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="packet_semantic_ingestion_receipt_incomplete",
                    detail=",".join(row_missing),
                )
            )
            continue
        body_digest = (
            coerce_string(packet.get("body_sha256"))
            or coerce_string(packet.get("body_digest"))
        )
        if body_digest and body_digest != coerce_string(receipt.get("body_sha256")):
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="packet_semantic_ingestion_body_digest_mismatch",
                )
            )
    return violations


def _inline_semantic_ingestion_receipts(
    packet: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    for key in (
        "semantic_ingestion_receipt",
        "packet_semantic_ingestion_receipt",
    ):
        value = packet.get(key)
        if isinstance(value, Mapping):
            rows.append(value)
    for key in ("semantic_ingestion_events", "packet_semantic_ingestion_events"):
        value = packet.get(key)
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            continue
        for item in value:
            if not isinstance(item, Mapping):
                continue
            receipt = item.get("packet_semantic_ingestion_receipt")
            if isinstance(receipt, Mapping):
                rows.append(receipt)
            elif coerce_string(item.get("contract_id")) == (
                PACKET_SEMANTIC_INGESTION_RECEIPT_CONTRACT_ID
            ):
                rows.append(item)
    return tuple(rows)


def _coerce_semantic_action_item_rows(
    value: object,
) -> tuple[PacketSemanticActionItem, ...]:
    if isinstance(value, PacketSemanticActionItem):
        return (value,)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    rows: list[PacketSemanticActionItem] = []
    for item in value:
        if isinstance(item, PacketSemanticActionItem):
            rows.append(item)
            continue
        if not isinstance(item, Mapping):
            continue
        rows.append(
            PacketSemanticActionItem(
                action_item_id=coerce_string(item.get("action_item_id")),
                kind=coerce_string(item.get("kind")),
                disposition=coerce_string(item.get("disposition")),
                target_ref=coerce_string(item.get("target_ref")),
                slice_ref=coerce_string(item.get("slice_ref")),
                packet_ref=coerce_string(item.get("packet_ref")),
                reason=coerce_string(item.get("reason")),
                evidence_refs=coerce_string_items(item.get("evidence_refs")),
                next_slice_refs=coerce_string_items(item.get("next_slice_refs")),
                blocked_reason=coerce_string(item.get("blocked_reason")),
                superseded_packet_id=coerce_string(item.get("superseded_packet_id")),
                operator_question_ref=coerce_string(item.get("operator_question_ref")),
                schema_version=(
                    coerce_int(item.get("schema_version"))
                    or PACKET_ABSORPTION_SCHEMA_VERSION
                ),
                contract_id=(
                    coerce_string(item.get("contract_id"))
                    or "PacketSemanticActionItem"
                ),
            )
        )
    return tuple(rows)


def _semantic_action_item_row_dicts(
    receipt: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    rows = _coerce_semantic_action_item_rows(
        receipt.get("action_item_rows")
        or receipt.get("structured_action_items")
    )
    return tuple(row.to_dict() for row in rows)


def _semantic_action_item_rows_missing_fields(
    rows: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    missing: list[str] = []
    for index, row in enumerate(rows, start=1):
        prefix = f"action_item_rows[{index}]"
        if not coerce_string(row.get("action_item_id")):
            missing.append(f"{prefix}:action_item_id")
        if not coerce_string(row.get("kind")):
            missing.append(f"{prefix}:kind")
        disposition = _disposition_status(coerce_string(row.get("disposition")))
        if not disposition:
            missing.append(f"{prefix}:disposition")
        elif disposition not in PACKET_SEMANTIC_INGESTION_ALLOWED_DISPOSITIONS:
            missing.append(f"{prefix}:invalid_disposition")
        if not any(
            coerce_string(row.get(field))
            for field in ("target_ref", "slice_ref", "packet_ref")
        ):
            missing.append(f"{prefix}:target_ref_or_slice_ref_or_packet_ref")
        if not coerce_string(row.get("reason")):
            missing.append(f"{prefix}:reason")
        if not coerce_string_items(row.get("evidence_refs")):
            missing.append(f"{prefix}:evidence_refs")
        if disposition == "deferred" and not coerce_string_items(
            row.get("next_slice_refs")
        ):
            missing.append(f"{prefix}:deferred:next_slice_refs")
        if disposition in {
            "blocked",
            "rejected",
            "needs_operator_decision",
        } and not coerce_string(row.get("blocked_reason")):
            missing.append(f"{prefix}:{disposition}:blocked_reason")
        if disposition == "needs_operator_decision" and not (
            coerce_string(row.get("operator_question_ref"))
            or coerce_string_items(row.get("next_slice_refs"))
        ):
            missing.append(
                f"{prefix}:needs_operator_decision:operator_question_ref_or_next_slice_refs"
            )
        if disposition == "superseded" and not coerce_string(
            row.get("superseded_packet_id")
        ):
            missing.append(f"{prefix}:superseded:superseded_packet_id")
    return tuple(missing)


def _receipt_violations(
    packet: Mapping[str, object],
    receipts: Sequence[Mapping[str, object]],
) -> list[PacketAbsorptionViolation]:
    packet_id = coerce_string(packet.get("packet_id"))
    violations: list[PacketAbsorptionViolation] = []
    for receipt in receipts:
        missing = [
            field
            for field in (
                "packet_id",
                "body_sha256",
                "absorbed_by_actor",
                "absorbed_by_role",
                "absorbed_by_session_id",
                "absorbed_at_utc",
                "resulting_decision",
                "decision_rationale",
            )
            if not coerce_string(receipt.get(field))
        ]
        dispositions = coerce_string_items(receipt.get("action_item_dispositions"))
        if not dispositions:
            missing.append("action_item_dispositions")
        if missing:
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="packet_absorption_receipt_incomplete",
                    detail=",".join(missing),
                )
            )
            continue
        disposition_missing = _disposition_specific_missing_fields(
            receipt,
            dispositions=dispositions,
        )
        if disposition_missing:
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="packet_absorption_receipt_incomplete",
                    detail=",".join(disposition_missing),
                )
            )
            continue
        invalid_dispositions = tuple(
            disposition
            for disposition in dispositions
            if _disposition_status(disposition)
            not in PACKET_ABSORPTION_ALLOWED_DISPOSITIONS
        )
        if invalid_dispositions:
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="packet_absorption_invalid_disposition",
                    detail=",".join(invalid_dispositions),
                )
            )
            continue
        body_digest = (
            coerce_string(packet.get("body_sha256"))
            or coerce_string(packet.get("body_digest"))
        )
        if body_digest and body_digest != coerce_string(receipt.get("body_sha256")):
            violations.append(
                PacketAbsorptionViolation(
                    packet_id=packet_id,
                    reason="packet_absorption_body_digest_mismatch",
                )
            )
    return violations


def _packet_body_observed(packet: Mapping[str, object]) -> bool:
    return any(
        coerce_string(packet.get(field))
        for field in (
            "body_observed_at_utc",
            "body_observed_by",
            "body_observed_role",
            "body_observed_session_id",
            "body_observed_event_id",
        )
    )


def _disposition_specific_missing_fields(
    receipt: Mapping[str, object],
    *,
    dispositions: Sequence[str],
) -> tuple[str, ...]:
    missing: list[str] = []
    evidence_refs = coerce_string_items(receipt.get("evidence_refs"))
    next_slice_refs = coerce_string_items(receipt.get("next_slice_refs"))
    defer_reason = coerce_string(receipt.get("defer_reason"))
    blocked_reason = coerce_string(receipt.get("blocked_reason"))
    superseded_packet_id = coerce_string(receipt.get("superseded_packet_id"))
    for disposition in dispositions:
        status = _disposition_status(disposition)
        if status in {"accepted", "already_shipped"}:
            if not evidence_refs:
                missing.append(f"{status}:evidence_refs")
        elif status == "deferred":
            if not defer_reason:
                missing.append("deferred:defer_reason")
            if not next_slice_refs:
                missing.append("deferred:next_slice_refs")
        elif status == "rejected":
            if not blocked_reason:
                missing.append("rejected:blocked_reason")
        elif status == "needs_operator_decision":
            if not blocked_reason:
                missing.append("needs_operator_decision:blocked_reason")
            if not next_slice_refs:
                missing.append("needs_operator_decision:next_slice_refs")
        elif status == "superseded":
            if not superseded_packet_id:
                missing.append("superseded:superseded_packet_id")
    return tuple(missing)


def _packet_status(packet: Mapping[str, object]) -> str:
    return coerce_string(packet.get("status")).lower()


def _disposition_status(value: str) -> str:
    text = coerce_string(value).lower()
    if ":" in text:
        text = text.rsplit(":", 1)[1]
    return text.strip()


def _unique_strings(values: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text.strip() or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


__all__ = [
    "ACTIONABLE_PACKET_KINDS",
    "PACKET_ABSORPTION_ALLOWED_DISPOSITIONS",
    "PACKET_ABSORPTION_GUARD_CONTRACT_ID",
    "PACKET_ABSORPTION_RECEIPT_CONTRACT_ID",
    "PACKET_ABSORPTION_SCHEMA_VERSION",
    "PACKET_SEMANTIC_INGESTION_RECEIPT_CONTRACT_ID",
    "PACKET_SEMANTIC_INGESTION_ALLOWED_DISPOSITIONS",
    "PacketAbsorptionReceipt",
    "PacketAbsorptionRequiredReport",
    "PacketAbsorptionViolation",
    "PacketSemanticActionItem",
    "PacketSemanticIngestionReceipt",
    "build_packet_absorption_receipt",
    "build_packet_semantic_ingestion_receipt",
    "evaluate_packet_absorption_required",
    "packet_absorbed",
    "packet_absorption_receipt_from_mapping",
    "packet_semantic_ingestion_receipt_from_mapping",
    "packet_semantically_ingested",
    "packet_semantically_ingested_by",
    "semantic_ingestion_missing_for_packet",
]
