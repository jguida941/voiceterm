"""Instruction-clearing helpers extracted from authority snapshot assembly."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .authority_snapshot_core import _mapping
from .review_state_semantics import is_missing_instruction


@dataclass(frozen=True, slots=True)
class AuthorityInstructionInputs:
    packet_inbox: Mapping[str, object]
    packet_target: object
    reviewer_agent: str
    actor_role: str
    actor_identity: str
    coordination_has_actors: bool
    current_instruction: str
    coordination_current_slice: str


def current_instruction_for_reviewer(
    *,
    current_session: Mapping[str, object],
    clear_from_packet_truth: bool,
) -> str:
    instruction = str(current_session.get("current_instruction") or "").strip()
    if clear_from_packet_truth or is_missing_instruction(instruction):
        return ""
    return instruction


def resolved_coordination_current_slice(
    *,
    coordination: Mapping[str, object],
    current_session: Mapping[str, object],
    clear_from_packet_truth: bool,
) -> str:
    current_slice = str(coordination.get("current_slice") or "").strip()
    raw_current_instruction = str(current_session.get("current_instruction") or "").strip()
    if clear_from_packet_truth and current_slice == raw_current_instruction:
        return ""
    if is_missing_instruction(raw_current_instruction) and current_slice == raw_current_instruction:
        return ""
    return current_slice


def reviewer_instruction_requires_clear(
    *,
    packet_inbox: Mapping[str, object],
    reviewer_agent: str,
) -> bool:
    agents = packet_inbox.get("agents")
    if not isinstance(agents, list):
        return False
    target_agent = str(reviewer_agent or "").strip().lower()
    if not target_agent:
        return False
    record = next(
        (
            _mapping(row)
            for row in agents
            if str(_mapping(row).get("agent") or "").strip().lower() == target_agent
        ),
        {},
    )
    if not record:
        return False
    return not str(record.get("current_instruction_packet_id") or "").strip()


def instruction_requires_clear(inputs: AuthorityInstructionInputs) -> bool:
    reviewer_clear = reviewer_instruction_requires_clear(
        packet_inbox=inputs.packet_inbox,
        reviewer_agent=inputs.reviewer_agent,
    )
    target_packet_id = str(
        getattr(inputs.packet_target, "current_instruction_packet_id", "") or ""
    ).strip()
    if not target_packet_id:
        return reviewer_clear

    target_agent = str(getattr(inputs.packet_target, "agent", "") or "").strip().lower()
    if not target_agent:
        return reviewer_clear

    reviewer_agent = str(inputs.reviewer_agent or "").strip().lower()
    if str(inputs.actor_role or "").strip().lower() != "implementer":
        return target_agent != reviewer_agent

    actor_identity = str(inputs.actor_identity or "").strip().lower()
    if inputs.coordination_has_actors and actor_identity and target_agent == actor_identity:
        return False

    if (
        str(inputs.coordination_current_slice or "").strip()
        == str(inputs.current_instruction or "").strip()
        and target_agent != reviewer_agent
    ):
        return True
    return False
