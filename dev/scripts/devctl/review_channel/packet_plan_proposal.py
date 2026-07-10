"""Plan-proposal classification for review-channel packets."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from ..runtime.master_plan_contract import PlanProposal
from ..runtime.master_plan_parse import (
    normalize_plan_proposal,
    plan_proposal_from_packet_fields,
)
from .contradiction_detector import find_plan_proposal_conflict

PLANNING_PACKET_KINDS = frozenset(
    {
        "plan_gap_review",
        "plan_patch_review",
        "plan_ready_gate",
    }
)
PROPOSAL_PACKET_KINDS = PLANNING_PACKET_KINDS


@dataclass(frozen=True, slots=True)
class PlanProposalPacketFields:
    kind: str
    requested_action: str
    target_kind: str
    target_ref: str
    target_revision: str
    anchor_refs: Sequence[str]
    mutation_op: str
    explicit_proposal: object


def carrier_packet_kinds(valid_packet_kinds: Iterable[str]) -> frozenset[str]:
    return frozenset(valid_packet_kinds) - PLANNING_PACKET_KINDS


def plan_proposal_for_fields(fields: PlanProposalPacketFields) -> PlanProposal:
    proposal = normalize_plan_proposal(fields.explicit_proposal)
    if proposal.has_values():
        return proposal
    if (
        fields.kind not in PROPOSAL_PACKET_KINDS
        or fields.target_kind != "plan"
        or not fields.target_ref
    ):
        return PlanProposal()
    return plan_proposal_from_packet_fields(
        target_ref=fields.target_ref,
        anchor_refs=fields.anchor_refs,
        mutation_op=fields.mutation_op or fields.requested_action,
        plan_revision_at_propose=fields.target_revision,
    )


def validate_plan_proposal_contract(
    *,
    kind: str,
    proposal: PlanProposal,
    carrier_kinds: frozenset[str],
    existing_packets: Iterable[Mapping[str, object]] | None,
) -> None:
    if kind in carrier_kinds:
        if proposal.has_values():
            raise ValueError(
                "Carrier packet kinds must not carry PlanProposal metadata."
            )
        return
    if kind in PROPOSAL_PACKET_KINDS and not proposal.has_values():
        raise ValueError("Planning proposal packets require PlanProposal metadata.")
    if existing_packets is None:
        return
    conflict = find_plan_proposal_conflict(
        proposal=proposal,
        existing_packets=existing_packets,
    )
    if conflict is None:
        return
    raise ValueError(
        "PlanProposalConflict: packet "
        f"{conflict.get('packet_id')} already targets "
        f"{proposal.target_ref} with mutation {proposal.mutation_op}."
    )


__all__ = [
    "PLANNING_PACKET_KINDS",
    "PROPOSAL_PACKET_KINDS",
    "PlanProposalPacketFields",
    "carrier_packet_kinds",
    "plan_proposal_for_fields",
    "validate_plan_proposal_contract",
]
