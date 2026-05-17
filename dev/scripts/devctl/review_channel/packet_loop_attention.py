"""Shared packet-attention policy for agent-loop wake decisions."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_packet_inbox_actionable import (
    is_actionable,
    packet_is_communication_only,
)
from ..runtime.session_termination_policy import SESSION_TERMINATION_PACKET_KINDS
from ..runtime.value_coercion import coerce_text
from .packet_body_observation import packet_body_digest, packet_body_observed_by

_PENDING_LOOP_ATTENTION_LIFECYCLES = frozenset(
    {
        "",
        "pending",
        "delivery_pending",
        "execution_pending",
        "acknowledged",
        "in_progress",
        "apply_pending_after_execution",
        "task_started",
        "task_progress",
        "task_produced",
        "task_blocked",
        "operator_routed",
    }
)
_SUCCESSFUL_DURABLE_INGESTION_STATUSES = frozenset(
    {"already_present", "inserted", "updated"}
)
_COMMAND_LANE_KINDS = frozenset(
    {
        "action_request",
        "approval_request",
        "instruction",
    }
)


def packet_requires_loop_attention(packet: Mapping[str, object]) -> bool:
    """Return whether a live pending packet should wake an agent loop."""
    if coerce_text(packet.get("lifecycle_current_state")) not in (
        _PENDING_LOOP_ATTENTION_LIFECYCLES
    ):
        return False
    if coerce_text(packet.get("kind")) in SESSION_TERMINATION_PACKET_KINDS:
        return False
    if coerce_text(packet.get("to_agent")) != "operator":
        return True
    if coerce_text(packet.get("kind")) != "system_notice":
        return True
    if bool(packet.get("approval_required")):
        return True
    requested_action = coerce_text(packet.get("requested_action"))
    policy_hint = coerce_text(packet.get("policy_hint"))
    return requested_action not in {"", "review_only"} or policy_hint not in {
        "",
        "review_only",
    }


def packet_body_attention_required(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str = "",
    session: str = "",
) -> bool:
    """Return whether a packet still needs route-scoped body observation."""
    actor_id = coerce_text(actor)
    if not actor_id or coerce_text(packet.get("from_agent")) == actor_id:
        return False
    if not packet_body_digest(packet):
        return False
    if packet_body_observed_by(packet, actor=actor_id, role=role, session=session):
        return False
    if packet_durable_ingestion_succeeded(
        packet
    ) and not _route_scoped_peer_review_observation_required(
        packet,
        role=role,
        session=session,
    ):
        return False
    return True


def _route_scoped_peer_review_observation_required(
    packet: Mapping[str, object],
    *,
    role: str,
    session: str,
) -> bool:
    if not (coerce_text(role) or coerce_text(session)):
        return False
    kind = coerce_text(packet.get("kind"))
    requested_action = coerce_text(packet.get("requested_action"))
    policy_hint = coerce_text(packet.get("policy_hint"))
    return kind in {"finding", "decision", "task_progress", "task_produced"} or (
        requested_action == "review_only" and policy_hint == "review_only"
    )


def packet_requires_runtime_attention(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str = "",
    session: str = "",
) -> bool:
    """Return whether one pending packet should keep an agent-loop awake."""
    if packet_durable_ingestion_succeeded(packet) and not _command_lane_packet(packet):
        return packet_body_attention_required(
            packet,
            actor=actor,
            role=role,
            session=session,
        )
    if packet_requires_loop_attention(packet) and not packet_is_communication_only(packet):
        return True
    if is_actionable(packet):
        return True
    return packet_body_attention_required(
        packet,
        actor=actor,
        role=role,
        session=session,
    )


def packet_durable_ingestion_succeeded(packet: Mapping[str, object]) -> bool:
    receipt = packet.get("packet_durable_ingestion_receipt")
    if (
        isinstance(receipt, Mapping)
        and coerce_text(receipt.get("status")) in _SUCCESSFUL_DURABLE_INGESTION_STATUSES
    ):
        return True
    for key in ("durable_binding", "packet_creation_binding"):
        binding = packet.get(key)
        if not isinstance(binding, Mapping):
            continue
        if coerce_text(binding.get("binding_target_kind")) == "communication_only":
            continue
        if coerce_text(binding.get("status")) in _SUCCESSFUL_DURABLE_INGESTION_STATUSES:
            return True
    return False


def _command_lane_packet(packet: Mapping[str, object]) -> bool:
    return coerce_text(packet.get("kind")) in _COMMAND_LANE_KINDS
