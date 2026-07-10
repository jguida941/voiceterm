"""Apply-time PacketGuardAttestation validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ..runtime.collaboration_packet_kinds import (
    COLLABORATION_LIFECYCLE_PACKET_KINDS,
)
from ..runtime.value_coercion import coerce_mapping, coerce_string, coerce_string_items

PACKET_GUARD_ATTESTATION_CONTRACT_ID = "PacketGuardAttestation"
PACKET_GUARD_ATTESTATION_SCHEMA_VERSION = 1

_MINIMAL_ATTESTATION_KINDS = {
    "decision",
    "system_notice",
    "question",
    "instruction",
    "draft",
    "plan_gap_review",
    "plan_ready_gate",
} | COLLABORATION_LIFECYCLE_PACKET_KINDS


@dataclass(frozen=True, slots=True)
class PacketGuardAttestation:
    """Evidence attached to a packet_applied transition."""

    packet_id: str
    attestation_kind: str
    run_record_ids: tuple[str, ...] = ()
    action_result_ids: tuple[str, ...] = ()
    commit_sha: str = ""
    plan_revision_before: str = ""
    plan_revision_after: str = ""
    evidence_artifact_paths: tuple[str, ...] = ()
    attested_at_utc: str = ""
    attested_by: str = ""
    operator_signature: str = ""
    pipeline_generation: str = ""
    staged_snapshot_hash: str = ""
    mutation_op: str = ""
    schema_version: int = PACKET_GUARD_ATTESTATION_SCHEMA_VERSION
    contract_id: str = PACKET_GUARD_ATTESTATION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["run_record_ids"] = list(self.run_record_ids)
        payload["action_result_ids"] = list(self.action_result_ids)
        payload["evidence_artifact_paths"] = list(self.evidence_artifact_paths)
        return payload


def packet_guard_attestation_from_mapping(
    payload: Mapping[str, object],
) -> PacketGuardAttestation:
    evidence_paths = coerce_string_items(payload.get("evidence_artifact_paths"))
    return PacketGuardAttestation(
        packet_id=coerce_string(payload.get("packet_id")),
        attestation_kind=coerce_string(payload.get("attestation_kind")),
        run_record_ids=coerce_string_items(payload.get("run_record_ids")),
        action_result_ids=coerce_string_items(payload.get("action_result_ids")),
        commit_sha=coerce_string(payload.get("commit_sha")),
        plan_revision_before=coerce_string(payload.get("plan_revision_before")),
        plan_revision_after=coerce_string(payload.get("plan_revision_after")),
        evidence_artifact_paths=evidence_paths,
        attested_at_utc=coerce_string(payload.get("attested_at_utc")),
        attested_by=coerce_string(payload.get("attested_by")),
        operator_signature=coerce_string(payload.get("operator_signature")),
        pipeline_generation=coerce_string(payload.get("pipeline_generation")),
        staged_snapshot_hash=coerce_string(payload.get("staged_snapshot_hash")),
        mutation_op=coerce_string(payload.get("mutation_op")),
    )


def minimal_packet_guard_attestation(
    *,
    packet: Mapping[str, object],
    actor: str,
    timestamp_utc: str,
) -> PacketGuardAttestation:
    packet_id = _text(packet.get("packet_id"))
    attestation_kind = "carrier_timestamp_actor"
    return PacketGuardAttestation(
        packet_id=packet_id,
        attestation_kind=attestation_kind,
        attested_at_utc=timestamp_utc,
        attested_by=actor,
        operator_signature=actor,
    )


def validate_packet_apply_attestation(
    *,
    packet: Mapping[str, object],
    event: Mapping[str, object],
) -> PacketGuardAttestation:
    """Return the apply attestation or raise with missing evidence details."""
    event_type = _text(event.get("event_type"))
    if event_type != "packet_applied":
        raise ValueError("PacketGuardAttestation only applies to packet_applied events.")

    metadata = coerce_mapping(event.get("metadata"))
    attestation_payload = coerce_mapping(metadata.get("guard_attestation"))
    if not attestation_payload:
        kind = _text(packet.get("kind"))
        if kind in _MINIMAL_ATTESTATION_KINDS:
            return minimal_packet_guard_attestation(
                packet=packet,
                actor=_text(metadata.get("actor")) or _text(packet.get("to_agent")),
                timestamp_utc=_text(event.get("timestamp_utc")),
            )
        raise ValueError(
            f"Packet {packet.get('packet_id')} cannot be applied without "
            "PacketGuardAttestation."
        )

    attestation = packet_guard_attestation_from_mapping(attestation_payload)
    _validate_common(packet=packet, event=event, attestation=attestation)
    _validate_kind_requirements(packet=packet, attestation=attestation)
    return attestation


def _validate_common(
    *,
    packet: Mapping[str, object],
    event: Mapping[str, object],
    attestation: PacketGuardAttestation,
) -> None:
    packet_id = _text(packet.get("packet_id"))
    if attestation.packet_id != packet_id:
        raise ValueError(
            "PacketGuardAttestation packet_id does not match applied packet."
        )
    if not attestation.attested_at_utc:
        raise ValueError("PacketGuardAttestation requires attested_at_utc.")
    if not attestation.attested_by:
        raise ValueError("PacketGuardAttestation requires attested_by.")
    actor = _text(coerce_mapping(event.get("metadata")).get("actor"))
    if actor and attestation.attested_by != actor:
        raise ValueError(
            "PacketGuardAttestation attested_by must match transition actor."
        )


def _validate_kind_requirements(
    *,
    packet: Mapping[str, object],
    attestation: PacketGuardAttestation,
) -> None:
    kind = _text(packet.get("kind"))
    if kind == "action_request":
        _require_action_request_attestation(packet, attestation)
        return
    if kind == "commit_approval":
        _require_commit_approval_attestation(packet, attestation)
        return
    if kind == "plan_patch_review":
        _require_plan_patch_attestation(packet, attestation)
        return
    if kind == "finding":
        _require_finding_attestation(attestation)
        return
    if kind == "approval_request":
        _require_operator_signature(attestation)
        return
    if kind in _MINIMAL_ATTESTATION_KINDS:
        return
    raise ValueError(f"Unsupported PacketGuardAttestation packet kind: {kind}.")


def _require_action_request_attestation(
    packet: Mapping[str, object],
    attestation: PacketGuardAttestation,
) -> None:
    action = _text(packet.get("requested_action"))
    if action in {"commit", "push", "stage_commit_pipeline"}:
        _require_fields(
            attestation,
            "commit_sha",
            "run_record_ids",
            "action_result_ids",
            "evidence_artifact_paths",
        )
        return
    _require_fields(attestation, "action_result_ids")


def _require_commit_approval_attestation(
    packet: Mapping[str, object],
    attestation: PacketGuardAttestation,
) -> None:
    if attestation.pipeline_generation != _text(packet.get("pipeline_generation")):
        raise ValueError(
            "PacketGuardAttestation pipeline_generation must match packet."
        )
    if attestation.staged_snapshot_hash != _text(packet.get("staged_snapshot_hash")):
        raise ValueError(
            "PacketGuardAttestation staged_snapshot_hash must match packet."
        )
    _require_fields(attestation, "run_record_ids", "operator_signature")


def _require_plan_patch_attestation(
    packet: Mapping[str, object],
    attestation: PacketGuardAttestation,
) -> None:
    if attestation.mutation_op != _text(packet.get("mutation_op")):
        raise ValueError("PacketGuardAttestation mutation_op must match packet.")
    _require_fields(
        attestation,
        "plan_revision_before",
        "plan_revision_after",
        "mutation_op",
    )


def _require_finding_attestation(attestation: PacketGuardAttestation) -> None:
    _require_fields(attestation, "run_record_ids", "action_result_ids")


def _require_operator_signature(attestation: PacketGuardAttestation) -> None:
    _require_fields(attestation, "operator_signature")


def _require_fields(attestation: PacketGuardAttestation, *fields: str) -> None:
    missing: list[str] = []
    for field_name in fields:
        value = getattr(attestation, field_name)
        if isinstance(value, tuple) and not value:
            missing.append(field_name)
        elif isinstance(value, str) and not value:
            missing.append(field_name)
    if missing:
        raise ValueError(
            "PacketGuardAttestation missing required field(s): "
            + ", ".join(missing)
            + "."
        )


def _text(value: object) -> str:
    text = str(value or "")
    return text.strip()


__all__ = [
    "PACKET_GUARD_ATTESTATION_CONTRACT_ID",
    "PACKET_GUARD_ATTESTATION_SCHEMA_VERSION",
    "PacketGuardAttestation",
    "minimal_packet_guard_attestation",
    "packet_guard_attestation_from_mapping",
    "validate_packet_apply_attestation",
]
