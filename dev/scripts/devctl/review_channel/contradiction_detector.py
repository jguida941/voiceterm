"""Plan-proposal contradiction detection for review packets."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ..runtime.master_plan_contract import PlanProposal
from ..runtime.master_plan_parse import normalize_plan_proposal
from ..runtime.plan_ref import canonical_plan_ref, is_plan_ref

_TERMINAL_PACKET_STATES = {"applied", "dismissed", "expired", "archived"}


def find_plan_proposal_conflict(
    *,
    proposal: PlanProposal,
    existing_packets: Iterable[Mapping[str, object]],
) -> Mapping[str, object] | None:
    """Return the first live packet with the same plan mutation key."""
    if not _proposal_is_plan_scoped(proposal):
        return None
    key = _collision_key(proposal)
    if not key[0] or not key[2]:
        return None
    for packet in existing_packets:
        if not isinstance(packet, Mapping):
            continue
        if _packet_terminal(packet):
            continue
        existing_proposal = _proposal_from_packet(packet)
        if not _proposal_is_plan_scoped(existing_proposal):
            continue
        if _collision_key(existing_proposal) == key:
            return packet
    return None


def _proposal_from_packet(packet: Mapping[str, object]) -> PlanProposal:
    plan_proposal = normalize_plan_proposal(packet.get("plan_proposal"))
    if plan_proposal.has_values():
        return plan_proposal
    target_kind = _text(packet.get("target_kind"))
    target_ref = _text(packet.get("target_ref"))
    mutation_op = _text(packet.get("mutation_op")) or _text(
        packet.get("requested_action")
    )
    if target_kind != "plan" or not target_ref:
        return PlanProposal()
    return PlanProposal(
        target_ref=target_ref,
        anchor_refs=tuple(_string_rows(packet.get("anchor_refs"))),
        mutation_op=mutation_op,
        plan_revision_at_propose=_text(packet.get("target_revision")),
    )


def _proposal_is_plan_scoped(proposal: PlanProposal) -> bool:
    return is_plan_ref(proposal.target_ref)


def _collision_key(proposal: PlanProposal) -> tuple[str, tuple[str, ...], str]:
    return (
        canonical_plan_ref(proposal.target_ref),
        tuple(sorted(ref for ref in proposal.anchor_refs if ref)),
        proposal.mutation_op,
    )


def _packet_terminal(packet: Mapping[str, object]) -> bool:
    state = _text(packet.get("lifecycle_current_state")) or _text(packet.get("status"))
    return state in _TERMINAL_PACKET_STATES


def _string_rows(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["find_plan_proposal_conflict"]
