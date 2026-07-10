"""Instruction-authority transition receipt emission for review projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..runtime.instruction_authority import (
    DEFAULT_INSTRUCTION_TRANSITIONS_REL,
    InstructionTransitionReceipt,
    append_instruction_transition_receipt,
    deterministic_receipt_id,
)
from ..runtime.master_plan_contract import IngestionProvenance
from ..runtime.master_plan_parse import ingestion_provenance_from_mapping
from ..time_utils import utc_timestamp


def maybe_record_instruction_transition(
    *,
    repo_root: Path,
    prior_review_state: Mapping[str, object] | None,
    review_state: Mapping[str, object],
) -> InstructionTransitionReceipt | None:
    """Append a receipt when the active instruction source changes."""
    prior = _active_instruction(prior_review_state)
    current = _active_instruction(review_state)
    if not current.instruction_id:
        return None
    if prior.instruction_id == current.instruction_id:
        return None

    close_reason = _close_reason(prior, current, review_state)
    receipt = InstructionTransitionReceipt(
        receipt_id=deterministic_receipt_id(
            closed_instruction_id=prior.instruction_id,
            close_reason=close_reason,
            new_instruction_id=current.instruction_id,
            decided_via_rule=current.rule_id,
            new_instruction_hash=current.source_hash,
        ),
        closed_instruction_id=prior.instruction_id,
        close_reason=close_reason,
        new_instruction_id=current.instruction_id,
        new_instruction_provenance=current.provenance,
        decided_via_rule=current.rule_id,
        transitioned_at_utc=utc_timestamp(),
        typed_evidence=current.typed_evidence,
    )
    appended = append_instruction_transition_receipt(
        repo_root / DEFAULT_INSTRUCTION_TRANSITIONS_REL,
        receipt,
    )
    return receipt if appended else None


@dataclass(frozen=True)
class _InstructionAuthority:
    instruction_id: str
    source_kind: str
    rule_id: str
    provenance: IngestionProvenance | None
    source_hash: str
    status: str
    typed_evidence: dict[str, object] | None = None


def _active_instruction(
    review_state: Mapping[str, object] | None,
) -> _InstructionAuthority:
    if not isinstance(review_state, Mapping):
        return _empty_authority()

    queue = _mapping(review_state.get("queue"))
    source = _mapping(queue.get("derived_next_instruction_source"))
    packet_id = str(source.get("packet_id") or "").strip()
    if packet_id:
        provenance = _provenance_from_source(source)
        return _InstructionAuthority(
            instruction_id=packet_id,
            source_kind="packet",
            rule_id=_priority_rule(queue, source),
            provenance=provenance,
            source_hash=provenance.source_hash if provenance else "",
            status=_packet_status(review_state, packet_id),
            typed_evidence=_packet_typed_evidence(review_state, packet_id),
        )

    coordination = _mapping(review_state.get("coordination")) or _mapping(
        _mapping(review_state.get("collaboration")).get("coordination")
    )
    active_target = _mapping(coordination.get("active_target"))
    target_id = str(active_target.get("target_id") or "").strip()
    current_slice = str(coordination.get("current_slice") or "").strip()
    if target_id or current_slice:
        provenance = _provenance_from_active_target(active_target)
        return _InstructionAuthority(
            instruction_id=target_id or current_slice,
            source_kind="ingested_doc",
            rule_id="doc_authority_fallback",
            provenance=provenance,
            source_hash=provenance.source_hash,
            status="active",
        )

    return _empty_authority()


def _empty_authority() -> _InstructionAuthority:
    return _InstructionAuthority(
        instruction_id="",
        source_kind="none",
        rule_id="no_live_instruction_authority",
        provenance=None,
        source_hash="",
        status="",
    )


def _provenance_from_source(
    source: Mapping[str, object],
) -> IngestionProvenance | None:
    provenance = source.get("provenance")
    if not isinstance(provenance, Mapping):
        return None
    return ingestion_provenance_from_mapping(provenance)


def _provenance_from_active_target(
    active_target: Mapping[str, object],
) -> IngestionProvenance:
    plan_path = str(active_target.get("plan_path") or "").strip()
    expected_revision = str(active_target.get("expected_revision") or "").strip()
    return IngestionProvenance(
        source_file=plan_path,
        source_line=0,
        source_kind="CoordinationSnapshot",
        source_hash=expected_revision,
        observed_at_utc=utc_timestamp(),
        section_authority="owner_doc",
    )


def _priority_rule(
    queue: Mapping[str, object],
    source: Mapping[str, object],
) -> str:
    decision = _mapping(queue.get("instruction_priority_decision")) or _mapping(
        source.get("priority_decision")
    )
    return str(decision.get("rule_id") or source.get("selection_policy") or "").strip()


def _packet_status(review_state: Mapping[str, object], packet_id: str) -> str:
    packet = _packet_by_id(review_state, packet_id)
    return str(packet.get("status") or "").strip()


def _packet_typed_evidence(
    review_state: Mapping[str, object],
    packet_id: str,
) -> dict[str, object] | None:
    packet = _packet_by_id(review_state, packet_id)
    evidence = _mapping(packet.get("guard_attestation"))
    return dict(evidence) if evidence else None


def _packet_by_id(
    review_state: Mapping[str, object],
    packet_id: str,
) -> Mapping[str, object]:
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return {}
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        if str(packet.get("packet_id") or "").strip() == packet_id:
            return packet
    return {}


def _close_reason(
    prior: _InstructionAuthority,
    current: _InstructionAuthority,
    review_state: Mapping[str, object],
) -> str:
    if not prior.instruction_id:
        return "initial_authority"
    if prior.source_kind == "packet":
        status = _packet_status(review_state, prior.instruction_id) or prior.status
        if status in {"applied", "dismissed", "expired"}:
            return f"packet_{status}"
        if current.source_kind == "packet":
            return "supersedence"
        return "doc_authority_fallback"
    if current.source_kind == "packet":
        return "packet_priority"
    return "doc_authority_fallback"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


__all__ = ["maybe_record_instruction_transition"]
