"""Body lifecycle follow-up helpers for /develop packet attention."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ...runtime.packet_absorption import (
    ACTIONABLE_PACKET_KINDS,
    packet_absorbed,
    packet_semantically_ingested_by,
)
from ...review_channel.agent_packet_attention import packet_attention_for_agent
from ...review_channel.agent_packet_attention_body import (
    packet_absorption_command,
    packet_semantic_ingestion_command,
)
from ...review_channel.packet_body_observation import (
    packet_body_digest,
    packet_body_observed_by,
)
from ...review_channel.packet_semantic_action_items import (
    semantic_action_item_rows_for_packet,
)
from .packet_attention_commands import PacketShowCommandRoute, show_packet_command
from .packet_attention_lifecycle import packet_by_id, packet_exits_next_pool
from .packet_attention_support import _int, _work_board_rows
from .packet_attention_types import PacketExitContext


@dataclass(frozen=True, slots=True)
class PacketBodyFollowup:
    """Selected packet body lifecycle result for /develop."""

    route: PacketShowCommandRoute
    required: bool = False
    reason: str = ""
    packet_id: str = ""
    command: str = ""


def packet_body_followup_for_selection(
    review_state: Mapping[str, object],
    *,
    agent: str,
    packet_id: str,
    exit_context: PacketExitContext | None = None,
) -> PacketBodyFollowup:
    """Return the strongest body lifecycle follow-up for the selected packet."""

    route = active_actor_route(review_state, agent=agent)
    body_attention = packet_attention_for_agent(
        review_state,
        actor=agent,
        role=route.actor_role,
        session=route.session_id,
    )
    required, reason, body_packet_id, command = _body_attention_followup(
        body_attention
    )
    if required and _packet_exits_next_pool(
        exit_context,
        packet_id=body_packet_id,
    ):
        required, reason, body_packet_id, command = False, "", "", ""
    if required:
        return PacketBodyFollowup(route, True, reason, body_packet_id, command)
    if _packet_exits_next_pool(exit_context, packet_id=packet_id):
        return PacketBodyFollowup(route)
    required, reason, body_packet_id, command = _selected_packet_body_followup(
        packet_by_id(review_state, packet_id),
        actor=agent,
        route=route,
    )
    return PacketBodyFollowup(route, required, reason, body_packet_id, command)


def active_actor_route(
    review_state: Mapping[str, object],
    *,
    agent: str,
) -> PacketShowCommandRoute:
    """Return the active actor role/session route for command rendering."""

    return PacketShowCommandRoute(
        actor_role=_active_actor_route_field(review_state, agent=agent, field="role"),
        session_id=_active_actor_route_field(
            review_state,
            agent=agent,
            field="session_id",
        ),
    )


def _body_attention_followup(body_attention: object) -> tuple[bool, str, str, str]:
    if bool(getattr(body_attention, "body_open_required", False)):
        return (
            True,
            "packet_body_open_required",
            str(getattr(body_attention, "body_open_packet_id", "") or "").strip(),
            str(getattr(body_attention, "body_open_command", "") or "").strip(),
        )
    if bool(getattr(body_attention, "semantic_ingestion_required", False)):
        return (
            True,
            "packet_semantic_ingestion_required",
            str(
                getattr(body_attention, "semantic_ingestion_packet_id", "") or ""
            ).strip(),
            str(getattr(body_attention, "semantic_ingestion_command", "") or "").strip(),
        )
    if bool(getattr(body_attention, "absorption_required", False)):
        return (
            True,
            "packet_absorption_required",
            str(getattr(body_attention, "absorption_packet_id", "") or "").strip(),
            str(getattr(body_attention, "absorption_command", "") or "").strip(),
        )
    return False, "", "", ""


def _packet_exits_next_pool(
    exit_context: PacketExitContext | None,
    *,
    packet_id: str,
) -> bool:
    if exit_context is None:
        return False
    return packet_exits_next_pool(exit_context, packet_id=packet_id)


def _selected_packet_body_followup(
    packet: Mapping[str, object],
    *,
    actor: str,
    route: PacketShowCommandRoute,
) -> tuple[bool, str, str, str]:
    packet_id = _packet_text(packet, "packet_id")
    actor_id = str(actor or "").strip()
    if not packet_id or not actor_id:
        return False, "", "", ""
    if _packet_text(packet, "from_agent") == actor_id:
        return False, "", "", ""
    if not packet_body_digest(packet):
        return False, "", "", ""

    role = route.actor_role
    session = route.session_id
    if not packet_body_observed_by(
        packet,
        actor=actor_id,
        role=role,
        session=session,
    ):
        return (
            True,
            "packet_body_open_required",
            packet_id,
            show_packet_command(
                packet_id,
                route=PacketShowCommandRoute(
                    actor=actor_id,
                    actor_role=role,
                    session_id=session,
                    target_role=_packet_text(packet, "target_role"),
                    target_session_id=_packet_text(packet, "target_session_id"),
                ),
            ),
        )

    if _develop_semantic_lifecycle_packet(packet) and not packet_semantically_ingested_by(
        packet,
        actor=actor_id,
        role=role,
        session=session,
    ):
        return (
            True,
            "packet_semantic_ingestion_required",
            packet_id,
            packet_semantic_ingestion_command(
                packet_id=packet_id,
                actor=actor_id,
                role=role,
                session=session,
                action_item_rows=semantic_action_item_rows_for_packet(packet),
            ),
        )

    if _develop_semantic_lifecycle_packet(packet) and not packet_absorbed(packet):
        return (
            True,
            "packet_absorption_required",
            packet_id,
            packet_absorption_command(
                packet_id=packet_id,
                actor=actor_id,
                role=role,
                session=session,
            ),
        )

    return False, "", "", ""


def _develop_semantic_lifecycle_packet(packet: Mapping[str, object]) -> bool:
    return _packet_text(packet, "kind").lower() in ACTIONABLE_PACKET_KINDS


def _active_actor_route_field(
    review_state: Mapping[str, object],
    *,
    agent: str,
    field: str,
) -> str:
    candidates = [
        row
        for row in _work_board_rows(review_state)
        if str(row.get("actor_id") or "").strip().lower()
        == str(agent or "").strip().lower()
    ]
    if not candidates:
        return ""
    candidates.sort(key=lambda row: _int(row.get("idle_seconds")))
    row = candidates[0]
    if field == "role":
        return str(row.get("role") or "").strip()
    if field == "session_id":
        return str(row.get("session_id") or "").strip()
    return ""


def _packet_text(packet: Mapping[str, object], field: str) -> str:
    return str(packet.get(field) or "").strip()
