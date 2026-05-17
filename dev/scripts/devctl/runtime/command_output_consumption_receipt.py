"""Typed receipts proving command output was semantically consumed."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field

from .value_coercion import coerce_int, coerce_string, coerce_string_items

COMMAND_OUTPUT_CONSUMPTION_RECEIPT_CONTRACT_ID = "CommandOutputConsumptionReceipt"
COMMAND_OUTPUT_CONSUMPTION_RECEIPT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class CommandOutputConsumptionReceipt:
    """Proof that authority-bearing command output was read and dispositioned."""

    receipt_id: str
    command_output_receipt_id: str
    command_name: str
    output_sha256: str
    consumed_by_actor: str
    consumed_by_role: str
    consumed_at_utc: str
    extracted_authority_fields: tuple[str, ...] = ()
    extracted_authority_values: Mapping[str, object] = field(default_factory=dict)
    extracted_blockers: tuple[str, ...] = ()
    extracted_permissions: tuple[str, ...] = ()
    extracted_next_actions: tuple[str, ...] = ()
    contradiction_flags: tuple[str, ...] = ()
    resulting_decision: str = ""
    decision_rationale: str = ""
    evidence_refs: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    schema_version: int = COMMAND_OUTPUT_CONSUMPTION_RECEIPT_SCHEMA_VERSION
    contract_id: str = COMMAND_OUTPUT_CONSUMPTION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["extracted_authority_fields"] = list(self.extracted_authority_fields)
        payload["extracted_authority_values"] = dict(self.extracted_authority_values)
        payload["extracted_blockers"] = list(self.extracted_blockers)
        payload["extracted_permissions"] = list(self.extracted_permissions)
        payload["extracted_next_actions"] = list(self.extracted_next_actions)
        payload["contradiction_flags"] = list(self.contradiction_flags)
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["artifact_refs"] = list(self.artifact_refs)
        return payload


def build_command_output_consumption_receipt(
    *,
    command_output_receipt_id: str,
    command_name: str,
    output_sha256: str,
    consumed_by_actor: str,
    consumed_by_role: str,
    consumed_at_utc: str,
    extracted_authority_fields: Sequence[str] = (),
    extracted_authority_values: Mapping[str, object] | None = None,
    extracted_blockers: Sequence[str] = (),
    extracted_permissions: Sequence[str] = (),
    extracted_next_actions: Sequence[str] = (),
    contradiction_flags: Sequence[str] = (),
    resulting_decision: str = "",
    decision_rationale: str = "",
    evidence_refs: Sequence[str] = (),
    artifact_refs: Sequence[str] = (),
) -> CommandOutputConsumptionReceipt:
    """Build a stable receipt over the semantic consumption decision."""

    authority_fields = _unique_strings(extracted_authority_fields)
    authority_values = _authority_value_mapping(extracted_authority_values or {})
    blockers = _unique_strings(extracted_blockers)
    permissions = _unique_strings(extracted_permissions)
    next_actions = _unique_strings(extracted_next_actions)
    contradictions = _unique_strings(contradiction_flags)
    evidence = _unique_strings(evidence_refs)
    artifacts = _unique_strings(artifact_refs)
    fingerprint_source = "\x00".join(
        (
            coerce_string(command_output_receipt_id),
            coerce_string(command_name),
            coerce_string(output_sha256),
            coerce_string(consumed_by_actor),
            coerce_string(consumed_by_role),
            "\x1f".join(authority_fields),
            json.dumps(authority_values, sort_keys=True, separators=(",", ":")),
            "\x1f".join(blockers),
            "\x1f".join(permissions),
            "\x1f".join(next_actions),
            "\x1f".join(contradictions),
            coerce_string(resulting_decision),
            coerce_string(decision_rationale),
            "\x1f".join(evidence),
            "\x1f".join(artifacts),
        )
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    return CommandOutputConsumptionReceipt(
        receipt_id=f"command_output_consumption:{coerce_string(command_name)}:{fingerprint}",
        command_output_receipt_id=coerce_string(command_output_receipt_id),
        command_name=coerce_string(command_name),
        output_sha256=coerce_string(output_sha256),
        consumed_by_actor=coerce_string(consumed_by_actor),
        consumed_by_role=coerce_string(consumed_by_role),
        consumed_at_utc=coerce_string(consumed_at_utc),
        extracted_authority_fields=authority_fields,
        extracted_authority_values=authority_values,
        extracted_blockers=blockers,
        extracted_permissions=permissions,
        extracted_next_actions=next_actions,
        contradiction_flags=contradictions,
        resulting_decision=coerce_string(resulting_decision),
        decision_rationale=coerce_string(decision_rationale),
        evidence_refs=evidence,
        artifact_refs=artifacts,
    )


def command_output_consumption_receipt_from_mapping(
    payload: Mapping[str, object],
) -> CommandOutputConsumptionReceipt:
    return CommandOutputConsumptionReceipt(
        receipt_id=coerce_string(payload.get("receipt_id")),
        command_output_receipt_id=coerce_string(
            payload.get("command_output_receipt_id") or payload.get("source_receipt_id")
        ),
        command_name=coerce_string(payload.get("command_name")),
        output_sha256=coerce_string(payload.get("output_sha256")),
        consumed_by_actor=coerce_string(payload.get("consumed_by_actor")),
        consumed_by_role=coerce_string(payload.get("consumed_by_role")),
        consumed_at_utc=coerce_string(payload.get("consumed_at_utc")),
        extracted_authority_fields=coerce_string_items(
            payload.get("extracted_authority_fields")
        ),
        extracted_authority_values=_authority_value_mapping(
            payload.get("extracted_authority_values")
            if isinstance(payload.get("extracted_authority_values"), Mapping)
            else {}
        ),
        extracted_blockers=coerce_string_items(payload.get("extracted_blockers")),
        extracted_permissions=coerce_string_items(
            payload.get("extracted_permissions")
        ),
        extracted_next_actions=coerce_string_items(
            payload.get("extracted_next_actions")
        ),
        contradiction_flags=coerce_string_items(payload.get("contradiction_flags")),
        resulting_decision=coerce_string(payload.get("resulting_decision")),
        decision_rationale=coerce_string(payload.get("decision_rationale")),
        evidence_refs=coerce_string_items(payload.get("evidence_refs")),
        artifact_refs=coerce_string_items(payload.get("artifact_refs")),
        schema_version=(
            coerce_int(payload.get("schema_version"))
            or COMMAND_OUTPUT_CONSUMPTION_RECEIPT_SCHEMA_VERSION
        ),
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or COMMAND_OUTPUT_CONSUMPTION_RECEIPT_CONTRACT_ID
        ),
    )


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


def _authority_value_mapping(values: Mapping[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values.items():
        text_key = coerce_string(key)
        if not text_key:
            continue
        result[text_key] = value
    return result


__all__ = [
    "COMMAND_OUTPUT_CONSUMPTION_RECEIPT_CONTRACT_ID",
    "COMMAND_OUTPUT_CONSUMPTION_RECEIPT_SCHEMA_VERSION",
    "CommandOutputConsumptionReceipt",
    "build_command_output_consumption_receipt",
    "command_output_consumption_receipt_from_mapping",
]
