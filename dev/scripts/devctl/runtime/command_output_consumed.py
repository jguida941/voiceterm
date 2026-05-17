"""Guard helpers for semantic command-output consumption."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

from .control_decision_consistency import control_decision_violations
from .command_output_consumption_receipt import (
    COMMAND_OUTPUT_CONSUMPTION_RECEIPT_CONTRACT_ID,
)
from .command_output_receipt import COMMAND_OUTPUT_RECEIPT_CONTRACT_ID
from .value_coercion import coerce_bool, coerce_string, coerce_string_items

COMMAND_OUTPUT_CONSUMED_GUARD_CONTRACT_ID = "CommandOutputConsumedGuard"
COMMAND_OUTPUT_CONSUMED_SCHEMA_VERSION = 1

AUTHORITY_BEARING_COMMAND_NAMES = frozenset(
    {
        "agent-loop",
        "develop next",
        "develop-next",
        "session",
        "startup-context",
        "session-resume",
        "review-channel",
        "check-feature-has-proof-receipt",
        "check-publication-scope-integrity",
        "check-substrate-commits-have-applied-plan-row",
        "check-startup-authority-contract",
        "devctl push",
        "push",
        "raw-git",
    }
)

AGENT_LOOP_AUTHORITY_FIELDS = (
    "decision",
    "required_action",
    "reason_code",
    "may_mutate",
    "can_run_next_command",
    "operator_override.requested",
    "operator_override.active",
    "operator_override.state",
    "next_action",
    "next_command",
    "top_blocker",
    "pending_packet_count",
    "active_packet_id",
    "attention_packet_id",
    "body_open_required",
    "body_open_packet_id",
    "unopened_body_packet_ids",
    "pivot_required",
)


@dataclass(frozen=True, slots=True)
class CommandOutputConsumedViolation:
    receipt_id: str
    command_name: str
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CommandOutputConsumedReport:
    ok: bool
    command_output_receipt_count: int
    consumption_receipt_count: int
    authority_bearing_receipt_count: int
    violation_count: int
    violations: tuple[dict[str, str], ...] = ()
    schema_version: int = COMMAND_OUTPUT_CONSUMED_SCHEMA_VERSION
    contract_id: str = COMMAND_OUTPUT_CONSUMED_GUARD_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_command_output_consumed(
    payload: object,
    *,
    allow_empty: bool = False,
) -> CommandOutputConsumedReport:
    """Fail when authority-bearing command output lacks consumption proof."""

    command_receipts: list[Mapping[str, object]] = []
    consumption_receipts: list[Mapping[str, object]] = []
    _collect_receipts(payload, command_receipts, consumption_receipts)
    consumption_by_receipt_id = _consumption_by_receipt_id(consumption_receipts)
    violations: list[CommandOutputConsumedViolation] = []
    if not command_receipts and not allow_empty:
        violations.append(
            CommandOutputConsumedViolation(
                receipt_id="",
                command_name="",
                reason="no_authority_output_input",
                detail="No CommandOutputReceipt payloads were supplied or loaded.",
            )
        )
    authority_count = 0
    for receipt in command_receipts:
        receipt_id = coerce_string(receipt.get("receipt_id"))
        command_name = coerce_string(receipt.get("command_name"))
        if not _authority_bearing_command(command_name):
            continue
        authority_count += 1
        if coerce_bool(receipt.get("output_assertions_satisfied")) is False:
            violations.append(
                CommandOutputConsumedViolation(
                    receipt_id=receipt_id,
                    command_name=command_name,
                    reason="authority_output_assertions_failed",
                )
            )
        if _tail_only_without_full_artifact(receipt):
            violations.append(
                CommandOutputConsumedViolation(
                    receipt_id=receipt_id,
                    command_name=command_name,
                    reason="authority_output_tail_without_full_artifact",
                )
            )
        consumption = consumption_by_receipt_id.get(receipt_id)
        if consumption is None:
            violations.append(
                CommandOutputConsumedViolation(
                    receipt_id=receipt_id,
                    command_name=command_name,
                    reason="authority_output_unconsumed",
                )
            )
            continue
        violations.extend(
            _content_violations_for_consumption(
                receipt=receipt,
                consumption=consumption,
            )
        )
    if command_receipts and authority_count == 0 and not allow_empty:
        violations.append(
            CommandOutputConsumedViolation(
                receipt_id="",
                command_name="",
                reason="no_authority_output_input",
                detail="No authority-bearing CommandOutputReceipt payloads were supplied.",
            )
        )
    violation_payloads = tuple(violation.to_dict() for violation in violations)
    return CommandOutputConsumedReport(
        ok=not violation_payloads,
        command_output_receipt_count=len(command_receipts),
        consumption_receipt_count=len(consumption_receipts),
        authority_bearing_receipt_count=authority_count,
        violation_count=len(violation_payloads),
        violations=violation_payloads,
    )


def _collect_receipts(
    payload: object,
    command_receipts: list[Mapping[str, object]],
    consumption_receipts: list[Mapping[str, object]],
) -> None:
    if isinstance(payload, Mapping):
        contract_id = coerce_string(payload.get("contract_id"))
        if contract_id == COMMAND_OUTPUT_RECEIPT_CONTRACT_ID:
            command_receipts.append(payload)
        elif contract_id == COMMAND_OUTPUT_CONSUMPTION_RECEIPT_CONTRACT_ID:
            consumption_receipts.append(payload)
        for value in payload.values():
            _collect_receipts(value, command_receipts, consumption_receipts)
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes)):
        for item in payload:
            _collect_receipts(item, command_receipts, consumption_receipts)


def _consumption_by_receipt_id(
    receipts: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for item in receipts:
        receipt_id = coerce_string(
            item.get("command_output_receipt_id") or item.get("source_receipt_id")
        )
        if receipt_id:
            result[receipt_id] = item
    return result


def _content_violations_for_consumption(
    *,
    receipt: Mapping[str, object],
    consumption: Mapping[str, object],
) -> list[CommandOutputConsumedViolation]:
    command_name = coerce_string(receipt.get("command_name"))
    if _normalized_command_name(command_name) != "agent-loop":
        return []
    decision = _agent_loop_decision_from_receipt(receipt)
    if not decision:
        return []
    receipt_id = coerce_string(receipt.get("receipt_id"))
    full_artifact = _full_output_artifact_ref(receipt)
    if full_artifact:
        consumed_output_hash = coerce_string(consumption.get("output_sha256"))
        artifact_hash = coerce_string(full_artifact.get("sha256"))
        if consumed_output_hash != artifact_hash:
            return [
                CommandOutputConsumedViolation(
                    receipt_id=receipt_id,
                    command_name=command_name,
                    reason="consumption_output_sha_mismatch",
                    detail="full_output_artifact_ref.sha256",
                )
            ]
    extracted_fields = set(
        coerce_string_items(consumption.get("extracted_authority_fields"))
    )
    extracted_values = (
        consumption.get("extracted_authority_values")
        if isinstance(consumption.get("extracted_authority_values"), Mapping)
        else {}
    )
    violations: list[CommandOutputConsumedViolation] = []
    for field in AGENT_LOOP_AUTHORITY_FIELDS:
        if not _has_authority_field(decision, field):
            continue
        if field not in extracted_fields:
            violations.append(
                CommandOutputConsumedViolation(
                    receipt_id=receipt_id,
                    command_name=command_name,
                    reason="consumption_missing_authority_field",
                    detail=field,
                )
            )
            continue
        source_value = _authority_field_value(decision, field)
        if field not in extracted_values:
            violations.append(
                CommandOutputConsumedViolation(
                    receipt_id=receipt_id,
                    command_name=command_name,
                    reason="consumption_missing_authority_value",
                    detail=field,
                )
            )
            continue
        if not _authority_value_matches(
            source_value=source_value,
            consumed_value=extracted_values.get(field),
        ):
            violations.append(
                CommandOutputConsumedViolation(
                    receipt_id=receipt_id,
                    command_name=command_name,
                    reason="consumption_authority_value_mismatch",
                    detail=field,
                )
            )
    contradiction_flags = set(
        coerce_string_items(consumption.get("contradiction_flags"))
    )
    for violation in control_decision_violations(decision, source=receipt_id):
        if violation.reason not in contradiction_flags:
            violations.append(
                CommandOutputConsumedViolation(
                    receipt_id=receipt_id,
                    command_name=command_name,
                    reason="consumption_missing_contradiction_flag",
                    detail=violation.reason,
                )
            )
    return violations


def _agent_loop_decision_from_receipt(
    receipt: Mapping[str, object],
) -> Mapping[str, object]:
    excerpt = coerce_string(receipt.get("output_excerpt"))
    if not excerpt:
        return {}
    try:
        payload = json.loads(excerpt)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, Mapping):
        return {}
    decision = payload.get("agent_loop_decision")
    if isinstance(decision, Mapping):
        return _with_packet_attention(payload, decision)
    if coerce_string(payload.get("contract_id")) == "AgentLoopDecision":
        return payload
    if any(field in payload for field in ("decision", "may_mutate", "next_action")):
        return _with_packet_attention(payload, payload)
    return {}


def _has_authority_field(decision: Mapping[str, object], field: str) -> bool:
    return _authority_field_value(decision, field, missing=...) is not ...


def _authority_field_value(
    decision: Mapping[str, object],
    field: str,
    *,
    missing: object = "",
) -> object:
    current: object = decision
    for part in field.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return missing
        current = current[part]
    return current


def _with_packet_attention(
    payload: Mapping[str, object],
    decision: Mapping[str, object],
) -> Mapping[str, object]:
    result = dict(decision)
    packet_attention = payload.get("packet_attention")
    if isinstance(packet_attention, Mapping):
        merge_map = {
            "body_open_required": "body_open_required",
            "body_open_packet_id": "body_open_packet_id",
            "attention_packet_id": "latest_attention_packet_id",
            "active_packet_id": "active_packet_id",
            "pending_packet_count": "pending_packet_count",
            "unopened_body_packet_ids": "unopened_body_packet_ids",
            "pivot_required": "pivot_required",
        }
        for target_key, source_key in merge_map.items():
            if source_key in packet_attention:
                result[target_key] = packet_attention[source_key]
        if "attention_packet_id" not in result and "attention_packet_id" in packet_attention:
            result["attention_packet_id"] = packet_attention["attention_packet_id"]
    return result


def _authority_value_matches(
    *,
    source_value: object,
    consumed_value: object,
) -> bool:
    if isinstance(source_value, bool):
        return coerce_bool(consumed_value) is source_value
    if isinstance(source_value, int) and not isinstance(source_value, bool):
        try:
            return int(consumed_value) == source_value
        except (TypeError, ValueError):
            return False
    return coerce_string(source_value) == coerce_string(consumed_value)


def _authority_bearing_command(command_name: str) -> bool:
    normalized = _normalized_command_name(command_name)
    if normalized in AUTHORITY_BEARING_COMMAND_NAMES:
        return True
    return normalized.startswith(
        (
            "review-channel ",
            "devctl push",
            "check-feature-has-proof-receipt",
            "check-publication-scope-integrity",
            "check-substrate-commits-have-applied-plan-row",
            "check-startup-authority-contract",
        )
    )


def _tail_only_without_full_artifact(receipt: Mapping[str, object]) -> bool:
    if coerce_string(receipt.get("capture_scope")).lower() != "tail":
        return False
    return not bool(_full_output_artifact_ref(receipt))


def _full_output_artifact_ref(
    receipt: Mapping[str, object],
) -> Mapping[str, object]:
    artifact = receipt.get("full_output_artifact_ref")
    if not isinstance(artifact, Mapping):
        return {}
    if coerce_string(artifact.get("contract_id")) != "CommandOutputFullArtifact":
        return {}
    if coerce_string(artifact.get("capture_scope")).lower() != "full":
        return {}
    for field in ("path", "sha256", "byte_count"):
        if not coerce_string(artifact.get(field)):
            return {}
    artifact_receipt_id = coerce_string(artifact.get("command_output_receipt_id"))
    if artifact_receipt_id and artifact_receipt_id != coerce_string(receipt.get("receipt_id")):
        return {}
    return artifact


def _normalized_command_name(command_name: str) -> str:
    return command_name.strip().lower().replace("_", "-")


__all__ = [
    "AUTHORITY_BEARING_COMMAND_NAMES",
    "AGENT_LOOP_AUTHORITY_FIELDS",
    "COMMAND_OUTPUT_CONSUMED_GUARD_CONTRACT_ID",
    "COMMAND_OUTPUT_CONSUMED_SCHEMA_VERSION",
    "CommandOutputConsumedReport",
    "CommandOutputConsumedViolation",
    "evaluate_command_output_consumed",
]
