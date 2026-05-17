"""Typed round-proof rows owned by ReviewState."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field

from .value_coercion import (
    coerce_bool,
    coerce_mapping,
    coerce_mapping_items,
    coerce_string_items,
    coerce_text,
)

ROUND_PROOF_CONTRACT_ID = "RoundProof"
ROUND_PROOF_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RoundProofState:
    """Typed proof that one agent round has completed review and guard closure."""

    proof_id: str
    status: str
    proof_state: str
    actor_id: str
    role: str
    session_id: str
    target_kind: str = ""
    target_ref: str = ""
    packet_id: str = ""
    handoff_packet_id: str = ""
    source_event_id: str = ""
    guard_evidence_ref: str = ""
    reviewer_semantic_review: bool = False
    reviewer_semantic_source: str = ""
    evidence_refs: tuple[str, ...] = ()
    missing_proofs: tuple[str, ...] = ()
    source_contract: str = "ReviewState"
    snapshot_id: str = ""
    zref: str = ""
    schema_version: int = ROUND_PROOF_SCHEMA_VERSION
    contract_id: str = ROUND_PROOF_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["missing_proofs"] = list(self.missing_proofs)
        return payload


def round_proofs_from_value(value: object) -> tuple[RoundProofState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    rows: list[RoundProofState] = []
    for row in value:
        mapping = coerce_mapping(row)
        if not mapping:
            continue
        proof = round_proof_from_mapping(mapping)
        if proof is not None:
            rows.append(proof)
    return tuple(rows)


def round_proof_from_mapping(
    value: Mapping[str, object],
) -> RoundProofState | None:
    proof_id = coerce_text(value.get("proof_id"))
    target_ref = coerce_text(value.get("target_ref"))
    packet_id = coerce_text(value.get("packet_id"))
    handoff_packet_id = coerce_text(value.get("handoff_packet_id"))
    actor_id = coerce_text(value.get("actor_id") or value.get("session_actor_id"))
    if not proof_id:
        proof_id = _proof_id(
            actor_id=actor_id,
            session_id=coerce_text(value.get("session_id")),
            target_ref=target_ref or handoff_packet_id or packet_id,
            source_event_id=coerce_text(value.get("source_event_id")),
        )
    if not (proof_id and actor_id):
        return None
    return RoundProofState(
        proof_id=proof_id,
        status=coerce_text(value.get("status")) or "missing",
        proof_state=coerce_text(value.get("proof_state")) or "missing",
        actor_id=actor_id,
        role=coerce_text(value.get("role") or value.get("session_actor_role")),
        session_id=coerce_text(value.get("session_id")),
        target_kind=coerce_text(value.get("target_kind")),
        target_ref=target_ref,
        packet_id=packet_id,
        handoff_packet_id=handoff_packet_id,
        source_event_id=coerce_text(value.get("source_event_id")),
        guard_evidence_ref=coerce_text(value.get("guard_evidence_ref")),
        reviewer_semantic_review=coerce_bool(
            value.get("reviewer_semantic_review")
        ),
        reviewer_semantic_source=coerce_text(
            value.get("reviewer_semantic_source")
        ),
        evidence_refs=coerce_string_items(value.get("evidence_refs")),
        missing_proofs=coerce_string_items(value.get("missing_proofs")),
        source_contract=coerce_text(value.get("source_contract")) or "ReviewState",
        snapshot_id=coerce_text(value.get("snapshot_id")),
        zref=coerce_text(value.get("zref")),
        schema_version=ROUND_PROOF_SCHEMA_VERSION,
        contract_id=(
            coerce_text(value.get("contract_id")) or ROUND_PROOF_CONTRACT_ID
        ),
    )


def build_round_proofs_from_review_state(
    review_state: Mapping[str, object],
) -> tuple[RoundProofState, ...]:
    """Project round proofs from typed ReviewState-owned subcontracts."""
    packets = coerce_mapping_items(review_state.get("packets"))
    packet_by_id = {
        coerce_text(packet.get("packet_id")): packet
        for packet in packets
        if coerce_text(packet.get("packet_id"))
    }
    runtime = coerce_mapping(review_state.get("reviewer_runtime"))
    reviewer = _reviewer_semantic_state(runtime)
    rows: list[RoundProofState] = []
    for outcome in _session_outcomes(review_state):
        if coerce_text(outcome.get("outcome")) != "completed_handoff":
            continue
        row = _round_proof_for_outcome(
            outcome=outcome,
            packet_by_id=packet_by_id,
            reviewer=reviewer,
            snapshot_id=coerce_text(review_state.get("snapshot_id")),
            zref=coerce_text(review_state.get("zref")),
        )
        if row is not None:
            rows.append(row)
    return tuple(rows)


def _session_outcomes(
    review_state: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    collaboration = coerce_mapping(review_state.get("collaboration"))
    return coerce_mapping_items(collaboration.get("session_outcomes"))


def _round_proof_for_outcome(
    *,
    outcome: Mapping[str, object],
    packet_by_id: Mapping[str, Mapping[str, object]],
    reviewer: tuple[bool, str],
    snapshot_id: str,
    zref: str,
) -> RoundProofState | None:
    actor_id = coerce_text(outcome.get("session_actor_id") or outcome.get("provider"))
    if not actor_id:
        return None
    packet_id = coerce_text(outcome.get("handoff_packet_id"))
    target_ref = coerce_text(outcome.get("target_ref")) or packet_id
    packet = packet_by_id.get(packet_id) or packet_by_id.get(target_ref) or {}
    guard_ref = _guard_evidence_ref(packet)
    reviewer_ok, reviewer_source = reviewer
    missing = _missing_proofs(
        handoff=True,
        guard=bool(guard_ref),
        reviewer=reviewer_ok,
    )
    proof_state = "satisfied" if not missing else "missing"
    evidence_refs = tuple(
        item
        for item in (
            coerce_text(outcome.get("source_event_id")),
            packet_id,
            guard_ref,
            reviewer_source,
        )
        if item
    )
    return RoundProofState(
        proof_id=_proof_id(
            actor_id=actor_id,
            session_id=coerce_text(outcome.get("session_id")),
            target_ref=target_ref,
            source_event_id=coerce_text(outcome.get("source_event_id")),
        ),
        status=proof_state,
        proof_state=proof_state,
        actor_id=actor_id,
        role=coerce_text(outcome.get("session_actor_role")),
        session_id=coerce_text(outcome.get("session_id")),
        target_kind=coerce_text(outcome.get("target_kind")) or "packet",
        target_ref=target_ref,
        packet_id=coerce_text(packet.get("packet_id")) or packet_id,
        handoff_packet_id=packet_id,
        source_event_id=coerce_text(outcome.get("source_event_id")),
        guard_evidence_ref=guard_ref,
        reviewer_semantic_review=reviewer_ok,
        reviewer_semantic_source=reviewer_source,
        evidence_refs=evidence_refs,
        missing_proofs=missing,
        snapshot_id=snapshot_id,
        zref=zref,
    )


def _reviewer_semantic_state(
    reviewer_runtime: Mapping[str, object],
) -> tuple[bool, str]:
    acceptance = coerce_mapping(reviewer_runtime.get("review_acceptance"))
    if coerce_bool(acceptance.get("review_accepted")):
        return True, "review_acceptance"
    duty = coerce_mapping(reviewer_runtime.get("duty_proof"))
    source = coerce_text(duty.get("semantic_review_source"))
    if source in {"agent_mind", "agent_mind_auxiliary"}:
        return False, source
    claimed = coerce_bool(duty.get("semantic_review_claimed"))
    if claimed and coerce_text(duty.get("reviewed_diff_hash")):
        return True, source or "reviewer_runtime.duty_proof"
    return False, source


def _guard_evidence_ref(packet: Mapping[str, object]) -> str:
    direct = coerce_text(packet.get("full_guard_bundle_evidence"))
    if direct:
        return direct
    for source in (
        coerce_mapping_items(packet.get("acted_on_events")),
        coerce_mapping_items(
            coerce_mapping(packet.get("lifecycle_history")).get("acted_on_events")
        ),
    ):
        for event in source:
            attestation = coerce_mapping(event.get("guard_attestation"))
            attested_by = coerce_text(attestation.get("attested_by"))
            if attested_by:
                return coerce_text(attestation.get("attestation_id")) or attested_by
    return ""


def _missing_proofs(
    *,
    handoff: bool,
    guard: bool,
    reviewer: bool,
) -> tuple[str, ...]:
    missing: list[str] = []
    if not handoff:
        missing.append("implementer_handoff")
    if not guard:
        missing.append("guard_bundle_or_attestation")
    if not reviewer:
        missing.append("reviewer_semantic_review")
    return tuple(missing)


def _proof_id(
    *,
    actor_id: str,
    session_id: str,
    target_ref: str,
    source_event_id: str,
) -> str:
    parts = [
        "round",
        _token(actor_id),
        _token(session_id) or "unscoped",
        _token(target_ref) or "no-target",
        _token(source_event_id) or "no-event",
    ]
    return ":".join(parts)


def _token(value: str) -> str:
    text = coerce_text(value)
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in text)


__all__ = [
    "ROUND_PROOF_CONTRACT_ID",
    "ROUND_PROOF_SCHEMA_VERSION",
    "RoundProofState",
    "build_round_proofs_from_review_state",
    "round_proof_from_mapping",
    "round_proofs_from_value",
]
